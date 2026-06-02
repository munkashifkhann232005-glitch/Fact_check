"""
verifier.py
-----------
Verifies individual factual claims by:
1. Searching the web with Tavily API
2. Sending the claim + evidence to Gemini for classification
"""

import json
import re
import time
from google import genai
from tavily import TavilyClient


# --------------------------------------------------------------------------- #
#  Verdict dataclass (simple dict for portability)                             #
# --------------------------------------------------------------------------- #

def create_verdict(claim: str, status: str, explanation: str, source: str) -> dict:
    """
    Build a standardised verdict dictionary.

    Args:
        claim:       The original claim string.
        status:      One of 'Verified', 'Inaccurate', 'False', or 'Unverifiable'.
        explanation: Gemini's reasoning for the classification.
        source:      Primary supporting URL or 'N/A'.

    Returns:
        Dictionary with keys: claim, status, explanation, source.
    """
    return {
        "claim": claim,
        "status": status,
        "explanation": explanation,
        "source": source,
    }


# --------------------------------------------------------------------------- #
#  Web search via Tavily                                                        #
# --------------------------------------------------------------------------- #

def search_evidence(claim: str, tavily_api_key: str, max_results: int = 5) -> list[dict]:
    """
    Search the web for evidence related to a given claim.

    Args:
        claim:          The factual claim to search for.
        tavily_api_key: Tavily API key.
        max_results:    Number of search results to retrieve (default 5).

    Returns:
        List of result dicts with keys: title, url, content.
    """
    try:
        client = TavilyClient(api_key=tavily_api_key)
        response = client.search(
            query=claim,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", "")[:1000],  # Limit content length
            })
        return results

    except Exception as e:
        # Return empty list so verification can still run with limited evidence
        return [{"title": "Search failed", "url": "N/A", "content": str(e)}]


# --------------------------------------------------------------------------- #
#  Claim classification via Gemini                                              #
# --------------------------------------------------------------------------- #

def classify_claim(claim: str, search_results: list[dict], gemini_api_key: str) -> dict:
    """
    Use Gemini to classify a claim based on web evidence.

    Args:
        claim:          The factual claim string.
        search_results: List of evidence dicts from Tavily.
        gemini_api_key: Google Gemini API key.

    Returns:
        Verdict dictionary with keys: claim, status, explanation, source.
    """
    client = genai.Client(api_key=gemini_api_key)

    # Format evidence for the prompt
    if not search_results or search_results[0].get("url") == "N/A":
        evidence_text = "No web evidence could be retrieved for this claim."
        primary_source = "N/A"
    else:
        evidence_parts = []
        for i, r in enumerate(search_results, 1):
            evidence_parts.append(
                f"[{i}] Title: {r['title']}\n    URL: {r['url']}\n    Content: {r['content']}"
            )
        evidence_text = "\n\n".join(evidence_parts)
        primary_source = search_results[0].get("url", "N/A")

    prompt = f"""You are an expert fact-checker. Analyse the claim below against the provided web evidence and classify it accurately.

Claim:
"{claim}"

Web Evidence:
{evidence_text}

Classification rules:
- **Verified**: The evidence clearly supports or confirms the claim.
- **Inaccurate**: The claim is partially correct but contains errors (e.g., wrong number, wrong year).
- **False**: The evidence directly contradicts the claim.
- **Unverifiable**: There is insufficient evidence to confirm or deny the claim.

Return ONLY a valid JSON object with exactly these keys (no markdown, no extra text):
{{
  "status": "<Verified | Inaccurate | False | Unverifiable>",
  "explanation": "<2-3 sentence explanation of the classification>",
  "source": "<the most relevant URL from the evidence, or 'N/A'>"
}}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        response_text = response.text.strip()

        # Strip markdown fences
        response_text = re.sub(r"```json\s*", "", response_text)
        response_text = re.sub(r"```\s*", "", response_text)
        response_text = response_text.strip()

        result = json.loads(response_text)

        # Validate expected keys
        status      = result.get("status", "Unverifiable")
        explanation = result.get("explanation", "No explanation provided.")
        source      = result.get("source", primary_source)

        # Normalise status
        valid_statuses = {"Verified", "Inaccurate", "False", "Unverifiable"}
        if status not in valid_statuses:
            status = "Unverifiable"

        return create_verdict(claim, status, explanation, source)

    except json.JSONDecodeError:
        return create_verdict(
            claim,
            "Unverifiable",
            "Could not parse Gemini's response. Manual review recommended.",
            primary_source,
        )
    except Exception as e:
        return create_verdict(
            claim,
            "Unverifiable",
            f"Verification error: {str(e)}",
            "N/A",
        )


# --------------------------------------------------------------------------- #
#  Main verification pipeline                                                   #
# --------------------------------------------------------------------------- #

def verify_claims(
    claims: list[str],
    gemini_api_key: str,
    tavily_api_key: str,
    progress_callback=None,
) -> list[dict]:
    """
    Verify a list of claims end-to-end: search → classify.

    Args:
        claims:            List of claim strings to verify.
        gemini_api_key:    Google Gemini API key.
        tavily_api_key:    Tavily API key.
        progress_callback: Optional callable(current, total, claim_text).

    Returns:
        List of verdict dictionaries.
    """
    verdicts = []
    total = len(claims)

    for i, claim in enumerate(claims):
        if progress_callback:
            progress_callback(i, total, claim)

        # Step 1: Search web evidence
        evidence = search_evidence(claim, tavily_api_key)

        # Step 2: Classify with Gemini
        verdict = classify_claim(claim, evidence, gemini_api_key)
        verdicts.append(verdict)

        # Small delay to respect API rate limits
        time.sleep(0.5)

    if progress_callback:
        progress_callback(total, total, "Complete")

    return verdicts
