"""Generación de informes (Markdown y HTML) a partir de hallazgos explicados por IA."""

import html

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

# Clase CSS por severidad: CRITICAL/HIGH comparten el color rojo, MEDIUM
# amarillo y LOW verde (ver reglas .sev-* en _HTML_STYLE).
_SEVERITY_CSS_CLASS: dict[Severity, str] = {
    Severity.CRITICAL: "sev-critical",
    Severity.HIGH: "sev-high",
    Severity.MEDIUM: "sev-medium",
    Severity.LOW: "sev-low",
}


def _sorted_by_severity(
    explained_findings: list[ExplainedFinding],
) -> list[ExplainedFinding]:
    """Ordena los hallazgos por severidad (CRITICAL y HIGH primero, LOW al final)."""
    return sorted(
        explained_findings,
        key=lambda ef: _SEVERITY_ORDER.index(ef.finding.severity),
    )


def _counts_by_severity(
    explained_findings: list[ExplainedFinding],
) -> list[tuple[Severity, int]]:
    """Cuenta los hallazgos por severidad, en el orden de _SEVERITY_ORDER, omitiendo las que no tienen hallazgos."""
    counts = []
    for severity in _SEVERITY_ORDER:
        count = sum(1 for ef in explained_findings if ef.finding.severity == severity)
        if count:
            counts.append((severity, count))
    return counts


def _build_summary(explained_findings: list[ExplainedFinding]) -> str:
    """Construye el bloque de resumen: total de hallazgos y desglose por severidad."""
    lines = [f"**Total de hallazgos:** {len(explained_findings)}", ""]
    for severity, count in _counts_by_severity(explained_findings):
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
    sorted_findings = _sorted_by_severity(explained_findings)

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


_HTML_STYLE = """
    :root {
        --bg: #0a0e14;
        --surface: #10161f;
        --surface-raised: #161d29;
        --border: #232c3a;
        --border-strong: #2f3a4a;
        --text: #e8edf4;
        --text-muted: #7c8899;
        --text-faint: #4d5666;

        --accent: #4dd8c0;
        --accent-soft: rgba(77, 216, 192, 0.12);

        --red: #f2545b;
        --red-soft: rgba(242, 84, 91, 0.12);
        --amber: #e3a008;
        --amber-soft: rgba(227, 160, 8, 0.12);
        --green: #3ecf8e;
        --green-soft: rgba(62, 207, 142, 0.12);

        --font-mono: ui-monospace, "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
        --font-sans: -apple-system, "Segoe UI", Inter, Roboto, Helvetica, Arial, sans-serif;
    }

    * { box-sizing: border-box; }

    @media (prefers-reduced-motion: reduce) {
        * { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
    }

    body {
        margin: 0;
        padding: 0 1.5rem 4rem;
        background: var(--bg);
        color: var(--text);
        font-family: var(--font-sans);
        line-height: 1.6;
        font-size: 15px;
    }

    main {
        max-width: 880px;
        margin: 0 auto;
    }

    /* ---------- Cabecera ---------- */

    .report-header {
        position: relative;
        overflow: hidden;
        margin: 0 -1.5rem 2.5rem;
        padding: 3rem 1.5rem 2.25rem;
        border-bottom: 1px solid var(--border);
        background-image: radial-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px);
        background-size: 22px 22px;
    }

    .scan-beam {
        position: absolute;
        left: 0;
        right: 0;
        top: -10%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        opacity: 0;
        animation: scan-sweep 1.6s cubic-bezier(.4, 0, .2, 1) 0.15s 1 both;
    }

    @keyframes scan-sweep {
        0%   { top: -5%;   opacity: 0; }
        12%  { opacity: 1; }
        88%  { opacity: 1; }
        100% { top: 100%;  opacity: 0; }
    }

    .eyebrow {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        color: var(--accent);
        margin: 0 0 0.75rem 0;
    }

    h1 {
        margin: 0 0 0.9rem 0;
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        max-width: 620px;
        position: relative;
        z-index: 1;
    }

    .target-path {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        color: var(--text-muted);
        margin: 0;
        position: relative;
        z-index: 1;
        word-break: break-all;
    }

    .target-path .prompt {
        color: var(--accent);
        margin-right: 0.5em;
    }

    .target-path code {
        color: var(--text);
    }

    /* ---------- Barra de estadísticas ---------- */

    h2 {
        font-family: var(--font-mono);
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-faint);
        margin: 0 0 1rem 0;
    }

    .stat-bar {
        display: flex;
        flex-wrap: wrap;
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 2.5rem;
    }

    .stat-block {
        flex: 1 1 120px;
        padding: 1.1rem 1.3rem;
        border-right: 1px solid var(--border);
        background: var(--surface);
    }

    .stat-block:last-child { border-right: none; }

    .stat-number {
        display: block;
        font-family: var(--font-mono);
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.1;
    }

    .stat-label {
        display: block;
        margin-top: 0.3rem;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
    }

    .stat-block.sev-critical .stat-number,
    .stat-block.sev-high .stat-number { color: var(--red); }
    .stat-block.sev-medium .stat-number { color: var(--amber); }
    .stat-block.sev-low .stat-number { color: var(--green); }

    /* ---------- Tarjetas de hallazgos ---------- */

    .findings {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .finding-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--border-strong);
        border-radius: 8px;
        padding: 1.3rem 1.5rem;
    }

    .finding-card.sev-critical,
    .finding-card.sev-high { border-left-color: var(--red); }
    .finding-card.sev-medium { border-left-color: var(--amber); }
    .finding-card.sev-low { border-left-color: var(--green); }

    .finding-top {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 0.6rem;
    }

    .badge {
        display: inline-block;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.2rem 0.55rem;
        border-radius: 5px;
    }

    .sev-critical .badge, .sev-high .badge {
        background: var(--red-soft); color: var(--red);
    }
    .sev-medium .badge { background: var(--amber-soft); color: var(--amber); }
    .sev-low .badge { background: var(--green-soft); color: var(--green); }

    .finding-location {
        font-family: var(--font-mono);
        font-size: 0.78rem;
        color: var(--text-faint);
    }

    .finding-card h3 {
        margin: 0 0 0.7rem 0;
        font-family: var(--font-mono);
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text);
        word-break: break-word;
    }

    .finding-message {
        margin: 0;
        color: var(--text-muted);
    }

    .finding-block {
        margin-top: 1.1rem;
        padding-top: 1.1rem;
        border-top: 1px solid var(--border);
    }

    .block-label {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent);
        margin-bottom: 0.5rem;
    }

    .explanation-block {
        white-space: pre-wrap;
        color: var(--text);
    }

    .fix-block pre {
        background: #05070a;
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 0.9rem 1rem;
        overflow-x: auto;
        margin: 0;
    }

    .fix-block code {
        font-family: var(--font-mono);
        font-size: 0.82rem;
        color: #d1f7ec;
        white-space: pre;
    }
""".strip()


def _build_html_summary(explained_findings: list[ExplainedFinding]) -> str:
    """Construye la barra de estadísticas: total + un bloque por severidad presente."""
    blocks = [
        f"""<div class="stat-block">
            <span class="stat-number">{len(explained_findings)}</span>
            <span class="stat-label">Total</span>
        </div>"""
    ]
    for severity, count in _counts_by_severity(explained_findings):
        css_class = _SEVERITY_CSS_CLASS[severity]
        blocks.append(
            f"""<div class="stat-block {css_class}">
            <span class="stat-number">{count}</span>
            <span class="stat-label">{html.escape(severity.value)}</span>
        </div>"""
        )
    return '<div class="stat-bar">\n' + "\n".join(blocks) + "\n</div>"


def _build_html_finding_card(explained_finding: ExplainedFinding) -> str:
    """Construye la tarjeta HTML correspondiente a un único hallazgo explicado."""
    finding = explained_finding.finding
    css_class = _SEVERITY_CSS_CLASS[finding.severity]

    parts = [
        f'<article class="finding-card {css_class}">',
        '<div class="finding-top">',
        f'<span class="badge">{html.escape(finding.severity.value)}</span>',
        f'<span class="finding-location">{html.escape(finding.file_path)}:{finding.line}</span>',
        "</div>",
        f"<h3>{html.escape(finding.rule_id)}</h3>",
        f'<p class="finding-message">{html.escape(finding.message)}</p>',
    ]

    if explained_finding.explanation:
        parts.append(
            '<div class="finding-block">'
            '<div class="block-label">Análisis IA</div>'
            f'<div class="explanation-block">{html.escape(explained_finding.explanation)}</div>'
            "</div>"
        )

    if explained_finding.suggested_fix:
        parts.append(
            '<div class="finding-block fix-block">'
            '<div class="block-label">Fix sugerido</div>'
            f"<pre><code>{html.escape(explained_finding.suggested_fix)}</code></pre>"
            "</div>"
        )

    parts.append("</article>")
    return "\n".join(parts)


def generate_html_report(
    explained_findings: list[ExplainedFinding],
    target_path: str,
) -> str:
    """Genera un informe HTML autocontenido con estética de consola de seguridad
    (tema oscuro, tipografía monoespaciada para datos, barrido de escaneo animado
    una sola vez en la cabecera, respetando prefers-reduced-motion).
    """
    sorted_findings = _sorted_by_severity(explained_findings)

    if sorted_findings:
        findings_html = (
            '<h2>Hallazgos</h2>\n<div class="findings">\n'
            + "\n".join(_build_html_finding_card(ef) for ef in sorted_findings)
            + "\n</div>"
        )
    else:
        findings_html = ""

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Informe de Seguridad</title>
<style>
{_HTML_STYLE}
</style>
</head>
<body>
<main>
<header class="report-header">
<div class="scan-beam"></div>
<div class="eyebrow">Security Scan Report</div>
<h1>Informe de Seguridad</h1>
<p class="target-path"><span class="prompt">$</span> scan <code>{html.escape(target_path)}</code></p>
</header>
<h2>Resumen</h2>
{_build_html_summary(explained_findings)}
{findings_html}
</main>
</body>
</html>
"""


def save_report(content: str, output_path: str) -> None:
    """Guarda el contenido del informe en un archivo de texto."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
