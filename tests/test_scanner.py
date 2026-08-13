"""Tests para el parseo de resultados de Semgrep en src/scanner/semgrep_runner.py."""

from src.scanner.models import Severity
from src.scanner.semgrep_runner import _parse_result


def _build_semgrep_result(**overrides) -> dict:
    """Construye un dict con la forma típica de un elemento result["results"] de Semgrep."""
    result = {
        "check_id": "python.lang.security.audit.dangerous-eval",
        "path": "src/app.py",
        "start": {"line": 42},
        "extra": {
            "severity": "ERROR",
            "message": "Uso de eval() con entrada no confiable.",
            "lines": "eval(user_input)",
        },
    }
    result.update(overrides)
    return result


def test_severidad_error_se_mapea_a_high_y_todos_los_campos_se_extraen():
    """Verifica que un resultado con severidad ERROR se mapea a Severity.HIGH y que
    file_path, line, rule_id, message y code_snippet se extraen correctamente."""
    raw_result = _build_semgrep_result()

    finding = _parse_result(raw_result)

    assert finding.severity == Severity.HIGH
    assert finding.file_path == "src/app.py"
    assert finding.line == 42
    assert finding.rule_id == "python.lang.security.audit.dangerous-eval"
    assert finding.message == "Uso de eval() con entrada no confiable."
    assert finding.code_snippet == "eval(user_input)"


def test_severidad_info_se_mapea_a_low():
    """Verifica que un resultado con severidad INFO se mapea a Severity.LOW."""
    raw_result = _build_semgrep_result(extra={"severity": "INFO", "message": "Nota informativa.", "lines": "x = 1"})

    finding = _parse_result(raw_result)

    assert finding.severity == Severity.LOW


def test_severidad_critical_se_mapea_a_critical():
    """Verifica que un resultado con severidad CRITICAL se mapea a Severity.CRITICAL."""
    raw_result = _build_semgrep_result(
        extra={"severity": "CRITICAL", "message": "Vulnerabilidad crítica.", "lines": "os.system(cmd)"}
    )

    finding = _parse_result(raw_result)

    assert finding.severity == Severity.CRITICAL


def test_severidad_desconocida_usa_low_por_defecto_sin_lanzar_error():
    """Verifica que una severidad no reconocida por _SEVERITY_MAP no lanza excepción
    y se resuelve al valor por defecto Severity.LOW."""
    raw_result = _build_semgrep_result(extra={"severity": "UNKNOWN_LEVEL", "message": "??", "lines": "??"})

    finding = _parse_result(raw_result)

    assert finding.severity == Severity.LOW


def test_campos_faltantes_no_rompen_el_parseo_y_usan_valores_por_defecto():
    """Verifica que un resultado sin la clave 'extra' (ni otras claves opcionales) no
    lanza excepción y produce un Finding con valores por defecto razonables."""
    raw_result = {"check_id": "some.rule.id", "path": "src/legacy.py", "start": {"line": 7}}

    finding = _parse_result(raw_result)

    assert finding.file_path == "src/legacy.py"
    assert finding.line == 7
    assert finding.rule_id == "some.rule.id"
    assert finding.severity == Severity.LOW
    assert finding.message == ""
    assert finding.code_snippet == ""


def test_resultado_completamente_vacio_no_rompe_el_parseo():
    """Verifica que un dict vacío (sin ninguna clave) tampoco lanza excepción y
    produce un Finding con valores por defecto para todos los campos."""
    finding = _parse_result({})

    assert finding.file_path == ""
    assert finding.line == 0
    assert finding.rule_id == ""
    assert finding.severity == Severity.LOW
    assert finding.message == ""
    assert finding.code_snippet == ""
