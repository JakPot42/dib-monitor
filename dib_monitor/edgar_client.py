"""
SEC EDGAR API client.
Only used in live (non-demo) mode. All demo data comes from seed_data.py.
"""
from __future__ import annotations
import json
import re
from typing import Optional
import urllib.request
import urllib.parse
import urllib.error

from .config import EDGAR_USER_AGENT


class EdgarError(Exception):
    pass


def _get(url: str, timeout: int = 10) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": EDGAR_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise EdgarError(f"HTTP {exc.code} fetching {url}") from exc
    except Exception as exc:
        raise EdgarError(f"Error fetching {url}: {exc}") from exc


def search_company_cik(company_name: str) -> Optional[str]:
    """
    Search EDGAR for a company by name, return its CIK (zero-padded to 10 digits).
    Returns None if not found.
    """
    encoded = urllib.parse.quote(company_name)
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{encoded}%22&dateRange=custom&startdt=2020-01-01&enddt=2026-12-31&forms=10-K"
    try:
        data = json.loads(_get(url))
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return None
        entity_id = hits[0].get("_source", {}).get("entity_id")
        if entity_id:
            return str(entity_id).zfill(10)
        return None
    except EdgarError:
        return None


def fetch_latest_10k_text(cik: str, max_chars: int = 15_000) -> Optional[str]:
    """
    Fetch the text of the most recent 10-K filing for a company.
    Returns at most max_chars characters (focused on MD&A and liquidity sections).
    Returns None if no filing is found.
    """
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    try:
        data = json.loads(_get(url))
    except EdgarError:
        return None

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])

    # Find the most recent 10-K
    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accessions[i].replace("-", "")
            doc = primary_docs[i]
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession}/{doc}"
            )
            try:
                raw = _get(filing_url, timeout=20).decode("utf-8", errors="ignore")
                text = re.sub(r"<[^>]+>", " ", raw)
                text = re.sub(r"\s+", " ", text).strip()
                return text[:max_chars]
            except EdgarError:
                return None

    return None


def fetch_13f_owners(cik: str) -> list[dict]:
    """
    Stub — returns empty list in this version.
    Live 13F parsing requires institutional CIK lookup (out of scope for MVP).
    """
    return []


def fetch_latest_8k_exhibit99(cik: str, max_chars: int = 8_000) -> Optional[dict]:
    """
    Fetch Exhibit 99 text from the most recent 8-K filing (earnings transcript/press release).
    Returns {"text": str, "filed_date": str, "accession": str} or None if unavailable.

    8-K Exhibit 99 filings are where executives disclose forward-looking supply chain
    language (e.g., "diversifying away from Supplier X due to export controls") before
    that intent appears in formal 10-K filings.
    """
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    try:
        data = json.loads(_get(url))
    except EdgarError:
        return None

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    filing_dates = filings.get("filingDate", [])

    for i, form in enumerate(forms):
        if form != "8-K":
            continue

        accession_dashes = accessions[i]
        accession_nodash = accession_dashes.replace("-", "")
        filed_date = filing_dates[i] if i < len(filing_dates) else "Unknown"
        cik_int = int(cik)

        # Try the filing index JSON to find an Exhibit 99 document
        index_url = (
            f"https://data.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_nodash}/{accession_dashes}-index.json"
        )
        try:
            index_data = json.loads(_get(index_url, timeout=10))
            for doc in index_data.get("documents", []):
                doc_type = str(doc.get("type", "")).upper()
                filename = doc.get("filename", "")
                if "EX-99" in doc_type and filename:
                    exhibit_url = (
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik_int}/{accession_nodash}/{filename}"
                    )
                    try:
                        raw = _get(exhibit_url, timeout=20).decode("utf-8", errors="ignore")
                        text = re.sub(r"<[^>]+>", " ", raw)
                        text = re.sub(r"\s+", " ", text).strip()
                        if len(text) > 100:
                            return {"text": text[:max_chars], "filed_date": filed_date, "accession": accession_dashes}
                    except EdgarError:
                        pass
        except (EdgarError, Exception):
            pass

        # Fallback: fetch the primary document of the 8-K itself
        primary_doc = primary_docs[i] if i < len(primary_docs) else None
        if primary_doc:
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik_int}/{accession_nodash}/{primary_doc}"
            )
            try:
                raw = _get(doc_url, timeout=20).decode("utf-8", errors="ignore")
                text = re.sub(r"<[^>]+>", " ", raw)
                text = re.sub(r"\s+", " ", text).strip()
                if len(text) > 200:
                    return {"text": text[:max_chars], "filed_date": filed_date, "accession": accession_dashes}
            except EdgarError:
                continue

    return None
