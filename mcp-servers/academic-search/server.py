#!/usr/bin/env python3
"""Academic Search MCP Server — PubMed search tools.

Provides search tools for PubMed via NCBI's E-utilities API.
Semantic Scholar is already available via a connected MCP tool,
so this server focuses on PubMed-specific functionality.

Run with: python server.py
Requires: pip install fastmcp httpx
"""

import httpx
from fastmcp import FastMCP

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ARXIV_BASE = "https://export.arxiv.org/api/query"
# arXiv asks that API clients identify themselves via User-Agent
ARXIV_HEADERS = {"User-Agent": "ProposalWriter/1.0 (grant proposal writing tool; contact via GitHub)"}

mcp = FastMCP("academic-search")


@mcp.tool()
async def search_pubmed(
    query: str,
    max_results: int = 20,
    date_from: str = "",
    date_to: str = "",
) -> str:
    """Search PubMed for academic papers.

    Args:
        query: Search query (supports PubMed search syntax).
        max_results: Maximum number of results to return (default 20, max 100).
        date_from: Optional start date filter (YYYY/MM/DD format).
        date_to: Optional end date filter (YYYY/MM/DD format).

    Returns:
        JSON string with search results including PMIDs, titles, and abstracts.
    """
    max_results = min(max_results, 100)

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
    }
    if date_from:
        params["mindate"] = date_from
    if date_to:
        params["maxdate"] = date_to
    if date_from or date_to:
        params["datetype"] = "pdat"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Search for PMIDs
        resp = await client.get(f"{PUBMED_BASE}/esearch.fcgi", params=params)
        resp.raise_for_status()
        search_data = resp.json()

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        total_count = search_data.get("esearchresult", {}).get("count", "0")

        if not id_list:
            return f'{{"total_count": {total_count}, "results": [], "message": "No results found for: {query}"}}'

        # Step 2: Fetch summaries for found PMIDs
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
        }
        summary_resp = await client.get(
            f"{PUBMED_BASE}/esummary.fcgi", params=summary_params
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        results = []
        for pmid in id_list:
            article = summary_data.get("result", {}).get(pmid, {})
            if not article or pmid == "uids":
                continue

            authors = ", ".join(
                a.get("name", "") for a in article.get("authors", [])[:5]
            )
            if len(article.get("authors", [])) > 5:
                authors += " et al."

            results.append({
                "pmid": pmid,
                "title": article.get("title", ""),
                "authors": authors,
                "journal": article.get("fulljournalname", article.get("source", "")),
                "year": article.get("pubdate", "")[:4],
                "doi": next(
                    (
                        aid.get("value", "")
                        for aid in article.get("articleids", [])
                        if aid.get("idtype") == "doi"
                    ),
                    "",
                ),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

        import json
        return json.dumps({
            "total_count": int(total_count),
            "returned": len(results),
            "results": results,
        }, indent=2)


@mcp.tool()
async def fetch_abstract(pmid: str) -> str:
    """Fetch the full abstract for a PubMed article.

    Args:
        pmid: PubMed ID (e.g., "39123456").

    Returns:
        JSON string with title, abstract, MeSH terms, and metadata.
    """
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{PUBMED_BASE}/efetch.fcgi", params=params)
        resp.raise_for_status()
        xml_text = resp.text

    # Simple XML parsing for abstract text
    import re

    title_match = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", xml_text, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    # Extract abstract sections
    abstract_parts = re.findall(
        r"<AbstractText(?:\s+Label=\"([^\"]*)\")?\s*>(.*?)</AbstractText>",
        xml_text,
        re.DOTALL,
    )
    if abstract_parts:
        abstract_text = "\n\n".join(
            f"**{label}**: {text.strip()}" if label else text.strip()
            for label, text in abstract_parts
        )
    else:
        abstract_text = "No abstract available."

    # Extract MeSH terms
    mesh_terms = re.findall(
        r"<DescriptorName[^>]*>(.*?)</DescriptorName>", xml_text
    )

    # Extract publication type
    pub_types = re.findall(
        r"<PublicationType[^>]*>(.*?)</PublicationType>", xml_text
    )

    import json
    return json.dumps({
        "pmid": pmid,
        "title": title,
        "abstract": abstract_text,
        "mesh_terms": mesh_terms[:20],
        "publication_types": pub_types,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }, indent=2)


@mcp.tool()
async def fetch_mesh_terms(pmid: str) -> str:
    """Fetch MeSH (Medical Subject Headings) terms for a PubMed article.

    Useful for understanding how a paper is categorized and finding
    related papers via MeSH-based searches.

    Args:
        pmid: PubMed ID.

    Returns:
        JSON string with MeSH terms and qualifiers.
    """
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{PUBMED_BASE}/efetch.fcgi", params=params)
        resp.raise_for_status()
        xml_text = resp.text

    import re

    # Extract MeSH headings with qualifiers
    mesh_entries = []
    mesh_blocks = re.findall(
        r"<MeshHeading>(.*?)</MeshHeading>", xml_text, re.DOTALL
    )
    for block in mesh_blocks:
        descriptor = re.search(
            r"<DescriptorName[^>]*>(.*?)</DescriptorName>", block
        )
        qualifiers = re.findall(
            r"<QualifierName[^>]*>(.*?)</QualifierName>", block
        )
        if descriptor:
            mesh_entries.append({
                "descriptor": descriptor.group(1),
                "qualifiers": qualifiers,
            })

    import json
    return json.dumps({
        "pmid": pmid,
        "mesh_terms": mesh_entries,
        "total": len(mesh_entries),
    }, indent=2)


@mcp.tool()
async def search_arxiv(
    query: str,
    max_results: int = 20,
    category: str = "",
    date_from: str = "",
    date_to: str = "",
) -> str:
    """Search arXiv for preprints and papers.

    Args:
        query: Search query (supports arXiv search syntax, e.g., 'ti:CRISPR AND abs:therapy').
        max_results: Maximum number of results to return (default 20, max 100).
        category: Optional arXiv category filter (e.g., 'cs.AI', 'q-bio.GN', 'physics.med-ph').
        date_from: Optional start date filter (YYYYMMDD format, e.g., '20220101').
        date_to: Optional end date filter (YYYYMMDD format, e.g., '20241231').

    Returns:
        JSON string with results including arXiv IDs, titles, abstracts, authors, and categories.
    """
    import xml.etree.ElementTree as ET

    max_results = min(max_results, 100)

    # Build search query
    search_query = query
    if category:
        search_query = f"cat:{category} AND ({query})"

    params = {
        "search_query": search_query,
        "start": "0",
        "max_results": str(max_results),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    if date_from or date_to:
        # arXiv date filtering via submittedDate field
        from_str = date_from or "19910101"
        to_str = date_to or "30000101"
        params["search_query"] = f"submittedDate:[{from_str} TO {to_str}] AND ({search_query})"

    async with httpx.AsyncClient(timeout=60.0, headers=ARXIV_HEADERS) as client:
        resp = await client.get(ARXIV_BASE, params=params)
        resp.raise_for_status()
        xml_text = resp.text

    # Parse Atom feed
    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)

    total_results_el = root.find("opensearch:totalResults", {
        "opensearch": "http://a9.com/-/spec/opensearch/1.1/"
    })
    total_count = int(total_results_el.text) if total_results_el is not None else 0

    results = []
    for entry in root.findall("atom:entry", NS):
        arxiv_id_raw = (entry.findtext("atom:id", "", NS) or "").strip()
        # Extract just the ID (e.g., "2301.00001v1" -> "2301.00001")
        arxiv_id = arxiv_id_raw.split("/abs/")[-1].split("v")[0] if "/abs/" in arxiv_id_raw else arxiv_id_raw

        title = (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " ")
        summary = (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " ")

        authors = [
            (a.findtext("atom:name", "", NS) or "").strip()
            for a in entry.findall("atom:author", NS)
        ]
        authors_str = ", ".join(authors[:5])
        if len(authors) > 5:
            authors_str += " et al."

        published = (entry.findtext("atom:published", "", NS) or "")[:10]
        year = published[:4] if published else ""

        categories = [
            t.get("term", "")
            for t in entry.findall("atom:category", NS)
        ]

        doi_el = entry.find("arxiv:doi", NS)
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""

        results.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors_str,
            "year": year,
            "published": published,
            "categories": categories,
            "abstract": summary[:500] + ("..." if len(summary) > 500 else ""),
            "doi": doi,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        })

    import json
    return json.dumps({
        "total_count": total_count,
        "returned": len(results),
        "results": results,
    }, indent=2)


@mcp.tool()
async def fetch_arxiv_paper(arxiv_id: str) -> str:
    """Fetch full metadata and abstract for an arXiv paper.

    Args:
        arxiv_id: arXiv paper ID (e.g., '2301.00001' or '2301.00001v2').

    Returns:
        JSON string with full title, abstract, authors, categories, and links.
    """
    import xml.etree.ElementTree as ET

    # Strip version suffix for the query
    clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

    params = {
        "id_list": clean_id,
        "max_results": "1",
    }

    async with httpx.AsyncClient(timeout=60.0, headers=ARXIV_HEADERS) as client:
        resp = await client.get(ARXIV_BASE, params=params)
        resp.raise_for_status()
        xml_text = resp.text

    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)
    entry = root.find("atom:entry", NS)

    if entry is None:
        import json
        return json.dumps({"error": f"No paper found for arXiv ID: {arxiv_id}"})

    title = (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " ")
    summary = (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " ")
    published = (entry.findtext("atom:published", "", NS) or "")[:10]
    updated = (entry.findtext("atom:updated", "", NS) or "")[:10]

    authors = [
        (a.findtext("atom:name", "", NS) or "").strip()
        for a in entry.findall("atom:author", NS)
    ]

    categories = [
        t.get("term", "")
        for t in entry.findall("atom:category", NS)
    ]

    primary_cat_el = entry.find("arxiv:primary_category", NS)
    primary_category = primary_cat_el.get("term", "") if primary_cat_el is not None else (categories[0] if categories else "")

    doi_el = entry.find("arxiv:doi", NS)
    doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""

    comment_el = entry.find("arxiv:comment", NS)
    comment = comment_el.text.strip() if comment_el is not None and comment_el.text else ""

    import json
    return json.dumps({
        "arxiv_id": clean_id,
        "title": title,
        "authors": authors,
        "abstract": summary,
        "published": published,
        "updated": updated,
        "primary_category": primary_category,
        "all_categories": categories,
        "doi": doi,
        "comment": comment,
        "url": f"https://arxiv.org/abs/{clean_id}",
        "pdf_url": f"https://arxiv.org/pdf/{clean_id}",
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
