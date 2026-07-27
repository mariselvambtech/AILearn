"""
Crawl4AI Helper Module for LLM Markdown Page Understanding & Semantic Fingerprinting.

This module uses Crawl4AI / html2text logic to convert dynamic web pages into
clean LLM Markdown, generates concise page summaries, and creates semantic element
fingerprints (tag, role, visible text, parent context) for 100% accurate self-healing.
"""
import re
from typing import Dict, Any, Optional

try:
    import html2text
    HAVE_HTML2TEXT = True
except ImportError:
    HAVE_HTML2TEXT = False


def html_to_llm_markdown(html_content: str, url: str = "") -> str:
    """
    Convert raw HTML DOM into clean, noise-free LLM Markdown.
    Strips scripts, styles, SVG paths, and unnecessary styling tags.
    """
    if not html_content:
        return ""

    # Prune noise before conversion
    cleaned_html = re.sub(r"<(script|style|svg|noscript|iframe)[^>]*>[\s\S]*?</\1>", "", html_content, flags=re.IGNORECASE)
    
    if HAVE_HTML2TEXT:
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0
        markdown = h.handle(cleaned_html)
    else:
        # Fallback regex strip
        markdown = re.sub(r"<[^>]+>", " ", cleaned_html)

    # Collapse excess whitespace
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip()


def generate_page_summary(markdown_text: str, url: str = "") -> str:
    """
    Extract a concise 1-2 sentence page summary from LLM Markdown content.
    """
    if not markdown_text:
        return f"Web page: {url}" if url else "Unknown web page"

    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    
    # Grab main headings
    headings = [line.lstrip("#").strip() for line in lines if line.startswith("#")]
    text_blocks = [line for line in lines if not line.startswith("#") and len(line) > 20]

    title = headings[0] if headings else (url.split("/")[-1] or url)
    sample_context = " ".join(text_blocks[:2])[:180] if text_blocks else ""

    summary = f"Page Title: '{title}'."
    if sample_context:
        summary += f" Context: {sample_context}..."
    return summary


def build_element_fingerprint(element_info: Dict[str, Any], page_summary: str = "") -> Dict[str, Any]:
    """
    Build a rich semantic fingerprint for recorded elements.
    Includes tag, role, visible text, parent container anchor, and page summary.
    """
    return {
        "page_summary": page_summary,
        "tag": element_info.get("tag", "").lower(),
        "role": element_info.get("role", ""),
        "text": element_info.get("text", "").strip(),
        "attributes": element_info.get("attributes", {}),
        "parent_tag": element_info.get("parent_tag", ""),
        "parent_id": element_info.get("parent_id", ""),
        "parent_class": element_info.get("parent_class", "")
    }
