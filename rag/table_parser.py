"""
Stage 2b: RAW TABLE GRID -> CLEAN MARKDOWN + ONE-LINE SUMMARY

The grid itself (list of rows/cells) always comes from a local library
(pdfplumber / python-pptx - see parser.py), since that's just file-format
parsing, not "understanding". What's swappable is how that raw grid gets
turned into something worth embedding and citing:

    TABLE_PARSER_BACKEND=api    -> Claude reformats the grid into clean
                                    Markdown and writes a 1-line summary
                                    ("Revenue grew from $42M to $51M...").
                                    This is what makes messy/merged-cell
                                    tables searchable in plain language.
    TABLE_PARSER_BACKEND=local  -> pure string formatting, no LLM call,
                                    works fully offline.
"""
from typing import List
from . import config


def _rows_to_markdown(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    header, *body = rows
    width = len(header)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for row in body:
        row = row + [""] * (width - len(row)) if len(row) < width else row[:width]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def parse_table_local(rows: List[List[str]]) -> dict:
    markdown = _rows_to_markdown(rows)
    header = rows[0] if rows else []
    summary = f"Table with columns: {', '.join(c for c in header if c)}" if header else "Table"
    return {"markdown": markdown, "summary": summary}


def parse_table_api(rows: List[List[str]]) -> dict:
    from anthropic import Anthropic
    if not config.ANTHROPIC_API_KEY:
        return parse_table_local(rows)

    raw_grid = "\n".join([" | ".join(r) for r in rows])
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = (
        "You are cleaning a table extracted from a business document. The raw grid "
        "below may have OCR noise, merged cells, or misaligned columns.\n\n"
        f"RAW GRID:\n{raw_grid}\n\n"
        "Return exactly two sections, nothing else:\n"
        "MARKDOWN:\n<the table reformatted as clean GitHub-flavored Markdown>\n\n"
        "SUMMARY:\n<one sentence describing what this table shows, mentioning key "
        "figures and trends if numeric, e.g. 'Revenue by year: $42M (2024) to $51M (2025), up 21%.'>"
    )
    try:
        resp = client.messages.create(
            model=config.ANTHROPIC_TEXT_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.content[0].text
        markdown, summary = "", ""
        if "SUMMARY:" in content:
            md_part, summary_part = content.split("SUMMARY:", 1)
            markdown = md_part.replace("MARKDOWN:", "").strip()
            summary = summary_part.strip()
        else:
            markdown = content.strip()
        if not markdown:
            markdown = _rows_to_markdown(rows)
        return {"markdown": markdown, "summary": summary or "Table"}
    except Exception:
        return parse_table_local(rows)


def parse_table(rows: List[List[str]]) -> dict:
    if config.TABLE_PARSER_BACKEND == "local":
        return parse_table_local(rows)
    return parse_table_api(rows)
