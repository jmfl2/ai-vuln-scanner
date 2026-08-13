"""Generación de explicaciones y fixes para Findings usando un LLM local vía Ollama."""

import re

import ollama

from src.ai.prompts import build_explanation_prompt
from src.scanner.models import ExplainedFinding, Finding

MODEL = "qwen2.5-coder:7b"

# Reconoce el marcador FIX_MARKER ("---FIX---") aunque venga precedido de
# numeración de lista ("1. ", "2) ", "- ") o rodeado de espacios/asteriscos,
# variaciones habituales en la salida de modelos locales pequeños.
_FIX_MARKER_RE = re.compile(
    r"^[ \t]*(?:[-*\d]+[.)]?\s+)?\**\s*-{2,}\s*FIX\s*-{2,}\s*\**[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

# Bloque de código Markdown delimitado por ``` ... ```.
_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)


def _split_before_last_code_block(content: str) -> tuple[str, str] | None:
    """Heurística de respaldo: separa el texto usando el último bloque de código Markdown.

    Se usa cuando el modelo no reprodujo el marcador FIX_MARKER en absoluto:
    localiza el último bloque ``` ``` del contenido y considera que el fix
    empieza en la frase (o párrafo) que lo introduce, dejando todo lo anterior
    como explicación. Devuelve None si no hay ningún bloque de código o si la
    heurística no produce una división útil.
    """
    code_blocks = list(_CODE_BLOCK_RE.finditer(content))
    if not code_blocks:
        return None

    preceding_text = content[: code_blocks[-1].start()]

    paragraph_breaks = list(re.finditer(r"\n\s*\n", preceding_text))
    if paragraph_breaks:
        split_point = paragraph_breaks[-1].end()
    else:
        sentence_breaks = list(re.finditer(r"[.!?]\s+", preceding_text))
        split_point = sentence_breaks[-1].end() if sentence_breaks else 0

    explanation = content[:split_point].strip()
    suggested_fix = content[split_point:].strip()
    if not explanation or not suggested_fix:
        return None
    return explanation, suggested_fix


def _split_explanation_and_fix(content: str, finding: Finding) -> tuple[str, str]:
    """Separa la respuesta del LLM en (explicación, fix sugerido) de forma tolerante al formato.

    Los modelos locales pequeños no siempre reproducen el marcador FIX_MARKER
    tal cual se pide en el prompt (le añaden numeración, asteriscos, etc.), así
    que primero se intenta con una regex tolerante y, si falla, con una
    heurística de respaldo basada en el último bloque de código Markdown.
    """
    parts = _FIX_MARKER_RE.split(content, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    fallback = _split_before_last_code_block(content)
    if fallback is not None:
        return fallback

    print(
        f"[explainer] No se pudo separar explicación y fix para "
        f"{finding.rule_id} en {finding.file_path}:{finding.line}"
    )
    return content.strip(), ""


def explain_finding(finding: Finding) -> ExplainedFinding:
    """Pide al LLM una explicación y un fix para un Finding y devuelve un ExplainedFinding."""
    prompt = build_explanation_prompt(finding)
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response["message"]["content"]

    explanation, suggested_fix = _split_explanation_and_fix(content, finding)

    return ExplainedFinding(
        finding=finding,
        explanation=explanation,
        suggested_fix=suggested_fix,
    )


def explain_findings(findings: list[Finding]) -> list[ExplainedFinding]:
    """Aplica explain_finding a cada Finding de la lista."""
    return [explain_finding(finding) for finding in findings]
