"""Generación de informes en Markdown a partir de hallazgos explicados por IA."""

from src.scanner.models import ExplainedFinding, Severity

# Orden de severidad para ordenar los hallazgos (más crítico primero).
_SEVERITY_ORDER: list[Severity] = [
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
]

_SEVERITY_EMOJI: dict[Severity, str] = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🔴",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🟢",
}


def _build_summary(explained_findings: list[ExplainedFinding]) -> str:
    """Construye el bloque de resumen: total de hallazgos y desglose por severidad."""
    lines = [f"**Total de hallazgos:** {len(explained_findings)}", ""]
    for severity in _SEVERITY_ORDER:
        count = sum(
            1 for ef in explained_findings if ef.finding.severity == severity
        )
        if count:
            lines.append(f"- {_SEVERITY_EMOJI[severity]} **{severity.value}:** {count}")
    return "\n".join(lines)


def _build_finding_section(explained_finding: ExplainedFinding) -> str:
    """Construye la sección Markdown correspondiente a un único hallazgo explicado."""
    finding = explained_finding.finding
    emoji = _SEVERITY_EMOJI[finding.severity]

    lines = [
        f"## {emoji} {finding.rule_id}",
        "",
        f"**Archivo:** `{finding.file_path}:{finding.line}`",
        "",
        f"**Mensaje:** {finding.message}",
    ]

    if explained_finding.explanation:
        lines += ["", "**Explicación IA:**", "", explained_finding.explanation]

    if explained_finding.suggested_fix:
        lines += ["", "**Fix sugerido:**", "", "```", explained_finding.suggested_fix, "```"]

    return "\n".join(lines)


def generate_markdown_report(
    explained_findings: list[ExplainedFinding],
    target_path: str,
) -> str:
    """Genera un informe en Markdown a partir de una lista de ExplainedFinding.

    Los hallazgos se ordenan por severidad (CRITICAL y HIGH primero, LOW al
    final) e incluyen, si están disponibles, la explicación y el fix
    sugerido por la IA.
    """
    sorted_findings = sorted(
        explained_findings,
        key=lambda ef: _SEVERITY_ORDER.index(ef.finding.severity),
    )

    sections = [
        "# Informe de Seguridad",
        "",
        f"**Ruta escaneada:** `{target_path}`",
        "",
        "## Resumen",
        "",
        _build_summary(explained_findings),
    ]

    if sorted_findings:
        sections += ["", "## Hallazgos", ""]
        sections.append(
            "\n\n".join(_build_finding_section(ef) for ef in sorted_findings)
        )

    return "\n".join(sections) + "\n"


def save_report(content: str, output_path: str) -> None:
    """Guarda el contenido del informe en un archivo de texto."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
