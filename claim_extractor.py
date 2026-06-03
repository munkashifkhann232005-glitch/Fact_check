"""
claim_extractor.py
------------------
Uses Google Gemini API to identify and extract factual claims from document text.
"""

import json
import re
from google import genai


def extract_claims_from_text(text: str, api_key: str) -> list[str]:
    """
    Use Gemini to identify all factual claims in the provided text.

    Targets: statistics, percentages, dates, financial figures,
    market size claims, technical figures, and measurable statements.

    Args:
        text:    Full document text extracted from PDF.
        api_key: Google Gemini API key.

    Returns:
        A list of factual claim strings.

    Raises:
        ValueError: If Gemini returns no claims or an unexpected format.
    """
    client = genai.Client(api_key=api_key)

    # Truncate text if it's extremely long (Gemini has context limits)
    max_chars = 30000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Text truncated for processing...]"

    prompt = f"""You are a fact-checking assistant. Your task is to extract every verifiable factual claim from the document text below.

Focus specifically on:
- Statistics and numerical data (e.g., "70% of users prefer X")
- Dates and timelines (e.g., "The company was founded in 2010")
- Financial figures (e.g., "Revenue reached $5 billion in 2023")
- Market size claims (e.g., "The global AI market is worth $200 billion")
- Technical specifications and figures (e.g., "The processor runs at 3.2 GHz")
- Percentages and growth rates (e.g., "Sales grew by 45% year-over-year")
- Named facts and attributions (e.g., "NASA reported that...")
- Any other measurable or verifiable statements

Rules:
- Extract ONLY verifiable claims, not opinions or vague statements
- Each claim should be self-contained and understandable on its own
- Do NOT include the same claim twice
- Return ONLY a JSON array of strings, with no extra text or markdown

Document text:
{text}

Return format (JSON array only):
["claim 1", "claim 2", "claim 3"]"""

    
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        response_text = response.text.strip()

        # Strip markdown code fences if present
        response_text = re.sub(r"```json\s*", "", response_text)
        response_text = re.sub(r"```\s*", "", response_text)
        response_text = response_text.strip()

        claims = json.loads(response_text)
        

        if not isinstance(claims, list):
            raise ValueError("Gemini returned unexpected format (not a list).")

        # Filter out empty strings
        claims = [c.strip() for c in claims if isinstance(c, str) and c.strip()]

        if not claims:
            raise ValueError("No factual claims were identified in the document.")

        return claims

    except json.JSONDecodeError:
        # Fallback: try to extract list items from plain text
        lines = response_text.split("\n")
        claims = []
        for line in lines:
            line = line.strip().lstrip("-•*123456789. ")
            if len(line) > 20:  # Minimum meaningful claim length
                claims.append(line)
        if claims:
            return claims
        raise ValueError(
            "Failed to parse claims from Gemini response. Please try again."
        )
    except Exception as e:
        raise ValueError(f"Claim extraction failed: {str(e)}")
