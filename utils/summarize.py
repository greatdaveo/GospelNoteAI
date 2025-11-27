import math
import re
import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI, BadRequestError, RateLimitError

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# To ensure 4 chars per token heuristic


def _approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _split_into_sentences(text: str) -> List[str]:
    # To normalize whitespace
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    # To split on ., !, ? followed by space & capital/number (cheap splitter)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def _group_by_tokens(sentences: List[str], max_tokens: int, overlap: int = 0) -> List[str]:
    chunks, cur, budget = [], [], 0
    for s in sentences:
        t = _approx_tokens(s)
        if budget + t > max_tokens and cur:
            chunks.append(" ".join(cur))
            # To keep small overlap to avoid cutting thoughts mid-sentence
            if overlap > 0:
                cur = cur[-overlap:]
                budget = _approx_tokens(" ".join(cur))
            else:
                cur, budget = [], 0
        cur.append(s)
        budget += t
    if cur:
        # The final chunk
        chunks.append(" ".join(cur))
    return chunks

# PROMPTS
# The System prompt
SYS = (
    "You produce concise, accurate sermon notes. With no fluff. "
    "Never invent facts or verses not in the transcript."
)

# The Map prompt, applied to each chunk
MAP_USER_TMPL = """
You are a gospel sermon note writer and summarizer.

INSTRUCTIONS:
- Use only the transcript content; do not improvise.
- Extract key points from the sermon.
- Write in expressive bullet style, e.g., “The way of the Lord is… (Genesis 1:1)”.
- If Bible verses are mentioned, include them after the point.
- Normalize spoken verse formats, e.g., “John chapter 3 verse to 5” -> “John 3:2–5”.
- Do NOT add verses if none are mentioned.
- Include headings/subheadings where clearly implied.
- If this is not a sermon, say exactly: “This is not a sermon.”

TRANSCRIPT (Part {part} of {total}):
{chunk}

Summarize now into 5–10 clear bullets (with no intro/outro).
"""

# To reduce prompt, and merge partial bullet lists
REDUCE_USER_TMPL = """
You are a gospel sermon note writer.

Here are partial bullet lists from multiple transcript chunks:

{bullets}

Please merge them into a single, non-redundant set of bullets:
- Keep all distinct key points.
- Remove duplicates and overlaps.
- Preserve Bible verses and normalized references.
- Keep headings/subheadings if present.
- Maintain the concise expressive style.
"""

# To splits on paragraph/sentence-ish boundaries to stay under model limits.
def _split_transcript(text: str, max_chars: int = 3500) -> List[str]:
    # To normalize newlines
    text = re.sub(r"\r\n?", "\n", text).strip()

    # To prefer paragraph splits, then sentences
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks: List[str] = []
    buf = []

    def flush():
        if buf:
            chunks.append("\n".join(buf).strip())

    current_len = 0
    for p in paragraphs:
        if len(p) > max_chars:  # very long paragraph -> sentence split
            # For naive sentence split
            sentences = re.split(r"(?<=[\.\!\?])\s+", p)
            for s in sentences:
                if current_len + len(s) + 1 > max_chars:
                    flush()
                    buf.clear()
                    current_len = 0
                buf.append(s)
                current_len += len(s) + 1
        else:
            if current_len + len(p) + 1 > max_chars:
                flush()
                buf.clear()
                current_len = 0
            buf.append(p)
            current_len += len(p) + 1

    flush()
    return chunks if chunks else [text]

def _summarize_chunk(text: str, part: int, total: int, model: str = "gpt-4o-mini") -> List[str]:
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=600,
            messages=[
                {"role": "system", "content": SYS},
                {"role": "user", "content": MAP_USER_TMPL.format(chunk=text, part=part, total=total)},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        bullets = [
            re.sub(r"^[\-\*\•\s]+", "", line).strip()
            for line in content.splitlines()
            if line.strip()
        ]
        return [b for b in bullets if b]
    except BadRequestError as e:
        # Surface the actual model error text if present
        msg = getattr(e, "message", str(e))
        raise RuntimeError(f"OpenAI BadRequest: {msg}")
    except RateLimitError:
        raise RuntimeError("OpenAI rate limit hit; please retry shortly.")
    except Exception as e:
        raise RuntimeError(f"Chunk summarization failed: {str(e)}")

def _reduce_bullets(partials: List[str], model: str = "gpt-4o-mini") -> List[str]:
    try:
        # To join partial lists and keep it safely under a few thousand chars
        joined = "\n\n".join(partials)
        if len(joined) > 12000:  # To hard cap if you there are many long chunks
            joined = joined[:12000]

        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=800,
            messages=[
                {"role": "system", "content": SYS},
                {"role": "user", "content": REDUCE_USER_TMPL.format(bullets=joined)},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        bullets = [
            re.sub(r"^[\-\*\•\s]+", "", line).strip()
            for line in content.splitlines()
            if line.strip()
        ]
        return [b for b in bullets if b]
    except BadRequestError as e:
        msg = getattr(e, "message", str(e))
        raise RuntimeError(f"OpenAI BadRequest (reduce): {msg}")
    except RateLimitError:
        raise RuntimeError("OpenAI rate limit hit (reduce); please retry shortly.")
    except Exception as e:
        raise RuntimeError(f"Reduce step failed: {str(e)}")

# To accepts full transcript and returns final bullets list.
# Internally: split -> map (per chunk) -> reduce (merge).
def generate_summary(transcript: str) -> List[str]:
    if not transcript or not transcript.strip():
        return []

    chunks = _split_transcript(transcript, max_chars=3500)

    # Map
    partial_lists: List[str] = []
    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        partial = _summarize_chunk(chunk, part=i, total=total)
        # Store as a clean list string for reducer
        partial_lists.append("\n".join(f"- {p}" for p in partial))

    # Reduce
    final = _reduce_bullets(partial_lists)

    return final