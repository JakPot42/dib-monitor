"""
Claude Haiku extracts structured financial data and ownership flags
from 10-K/10-Q filing text.

Claude proposes; deterministic code scores. Same pattern as all prior projects.
"""
from __future__ import annotations
import json
import re
from typing import Optional

import anthropic

from .config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS


class AnalystError(Exception):
    pass


_EXTRACTION_PROMPT = """\
You are a financial analyst specializing in defense-sector suppliers and SEC filings.

Extract the following financial data from the 10-K/10-Q excerpt below for {company_name}.
All dollar amounts should be in millions USD.

FILING EXCERPT:
{filing_text}

Return ONLY valid JSON with these exact keys (use null for any field you cannot find):
{{
  "revenue_mm": <float or null>,
  "total_debt_mm": <float or null>,
  "cash_mm": <float or null>,
  "ebitda_mm": <float or null>,
  "debt_service_annual_mm": <float or null>,
  "covenant_summary": "<string summarizing any financial maintenance covenants, or null>",
  "going_concern_flag": <true or false>,
  "going_concern_quote": "<direct quote of going concern language, or null>",
  "near_term_maturity_mm": <float: debt maturing within 24 months in $M, or null>,
  "near_term_maturity_date": "<string: maturity date if found, or null>",
  "confidence": "<high|medium|low>"
}}"""

_OWNERSHIP_FLAG_PROMPT = """\
You are a national security financial intelligence analyst.

For the institutional owners listed below, flag any that appear to:
1. Be controlled by or affiliated with a foreign government (China, Russia, Iran, North Korea)
2. Have names suggesting shell company structures or obscure beneficial ownership
3. Represent CFIUS-relevant national security concerns given they hold equity in a US defense supplier

COMPANY: {company_name}
OWNERS:
{owners_list}

Return a JSON array. Only include owners with genuine concerns.
Each element: {{"owner_name": "...", "flag_reason": "...", "risk_level": "HIGH|MEDIUM|LOW", "cfius_flag": true|false}}
If no owners are flagged, return an empty array []."""


def _parse_json_from_response(text: str) -> dict | list:
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def extract_financials(
    company_name: str,
    filing_text: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Call Claude to extract structured financial data from 10-K/10-Q text.
    Returns a dict with keys matching the extraction prompt schema.
    Raises AnalystError on Claude failure.
    """
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    prompt = _EXTRACTION_PROMPT.format(
        company_name=company_name,
        filing_text=filing_text[:8_000],   # truncate to stay within token limits
    )
    try:
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        result = _parse_json_from_response(raw)
        if not isinstance(result, dict):
            raise AnalystError("Claude returned non-dict response")
        return result
    except AnalystError:
        raise
    except Exception as exc:
        raise AnalystError(f"Claude API error: {exc}") from exc


def flag_ownership_concerns(
    company_name: str,
    owners: list[dict],
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Call Claude to flag unusual or foreign-connected ownership.
    Returns a list of flagged owner dicts.
    Raises AnalystError on Claude failure.
    """
    if not owners:
        return []

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    owners_text = "\n".join(
        f"- {o.get('owner_name', 'Unknown')} ({o.get('pct_owned', 0):.1f}%)"
        + (f", country: {o['country']}" if o.get("country") else "")
        + (f", type: {o['owner_type']}" if o.get("owner_type") else "")
        for o in owners
    )
    prompt = _OWNERSHIP_FLAG_PROMPT.format(
        company_name=company_name,
        owners_list=owners_text,
    )
    try:
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        result = _parse_json_from_response(raw)
        if not isinstance(result, list):
            return []
        return result
    except AnalystError:
        raise
    except Exception as exc:
        raise AnalystError(f"Claude API error: {exc}") from exc
