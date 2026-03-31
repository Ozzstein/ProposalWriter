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


if __name__ == "__main__":
    mcp.run()
