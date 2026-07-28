"""Riscrittura del reel con l'API Anthropic (Claude).

Prende il profilo brand (system prompt, editabile in-app) + la trascrizione grezza
di Groq e restituisce un JSON con:
  { "transcript_it": ..., "rewritten_reel": ... }
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import anthropic

from .config import get_settings


class RewriteError(RuntimeError):
    pass


@dataclass
class RewriteResult:
    transcript_it: str
    rewritten_reel: str


# Schema per structured outputs: garantisce un JSON valido e completo.
_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "transcript_it": {"type": "string"},
        "rewritten_reel": {"type": "string"},
    },
    "required": ["transcript_it", "rewritten_reel"],
    "additionalProperties": False,
}


def _extract_json(text: str) -> dict:
    """Parsing robusto: gestisce eventuali code-fence o testo attorno al JSON."""
    text = text.strip()
    # rimuovi eventuali ```json ... ```
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # ultimo tentativo: primo blocco {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise RewriteError("La riscrittura non ha restituito un JSON valido.")


def rewrite(brand_prompt: str, raw_transcript: str, source_lang: str | None = None) -> RewriteResult:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RewriteError("ANTHROPIC_API_KEY non configurata.")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    user_content = (
        "Ecco la trascrizione grezza del reel"
        + (f" (lingua rilevata: {source_lang})" if source_lang else "")
        + ":\n\n"
        + raw_transcript.strip()
    )

    common_kwargs = dict(
        model=settings.anthropic_model,
        max_tokens=4000,
        system=brand_prompt,
        messages=[{"role": "user", "content": user_content}],
    )

    try:
        # Preferiamo structured outputs per un JSON sempre valido.
        try:
            resp = client.messages.create(
                **common_kwargs,
                output_config={
                    "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}
                },
            )
        except (anthropic.BadRequestError, TypeError):
            # Il modello scelto potrebbe non supportare structured outputs:
            # ripiega sul prompt "rispondi solo con JSON" (già nel brand).
            resp = client.messages.create(**common_kwargs)
    except anthropic.APIStatusError as exc:
        raise RewriteError(f"Errore API Anthropic ({exc.status_code}): {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise RewriteError("Errore di connessione all'API Anthropic.") from exc

    text = next((b.text for b in resp.content if b.type == "text"), "")
    data = _extract_json(text)

    return RewriteResult(
        transcript_it=(data.get("transcript_it") or "").strip(),
        rewritten_reel=(data.get("rewritten_reel") or "").strip(),
    )
