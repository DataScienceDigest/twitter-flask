import requests
import json
import re
from urllib.parse import urlencode


# ─── GEMINI API ───────────────────────────────────────────────────────────────
def gem_sentiment(news_data):
    payload_data = {
        "f.req": json.dumps([
            None,
            json.dumps([
                [
                    f"""
                    You are a financial news analyst and web content extractor.

                    You will be given multiple URLs. Your job is to:
                    1. Visit and read the full content of EVERY URL provided.
                    2. Extract all relevant information from each article.
                    3. Present the output in the structured format described below.

                    ---

                    ## STEP 1 — SUMMARY TABLE

                    Create a markdown table with one row per article. Use these columns:

                    | # | Source | Article Title | Published Date | Main Topic | Companies / Stocks Mentioned | Key Points (2-3 lines) | Market Impact | Sentiment | Important Numbers | URL |

                    Rules:
                    - If a field is not available, write `N/A`.
                    - Do NOT skip any URL.
                    - Do NOT fabricate or assume any information.
                    - For stocks/companies, list ALL mentioned (comma-separated).
                    - Keep Key Points concise but meaningful (no filler).
                    - Sentiment must be one of: Positive / Negative / Neutral / Mixed.

                    ---

                    ## STEP 2 — ARTICLE-WISE DEEP DIVE

                    After the table, for each article, provide a detailed breakdown:

                    **Article [N]: [Title]**
                    - **URL:** ...
                    - **Source:** ...
                    - **Date:** ...
                    - **Stocks/Companies:** ...
                    - **Summary:** (3-5 sentences covering what happened, why it matters)
                    - **Key Numbers:** (prices, targets, % moves, earnings figures, etc.)
                    - **Market Impact:** (what could this mean for traders/investors?)
                    - **Sentiment:** Positive / Negative / Neutral / Mixed — and why

                    ---

                    ## STEP 3 — COMBINED ANALYSIS

                    1. **Overall Summary:** A 4-6 sentence paragraph summarizing all articles together.
                    2. **All Unique Stocks/Companies Mentioned:** A consolidated list (alphabetically sorted).
                    3. **Common Themes / Market Trends:** What patterns or repeated topics appear across articles?
                    4. **Actionable Insights:** (If applicable) Any notable buy/sell signals, results, upgrades, downgrades, or events worth flagging.

                    ---

                    Here are the URLs to process:

                    {news_data}

                    Important reminders:
                    - Read EVERY URL before responding.
                    - Do not mix up information between articles.
                    - If a URL is inaccessible or returns an error, note it clearly and skip gracefully.
                    - Prioritize accuracy over speed.
                    """
                ],
            ])
        ]),
    }

    PAYLOAD = urlencode(payload_data)

    BASE_URL = "https://gemini.google.com/u/2/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"

    HEADERS = {
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }

    try:
        response = requests.post(
            BASE_URL,
            params={},
            headers=HEADERS,
            data=PAYLOAD,
            timeout=(10, 90)
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


# ─── RESPONSE PARSER — DEEP EXTRACT ──────────────────────────────────────────
def deep_extract_text(raw_response: str) -> str:
    """
    Fully unwrap Google WRB/XSSI response and extract all human-readable text.
    Handles multiple levels of JSON-encoded strings.
    """

    # Step 1: Strip XSSI prefix
    clean = raw_response.strip()
    if clean.startswith(")]}'"):
        clean = clean[4:].lstrip("\n")

    # Step 2: Recursively parse — handles strings that are themselves JSON
    def recursive_parse(obj):
        if isinstance(obj, str):
            stripped = obj.strip()
            if stripped.startswith(("{", "[", '"')):
                try:
                    return recursive_parse(json.loads(stripped))
                except (json.JSONDecodeError, ValueError):
                    pass
            return obj

        elif isinstance(obj, list):
            return [recursive_parse(item) for item in obj]

        elif isinstance(obj, dict):
            return {k: recursive_parse(v) for k, v in obj.items()}

        return obj

    # Step 3: Collect only meaningful text strings
    def collect_text(obj, min_length=40):
        texts = []
        if isinstance(obj, str):
            s = obj.strip()
            if len(s) >= min_length:
                texts.append(s)
        elif isinstance(obj, list):
            for item in obj:
                texts.extend(collect_text(item, min_length))
        elif isinstance(obj, dict):
            for v in obj.values():
                texts.extend(collect_text(v, min_length))
        return texts

    try:
        outer = json.loads(clean)
        fully_parsed = recursive_parse(outer)
        texts = collect_text(fully_parsed)
        return "\n\n---\n\n".join(texts)

    except Exception as e:
        return f"Parse error: {e}\n\nRaw preview:\n{raw_response[:300]}"


# ─── RESPONSE PARSER — MARKDOWN BLOCKS ───────────────────────────────────────
def extract_markdown_blocks(raw_response: str) -> list:
    """
    Specifically hunt for markdown content (##, **, |) inside the response.
    Returns a list of clean markdown strings found.
    """
    clean = raw_response.strip()
    if clean.startswith(")]}'"):
        clean = clean[4:].lstrip("\n")

    unescaped = clean.replace('\\"', '"').replace('\\\\n', '\n').replace('\\n', '\n')

    markdown_pattern = re.findall(
        r'"((?:[^"\\]|\\.)*(?:#{1,6} |(?:\*\*)|(?:\|))(?:[^"\\]|\\.)*)"',
        unescaped
    )

    results = []
    for block in markdown_pattern:
        cleaned = (block
                   .replace('\\n', '\n')
                   .replace('\\"', '"')
                   .replace('\\\\', '\\')
                   .strip())
        if len(cleaned) > 50:
            results.append(cleaned)

    return results


# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────
def process_links(links: list, portal_brains: dict = None) -> str:
    """
    Takes a list of URLs + optional Portal Brains content dict,
    sends everything to Gemini, returns parsed text result.
    """
    if not links and not portal_brains:
        return "No links or content provided."

    # Build news_data: URLs first
    news_data = "\n".join(links) if links else ""

    # Append Portal Brains content as direct text (no URL)
    if portal_brains:
        news_data += f"""

---

**Additional Source: Trade Brains Portal (Stock Alert — Direct Content)**
Date: {portal_brains.get('date', 'N/A')} {portal_brains.get('time', 'N/A')}
Heading: {portal_brains.get('heading', 'N/A')}

Content:
{portal_brains.get('content', 'N/A')}

---
"""

    print(f"\nSending {len(links)} URLs + Portal Brains content to Gemini...")
    raw_response = gem_sentiment(news_data)

    if not raw_response:
        return "Gemini returned no response."

    print("Parsing Gemini response...")
    result = deep_extract_text(raw_response)

    return result