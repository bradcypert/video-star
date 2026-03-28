"""Generate a YouTube video description.

Two paths:
  1. OpenAI GPT-4o (if OPENAI_API_KEY is configured) — rich, SEO-optimised.
  2. Template fallback — uses Deepgram summary + topics + chapters.
"""

from __future__ import annotations

from video_star.models.pipeline_result import PipelineResult
from video_star.utils.time_utils import seconds_to_youtube


def generate_description(result: PipelineResult, settings) -> str:  # type: ignore[type-arg]
    if settings.USE_OPENAI_DESCRIPTION and settings.OPENAI_API_KEY:
        try:
            return _openai_description(result, settings.OPENAI_API_KEY)
        except Exception:
            pass  # Fall through to template
    return _template_description(result)


# ---------------------------------------------------------------------------
# OpenAI path
# ---------------------------------------------------------------------------

def _openai_description(result: PipelineResult, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    chapters_text = "\n".join(
        f"  {seconds_to_youtube(c.start)} {c.title}" for c in result.chapters
    )
    topics_text = ", ".join(result.topics[:15]) if result.topics else "N/A"

    prompt = (
        "You are a YouTube SEO expert. Write a compelling YouTube video description "
        "based on the following information.\n\n"
        f"Summary:\n{result.summary}\n\n"
        f"Topics covered: {topics_text}\n\n"
        f"Chapters:\n{chapters_text}\n\n"
        "Requirements:\n"
        "- Start with a strong 1-2 sentence hook\n"
        "- 2-3 body paragraphs expanding on what viewers will learn\n"
        "- A chapters section (copy the timestamps exactly as provided)\n"
        "- End with 15-20 relevant SEO hashtags (format: #keyword)\n"
        "- Keep the total description under 5000 characters\n"
        "- Do NOT fabricate information not present in the summary or topics\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Template fallback
# ---------------------------------------------------------------------------

def _template_description(result: PipelineResult) -> str:
    lines: list[str] = []

    # Hook — use the summary
    if result.summary:
        lines.append(result.summary)
        lines.append("")

    # Topics
    if result.topics:
        lines.append("In this video we cover:")
        for topic in result.topics[:12]:
            lines.append(f"• {topic}")
        lines.append("")

    # Chapters
    if result.chapters:
        lines.append("⏱ CHAPTERS")
        for chapter in result.chapters:
            lines.append(f"{seconds_to_youtube(chapter.start)} {chapter.title}")
        lines.append("")

    # Hashtags from topics
    if result.topics:
        hashtags = " ".join(
            "#" + t.replace(" ", "").replace("-", "")
            for t in result.topics[:20]
            if t
        )
        lines.append(hashtags)

    return "\n".join(lines).strip()
