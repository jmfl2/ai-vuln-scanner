"""Construcción de prompts para el LLM que explica hallazgos de seguridad."""

from src.scanner.models import Finding

FIX_MARKER = "---FIX---"


def build_explanation_prompt(finding: Finding) -> str:
    """Construye el prompt en español para pedir al LLM que explique un Finding y proponga un fix."""
    return (
        "Eres un experto en seguridad de aplicaciones. Analiza el siguiente hallazgo "
        "detectado por un analizador de código estático.\n\n"
        f"Regla: {finding.rule_id}\n"
        f"Severidad: {finding.severity.value}\n"
        f"Mensaje: {finding.message}\n"
        f"Fragmento de código:\n{finding.code_snippet}\n\n"
        "Responde en español siguiendo exactamente este formato:\n"
        "1. Primero, explica en 2-3 frases claras y concisas por qué este hallazgo "
        "representa un riesgo de seguridad.\n"
        f"2. Luego escribe el marcador '{FIX_MARKER}' en una línea aparte.\n"
        "3. Después del marcador, propón un fix concreto para el problema, incluyendo "
        "un ejemplo de código corregido.\n"
    )
