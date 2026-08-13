"""Punto de entrada de línea de comandos del escáner de vulnerabilidades."""

import click

from src.ai.explainer import explain_findings
from src.report import generate_html_report, generate_markdown_report, save_report
from src.scanner.models import ExplainedFinding, Finding, Severity
from src.scanner.semgrep_runner import run_semgrep

_SEVERITY_COLORS: dict[Severity, str] = {
    Severity.LOW: "green",
    Severity.MEDIUM: "yellow",
    Severity.HIGH: "red",
    Severity.CRITICAL: "red",
}

# Rango numérico de cada severidad según el orden ya definido por la propia
# declaración del enum Severity (LOW < MEDIUM < HIGH < CRITICAL).
_SEVERITY_RANK: dict[Severity, int] = {
    severity: rank for rank, severity in enumerate(Severity)
}


def _filter_by_min_severity(
    findings: list[Finding], min_severity: Severity
) -> list[Finding]:
    """Filtra findings, conservando solo los de severidad igual o superior a min_severity."""
    return [
        finding
        for finding in findings
        if _SEVERITY_RANK[finding.severity] >= _SEVERITY_RANK[min_severity]
    ]


def _print_finding(finding: Finding, explanation: str | None) -> None:
    """Imprime un único finding formateado, con color según su severidad."""
    color = _SEVERITY_COLORS[finding.severity]
    click.secho(f"[{finding.severity.value}] {finding.rule_id}", fg=color, bold=True)
    click.echo(f"  {finding.file_path}:{finding.line}")
    click.echo(f"  {finding.message}")
    if explanation:
        click.echo(f"  Explicación IA: {explanation}")
    click.echo()


def _generate_report(
    explained_findings: list[ExplainedFinding], target_path: str, output: str
) -> tuple[str, str]:
    """Genera el contenido del informe según la extensión de output.

    Usa generate_html_report si output termina en ".html"; en cualquier otro
    caso (incluido ".md") usa generate_markdown_report. Devuelve una tupla
    (contenido, nombre del formato) para poder informar al usuario.
    """
    if output.lower().endswith(".html"):
        return generate_html_report(explained_findings, target_path), "HTML"
    return generate_markdown_report(explained_findings, target_path), "Markdown"


def _print_summary(findings: list[Finding]) -> None:
    """Imprime el resumen final: total de findings y desglose por severidad."""
    click.secho(f"Total de hallazgos: {len(findings)}", bold=True)
    for severity in Severity:
        count = sum(1 for f in findings if f.severity == severity)
        if count:
            click.secho(
                f"  {severity.value}: {count}", fg=_SEVERITY_COLORS[severity]
            )


@click.command()
@click.argument("target_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--skip-ai",
    is_flag=True,
    default=False,
    help="Omite la capa de IA y solo ejecuta el scanner (útil para pruebas rápidas).",
)
@click.option(
    "--min-severity",
    type=click.Choice([severity.value for severity in Severity], case_sensitive=False),
    default=Severity.LOW.value,
    help="Severidad mínima a incluir (LOW, MEDIUM, HIGH o CRITICAL). Por defecto LOW, que no filtra nada.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False),
    default=None,
    help=(
        "Ruta donde guardar el informe (si no se indica, no se genera informe). "
        "El formato se decide por la extensión: '.html' genera HTML, "
        "cualquier otra (incl. '.md') genera Markdown."
    ),
)
def main(
    target_path: str, skip_ai: bool, min_severity: str, output: str | None
) -> None:
    """Escanea TARGET_PATH en busca de vulnerabilidades con Semgrep y, opcionalmente, las explica con IA."""
    findings = run_semgrep(target_path)
    findings = _filter_by_min_severity(findings, Severity(min_severity.upper()))

    if not findings:
        click.secho("No se encontraron problemas.", fg="green", bold=True)

    if skip_ai:
        explained_findings: list[ExplainedFinding] = [
            ExplainedFinding(finding=finding, explanation="", suggested_fix="")
            for finding in findings
        ]
        for finding in findings:
            _print_finding(finding, explanation=None)
    else:
        explained_findings = explain_findings(findings)
        for explained in explained_findings:
            _print_finding(explained.finding, explanation=explained.explanation)

    if findings:
        _print_summary(findings)

    if output:
        report, report_format = _generate_report(explained_findings, target_path, output)
        save_report(report, output)
        click.secho(
            f"Informe ({report_format}) guardado en: {output}", fg="cyan", bold=True
        )


if __name__ == "__main__":
    main()
