"""Ejecución de Semgrep y parseo de sus resultados a objetos Finding."""

import json
import subprocess

from src.scanner.models import Finding, Severity

# Mapea la severidad nativa de Semgrep (INFO/WARNING/ERROR/CRITICAL) a nuestro enum.
_SEVERITY_MAP: dict[str, Severity] = {
    "INFO": Severity.LOW,
    "WARNING": Severity.MEDIUM,
    "ERROR": Severity.HIGH,
    "CRITICAL": Severity.CRITICAL,
}


def _parse_result(result: dict) -> Finding:
    """Convierte un elemento de result["results"] del JSON de Semgrep en un Finding."""
    extra = result.get("extra", {})
    raw_severity = extra.get("severity", "INFO")
    lines = extra.get("lines", "")

    return Finding(
        file_path=result.get("path", ""),
        line=result.get("start", {}).get("line", 0),
        rule_id=result.get("check_id", ""),
        severity=_SEVERITY_MAP.get(raw_severity, Severity.LOW),
        message=extra.get("message", ""),
        code_snippet=lines,
    )


def run_semgrep(target_path: str) -> list[Finding]:
    """Ejecuta `semgrep --config=auto --json` sobre target_path y devuelve sus Findings.

    Lanza FileNotFoundError si el binario de semgrep no está instalado, y
    RuntimeError si semgrep falla o su salida no puede interpretarse como JSON válido.
    """
    try:
        process = subprocess.run(
            ["semgrep", "--config=auto", "--json", target_path],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "El binario 'semgrep' no está instalado o no está en el PATH."
        ) from exc

    if not process.stdout.strip():
        raise RuntimeError(
            f"Semgrep no produjo salida. stderr: {process.stderr.strip()}"
        )

    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"No se pudo parsear la salida JSON de Semgrep: {exc}"
        ) from exc

    return [_parse_result(result) for result in payload.get("results", [])]
