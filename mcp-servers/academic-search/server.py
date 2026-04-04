#!/usr/bin/env python3
"""Academic Search MCP Server — PubMed, arXiv, Unpaywall, Elsevier, CrossRef, Europe PMC.

Provides search and retrieval tools for:
  - PubMed (NCBI E-utilities)
  - arXiv (Atom feed API)
  - Unpaywall (open-access PDF resolver)
  - Scopus (Elsevier bibliometric database — search + abstract snippet)
  - ScienceDirect (Elsevier full-text — OA or institutional access only)
  - CrossRef (DOI registry, citation counts, funder metadata — no key)
  - Europe PMC (EU-funded and biomedical OA literature — no key)

Run with: python server.py
Requires: pip install fastmcp httpx
Environment variables:
  ELSEVIER_API_KEY — from https://dev.elsevier.com/apikey/manage
"""

import os
import httpx
from fastmcp import FastMCP

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ARXIV_BASE = "https://export.arxiv.org/api/query"
UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
SCOPUS_BASE = "https://api.elsevier.com/content/search/scopus"
SCOPUS_ABSTRACT_BASE = "https://api.elsevier.com/content/abstract"
SCIENCEDIRECT_BASE = "https://api.elsevier.com/content/article"
CROSSREF_BASE = "https://api.crossref.org/works"
EUROPEPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Unpaywall requires a contact email for rate-limit identification (not authentication)
UNPAYWALL_EMAIL = "proposalwriter@tool.local"
# arXiv asks that API clients identify themselves via User-Agent
ARXIV_HEADERS = {"User-Agent": "ProposalWriter/1.0 (grant proposal writing tool; contact via GitHub)"}

_ELSEVIER_API_KEY = os.environ.get("ELSEVIER_API_KEY", "")

def _elsevier_headers(accept: str = "application/json") -> dict:
    """Build Elsevier API request headers."""
    return {
        "X-ELS-APIKey": _ELSEVIER_API_KEY,
        "Accept": accept,
        "User-Agent": "ProposalWriter/1.0 (grant proposal writing tool; contact via GitHub)",
    }

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


@mcp.tool()
async def unpaywall_fetch(doi: str) -> str:
    """Check whether a paywalled paper has a free legal open-access version via Unpaywall.

    Unpaywall indexes 50M+ papers and finds author manuscripts, PubMed Central
    copies, institutional repositories, and publisher open-access versions.
    This is the primary tool for accessing papers found in PubMed/arXiv results
    that are behind a paywall.

    Args:
        doi: Digital Object Identifier (e.g., "10.1038/s41586-021-03819-2").
             Strip any "https://doi.org/" prefix before passing.

    Returns:
        JSON string with open-access status, best PDF URL (if available),
        all known OA locations, and full paper metadata.
    """
    import json

    # Normalise DOI — strip URL prefix if present
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    elif doi.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]

    url = f"{UNPAYWALL_BASE}/{doi}"
    params = {"email": UNPAYWALL_EMAIL}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)

        if resp.status_code == 404:
            return json.dumps({
                "doi": doi,
                "is_oa": False,
                "best_oa_url": None,
                "message": "DOI not found in Unpaywall database.",
            })

        resp.raise_for_status()
        data = resp.json()

    best_oa = data.get("best_oa_location") or {}
    all_locations = data.get("oa_locations", [])

    # Build a clean list of all available free URLs
    free_urls = []
    for loc in all_locations:
        entry = {
            "url": loc.get("url_for_pdf") or loc.get("url") or "",
            "host_type": loc.get("host_type", ""),  # "publisher", "repository"
            "version": loc.get("version", ""),       # "publishedVersion", "acceptedVersion"
            "license": loc.get("license") or "",
            "repository_institution": loc.get("repository_institution") or "",
        }
        if entry["url"]:
            free_urls.append(entry)

    return json.dumps({
        "doi": doi,
        "title": data.get("title", ""),
        "authors": ", ".join(
            f"{a.get('family', '')}, {a.get('given', '')}"
            for a in (data.get("z_authors") or [])[:5]
        ),
        "year": data.get("year"),
        "journal": data.get("journal_name", ""),
        "publisher": data.get("publisher", ""),
        "is_oa": data.get("is_oa", False),
        "oa_status": data.get("oa_status", "closed"),  # gold/green/hybrid/bronze/closed
        "best_oa_url": best_oa.get("url_for_pdf") or best_oa.get("url"),
        "best_oa_host_type": best_oa.get("host_type", ""),
        "best_oa_version": best_oa.get("version", ""),
        "all_free_urls": free_urls,
        "total_free_locations": len(free_urls),
        "data_standard": data.get("data_standard"),
        "updated": data.get("updated"),
    }, indent=2)


@mcp.tool()
async def unpaywall_batch(dois: list[str]) -> str:
    """Check open-access availability for a batch of DOIs via Unpaywall.

    More efficient than calling unpaywall_fetch repeatedly when you have
    multiple DOIs from a literature search to check at once.

    Args:
        dois: List of DOIs to check (max 50). Strip "https://doi.org/" prefixes.

    Returns:
        JSON string with a summary table: DOI, is_oa, oa_status, best_oa_url
        for each paper. Papers without a free version are listed with is_oa=false.
    """
    import json
    import asyncio

    dois = [
        d.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        for d in dois[:50]
        if d.strip()
    ]

    async def check_one(client: httpx.AsyncClient, doi: str) -> dict:
        try:
            resp = await client.get(
                f"{UNPAYWALL_BASE}/{doi}",
                params={"email": UNPAYWALL_EMAIL},
                timeout=20.0,
            )
            if resp.status_code == 404:
                return {"doi": doi, "is_oa": False, "oa_status": "not_found", "best_oa_url": None}
            resp.raise_for_status()
            data = resp.json()
            best = data.get("best_oa_location") or {}
            return {
                "doi": doi,
                "title": data.get("title", ""),
                "year": data.get("year"),
                "is_oa": data.get("is_oa", False),
                "oa_status": data.get("oa_status", "closed"),
                "best_oa_url": best.get("url_for_pdf") or best.get("url"),
                "host_type": best.get("host_type", ""),
            }
        except Exception as e:
            return {"doi": doi, "is_oa": False, "oa_status": "error", "error": str(e), "best_oa_url": None}

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[check_one(client, doi) for doi in dois])

    oa_count = sum(1 for r in results if r.get("is_oa"))
    return json.dumps({
        "total_checked": len(results),
        "open_access_count": oa_count,
        "closed_count": len(results) - oa_count,
        "results": list(results),
    }, indent=2)


@mcp.tool()
async def scopus_search(
    query: str,
    max_results: int = 25,
    year_from: int = 0,
    year_to: int = 0,
    subject_area: str = "",
    doc_type: str = "",
) -> str:
    """Search the Scopus database (Elsevier) for peer-reviewed papers.

    Scopus covers 90M+ records across all disciplines with citation counts
    and journal metrics. Particularly strong for engineering, chemistry,
    materials science, and energy topics.

    Scopus query syntax examples:
      - TITLE-ABS-KEY(digital twin AND battery)   — search title, abstract, keywords
      - TITLE(lithium iron phosphate)               — title only
      - AUTH(Smith) AND AFFIL(MIT)                  — author + affiliation
      - SRCTITLE(Journal of Power Sources)          — specific journal
      Combine with AND, OR, AND NOT. Use parentheses for grouping.

    Args:
        query: Scopus query string (TITLE-ABS-KEY syntax recommended).
        max_results: Number of results (default 25, max 100).
        year_from: Optional start year filter (e.g. 2019).
        year_to: Optional end year filter (e.g. 2024).
        subject_area: Optional Scopus subject area code, e.g.:
                      ENGI (Engineering), CHEM (Chemistry), MATS (Materials Science),
                      ENER (Energy), COMP (Computer Science), MEDI (Medicine),
                      PHYS (Physics), ENVI (Environmental Science).
        doc_type: Optional document type: ar (article), re (review),
                  cp (conference paper), bk (book chapter).

    Returns:
        JSON with total results count, per-paper metadata including DOI,
        citation count, open-access flag, and abstract snippet.
    """
    import json

    if not _ELSEVIER_API_KEY:
        return json.dumps({"error": "ELSEVIER_API_KEY not set in environment."})

    # Build date filter
    date_range = ""
    if year_from and year_to:
        date_range = f"{year_from}-{year_to}"
    elif year_from:
        date_range = f"{year_from}-2030"
    elif year_to:
        date_range = f"1900-{year_to}"

    params: dict = {
        "query": query,
        "count": str(min(max_results, 100)),
        "start": "0",
        "sort": "relevancy",
        "field": "dc:identifier,dc:title,dc:creator,prism:publicationName,"
                 "prism:doi,prism:coverDate,citedby-count,openaccess,"
                 "prism:aggregationType,subtypeDescription,dc:description",
    }
    if date_range:
        params["date"] = date_range
    if subject_area:
        params["subj"] = subject_area
    if doc_type:
        params["doctype"] = doc_type

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(SCOPUS_BASE, headers=_elsevier_headers(), params=params)

        if resp.status_code == 401:
            return json.dumps({"error": "Elsevier API key invalid or expired."})
        if resp.status_code == 429:
            return json.dumps({"error": "Elsevier API rate limit exceeded. Wait and retry."})
        resp.raise_for_status()
        data = resp.json()

    search_results = data.get("search-results", {})
    total = search_results.get("opensearch:totalResults", "0")
    entries = search_results.get("entry", [])

    results = []
    for e in entries:
        doi = e.get("prism:doi", "")
        cover_date = e.get("prism:coverDate", "")
        year = cover_date[:4] if cover_date else ""
        # Abstract snippet may be in dc:description (not always present in search)
        abstract_snippet = (e.get("dc:description") or "")[:400]
        if len(e.get("dc:description") or "") > 400:
            abstract_snippet += "..."

        results.append({
            "scopus_id": e.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
            "title": e.get("dc:title", ""),
            "first_author": e.get("dc:creator", ""),
            "journal": e.get("prism:publicationName", ""),
            "year": year,
            "doi": doi,
            "doc_type": e.get("subtypeDescription", ""),
            "cited_by": int(e.get("citedby-count") or 0),
            "open_access": e.get("openaccess") in ("1", 1, True),
            "abstract_snippet": abstract_snippet,
            "url": f"https://doi.org/{doi}" if doi else "",
            "scopus_url": f"https://www.scopus.com/record/display.uri?eid={e.get('dc:identifier', '')}",
        })

    return json.dumps({
        "total_results": int(total),
        "returned": len(results),
        "query": query,
        "results": results,
    }, indent=2)


@mcp.tool()
async def scopus_abstract(doi: str) -> str:
    """Retrieve full abstract and metadata for a paper via the Scopus Abstract API.

    Use this after scopus_search to get the complete abstract, keywords,
    reference count, and subject classifications for a specific paper.
    Works for any paper in Scopus regardless of open-access status —
    abstracts are always available.

    Args:
        doi: Paper DOI (e.g., "10.1016/j.jpowsour.2023.233456").
             Strips "https://doi.org/" prefix automatically.

    Returns:
        JSON with full abstract, author list, keywords, subject areas,
        reference count, citation count, and funding information.
    """
    import json

    if not _ELSEVIER_API_KEY:
        return json.dumps({"error": "ELSEVIER_API_KEY not set in environment."})

    doi = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{SCOPUS_ABSTRACT_BASE}/doi/{doi}",
            headers=_elsevier_headers(),
            params={"view": "FULL"},
        )

        if resp.status_code == 404:
            return json.dumps({"doi": doi, "error": "Paper not found in Scopus."})
        if resp.status_code in (401, 403):
            return json.dumps({
                "doi": doi,
                "error": (
                    "Scopus Abstract Retrieval API requires an institutional network token "
                    "(X-ELS-Insttoken) in addition to the API key. This is only available via "
                    "university/company institutional subscriptions. "
                    "Use scopus_search instead — it returns abstract snippets for any paper."
                ),
            })
        resp.raise_for_status()
        data = resp.json()

    core = (
        data.get("abstracts-retrieval-response", {})
        .get("coredata", {})
    )
    item = data.get("abstracts-retrieval-response", {})

    # Authors
    author_list = []
    for a in (item.get("authors") or {}).get("author", []):
        name = a.get("ce:indexed-name") or a.get("preferred-name", {}).get("ce:indexed-name", "")
        affil = ""
        affil_data = a.get("affiliation")
        if isinstance(affil_data, dict):
            affil = affil_data.get("affilname", "")
        elif isinstance(affil_data, list) and affil_data:
            affil = affil_data[0].get("affilname", "")
        author_list.append({"name": name, "affiliation": affil})

    # Keywords
    kw_group = (item.get("authkeywords") or {}).get("author-keyword", [])
    if isinstance(kw_group, dict):
        kw_group = [kw_group]
    keywords = [k.get("$", "") for k in kw_group if k.get("$")]

    # Subject areas
    subj_areas = []
    for s in ((item.get("subject-areas") or {}).get("subject-area") or []):
        if isinstance(s, dict):
            subj_areas.append(s.get("$", ""))

    # Funding
    funding_list = []
    for f in ((item.get("funding-list") or {}).get("funding") or []):
        if isinstance(f, dict):
            funding_list.append({
                "agency": f.get("fund-agency") or f.get("fd:fund-agency", ""),
                "id": f.get("fund-id") or "",
            })

    return json.dumps({
        "doi": doi,
        "title": core.get("dc:title", ""),
        "abstract": core.get("dc:description", ""),
        "authors": author_list[:10],
        "journal": core.get("prism:publicationName", ""),
        "year": (core.get("prism:coverDate") or "")[:4],
        "volume": core.get("prism:volume", ""),
        "issue": core.get("prism:issueIdentifier", ""),
        "pages": f"{core.get('prism:startingPage','')}-{core.get('prism:endingPage','')}".strip("-"),
        "cited_by": core.get("citedby-count", 0),
        "open_access": core.get("openaccess") in ("1", 1, True),
        "keywords": keywords,
        "subject_areas": subj_areas,
        "reference_count": core.get("ref-count", 0),
        "funding": funding_list,
        "publisher": core.get("dc:publisher", ""),
        "url": f"https://doi.org/{doi}",
    }, indent=2)


@mcp.tool()
async def sciencedirect_fetch(doi: str) -> str:
    """Retrieve full text of a ScienceDirect paper via the Elsevier Article API.

    Full text is returned when EITHER:
      (a) The article is open-access (gold or hybrid OA), OR
      (b) Your Elsevier account has institutional access to the journal.

    For purely paywalled articles without institutional access, this returns
    the abstract and metadata only (same as scopus_abstract). Always try
    this tool before falling back to Unpaywall — it is faster and returns
    structured sections rather than raw PDF text.

    Args:
        doi: Paper DOI (e.g., "10.1016/j.jpowsour.2023.233456").
             Strips "https://doi.org/" prefix automatically.

    Returns:
        JSON with full_text_available flag, article sections (if accessible),
        abstract, and metadata. When full text is unavailable, returns abstract
        and a note explaining why.
    """
    import json

    if not _ELSEVIER_API_KEY:
        return json.dumps({"error": "ELSEVIER_API_KEY not set in environment."})

    doi = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")

    async with httpx.AsyncClient(timeout=45.0) as client:
        # Request plain-text article — most useful for extraction
        resp = await client.get(
            f"{SCIENCEDIRECT_BASE}/doi/{doi}",
            headers=_elsevier_headers(accept="application/json"),
            params={"view": "FULL"},
        )

        if resp.status_code == 404:
            return json.dumps({"doi": doi, "error": "Article not found in ScienceDirect."})
        if resp.status_code in (401, 403):
            return json.dumps({
                "doi": doi,
                "full_text_available": False,
                "access_status": "no_entitlement",
                "message": (
                    "Full text not accessible — no institutional subscription or entitlement for this journal. "
                    "Try unpaywall_fetch for an open-access version, or scopus_search for the abstract snippet."
                ),
            })
        if resp.status_code == 400:
            return json.dumps({
                "doi": doi,
                "full_text_available": False,
                "access_status": "bad_request",
                "message": (
                    "ScienceDirect rejected the request — the DOI may not be in ScienceDirect, "
                    "or full-text access requires an institutional token. "
                    "Try unpaywall_fetch or scopus_search instead."
                ),
            })

        resp.raise_for_status()
        data = resp.json()

    # Navigate the ScienceDirect article response structure
    article = data.get("full-text-retrieval-response", {})
    core = article.get("coredata", {})

    # Extract sections from originalText or sections structure
    sections = []
    orig = article.get("originalText", {})
    if orig:
        # Plain text sections
        body = orig.get("body") or orig.get("$", "")
        if body and len(str(body)) > 100:
            sections.append({"section": "body", "text": str(body)[:8000]})

    # Structured sections if available
    for sec in (article.get("document", {}).get("sections", {}).get("section", []) or []):
        if isinstance(sec, dict):
            title = sec.get("section-title", {}).get("$", "") or sec.get("label", "")
            text = sec.get("para", {})
            if isinstance(text, dict):
                text = text.get("$", "")
            elif isinstance(text, list):
                text = " ".join(p.get("$", "") if isinstance(p, dict) else str(p) for p in text)
            if text:
                sections.append({"section": title, "text": str(text)[:3000]})

    full_text_available = len(sections) > 0

    return json.dumps({
        "doi": doi,
        "full_text_available": full_text_available,
        "access_status": "open_access" if core.get("openaccess") in ("1", 1, True) else "institutional",
        "title": core.get("dc:title", ""),
        "abstract": core.get("dc:description", ""),
        "journal": core.get("prism:publicationName", ""),
        "year": (core.get("prism:coverDate") or "")[:4],
        "open_access": core.get("openaccess") in ("1", 1, True),
        "sections": sections,
        "section_count": len(sections),
        "url": f"https://doi.org/{doi}",
        "sciencedirect_url": f"https://www.sciencedirect.com/science/article/pii/{core.get('pii', '')}",
    }, indent=2)


@mcp.tool()
async def crossref_search(
    query: str,
    max_results: int = 20,
    year_from: int = 0,
    year_to: int = 0,
    doc_type: str = "",
) -> str:
    """Search CrossRef for published papers by title/keyword with citation metadata.

    CrossRef indexes 150M+ DOI-registered works across all publishers.
    Particularly useful for:
    - Verifying DOIs and publication details for papers found elsewhere
    - Finding citation counts and funder information
    - Discovering papers from publishers not covered by Scopus/IEEE
    - Checking whether a preprint has been published (by searching the title)

    Args:
        query: Title or keyword query.
        max_results: Number of results (default 20, max 100).
        year_from: Optional start year.
        year_to: Optional end year.
        doc_type: Optional work type — journal-article, proceedings-article,
                  book-chapter, dataset, report. Leave blank for all.

    Returns:
        JSON with DOI, title, authors, journal, year, citation count, funder,
        and open-access license info.
    """
    import json

    params: dict = {
        "query": query,
        "rows": str(min(max_results, 100)),
        "sort": "relevance",
        "mailto": "proposalwriter@tool.local",  # polite pool — faster responses
    }

    filters = []
    if year_from:
        filters.append(f"from-pub-date:{year_from}")
    if year_to:
        filters.append(f"until-pub-date:{year_to}")
    if doc_type:
        filters.append(f"type:{doc_type}")
    if filters:
        params["filter"] = ",".join(filters)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            CROSSREF_BASE,
            params=params,
            headers={"User-Agent": "ProposalWriter/1.0 (mailto:proposalwriter@tool.local)"},
        )
        resp.raise_for_status()
        data = resp.json()

    items = data.get("message", {}).get("items", [])
    total = data.get("message", {}).get("total-results", 0)

    results = []
    for item in items:
        doi = item.get("DOI", "")
        authors_raw = item.get("author", [])
        authors = ", ".join(
            f"{a.get('family', '')} {a.get('given', '')[:1]}".strip()
            for a in authors_raw[:5]
        )
        if len(authors_raw) > 5:
            authors += " et al."

        pub_date = item.get("published", {}).get("date-parts", [[""]])[0]
        year = str(pub_date[0]) if pub_date else ""

        # Funder info
        funders = [
            f.get("name", "")
            for f in (item.get("funder") or [])[:3]
        ]

        # License / OA
        licenses = [lic.get("URL", "") for lic in (item.get("license") or [])[:2]]

        results.append({
            "title": (item.get("title") or [""])[0],
            "authors": authors,
            "journal": (item.get("container-title") or [""])[0],
            "year": year,
            "doi": doi,
            "doc_type": item.get("type", ""),
            "citation_count": item.get("is-referenced-by-count", 0),
            "funders": funders,
            "licenses": licenses,
            "open_access": bool(licenses),
            "url": f"https://doi.org/{doi}" if doi else "",
        })

    return json.dumps({
        "total_results": total,
        "returned": len(results),
        "query": query,
        "results": results,
    }, indent=2)


@mcp.tool()
async def europepmc_search(
    query: str,
    max_results: int = 20,
    year_from: int = 0,
    year_to: int = 0,
    open_access_only: bool = False,
) -> str:
    """Search Europe PMC for biomedical and life-science open-access literature.

    Europe PMC aggregates 45M+ records including PubMed, PubMed Central,
    preprint servers, and EU-funded research outputs. Particularly useful for:
    - Finding full-text open-access versions of biomedical papers
    - Searching EU-funded research (Horizon Europe grantee publications)
    - Accessing preprints from bioRxiv, medRxiv, ChemRxiv in one query

    Args:
        query: Search query. Supports field tags:
               TITLE:term, ABSTRACT:term, AUTH:surname, JOURNAL:name,
               GRANT_AGENCY:name, HAS_FT:y (full text only)
        max_results: Number of results (default 20, max 100).
        year_from: Optional start year filter.
        year_to: Optional end year filter.
        open_access_only: If True, restricts to papers with free full text.

    Returns:
        JSON with paper metadata, full-text availability flag, DOI, PMID,
        citation count, and grant information.
    """
    import json

    q = query
    if year_from and year_to:
        q += f" AND (FIRST_PDATE:[{year_from}-01-01 TO {year_to}-12-31])"
    elif year_from:
        q += f" AND (FIRST_PDATE:[{year_from}-01-01 TO 3000-12-31])"
    elif year_to:
        q += f" AND (FIRST_PDATE:[1900-01-01 TO {year_to}-12-31])"
    if open_access_only:
        q += " AND (OPEN_ACCESS:y)"

    params = {
        "query": q,
        "resultType": "core",
        "pageSize": str(min(max_results, 100)),
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            EUROPEPMC_BASE,
            params=params,
            headers={"User-Agent": "ProposalWriter/1.0 (grant proposal writing tool)"},
        )
        resp.raise_for_status()
        data = resp.json()

    result_list = data.get("resultList", {}).get("result", [])
    total = data.get("hitCount", 0)

    results = []
    for r in result_list:
        results.append({
            "title": r.get("title", ""),
            "authors": r.get("authorString", ""),
            "journal": r.get("journalTitle", ""),
            "year": str(r.get("pubYear", "")),
            "pmid": r.get("pmid", ""),
            "pmcid": r.get("pmcid", ""),
            "doi": r.get("doi", ""),
            "source": r.get("source", ""),  # MED, PPR (preprint), etc.
            "citation_count": r.get("citedByCount", 0),
            "full_text_available": r.get("isOpenAccess") == "Y" or bool(r.get("pmcid")),
            "open_access": r.get("isOpenAccess") == "Y",
            "full_text_url": (
                f"https://europepmc.org/article/{r.get('source', 'MED')}/{r.get('pmid', r.get('pmcid', ''))}"
                if r.get("pmid") or r.get("pmcid") else ""
            ),
            "grant_list": [
                g.get("agency", "")
                for g in (r.get("grantsList", {}).get("grant") or [])[:3]
            ],
            "url": f"https://doi.org/{r.get('doi')}" if r.get("doi") else "",
        })

    return json.dumps({
        "total_results": total,
        "returned": len(results),
        "query": q,
        "results": results,
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
