"""Tests para el parseo de respuestas del LLM en src/ai/explainer.py."""

from src.ai.explainer import _split_explanation_and_fix
from src.scanner.models import Finding, Severity


def _build_finding(**overrides) -> Finding:
    """Construye un Finding mínimo de ejemplo para pasar como segundo argumento."""
    data = {
        "file_path": "src/app.py",
        "line": 42,
        "rule_id": "python.lang.security.audit.dangerous-eval",
        "severity": Severity.HIGH,
        "message": "Uso de eval() con entrada no confiable.",
        "code_snippet": "eval(user_input)",
    }
    data.update(overrides)
    return Finding(**data)


def test_marcador_fix_exacto_separa_explicacion_y_fix():
    """Verifica que una respuesta con el marcador "---FIX---" exacto se separa
    correctamente en explicación y fix sugerido."""
    content = (
        "Esta es la explicación del problema.\n"
        "---FIX---\n"
        "Este es el fix sugerido."
    )

    explanation, suggested_fix = _split_explanation_and_fix(content, _build_finding())

    assert explanation == "Esta es la explicación del problema."
    assert suggested_fix == "Este es el fix sugerido."


def test_marcador_fix_con_numeracion_de_lista_tambien_se_separa_correctamente():
    """Verifica que una respuesta donde el marcador viene precedido de numeración
    de lista (ej. "2. ---FIX---") también se separa correctamente: es el caso
    real que se vio fallar en desarrollo antes de mejorar la regex."""
    content = (
        "1. Explicación del problema detectado en el código.\n"
        "2. ---FIX---\n"
        "Cambia eval() por ast.literal_eval()."
    )

    explanation, suggested_fix = _split_explanation_and_fix(content, _build_finding())

    assert explanation == "1. Explicación del problema detectado en el código."
    assert suggested_fix == "Cambia eval() por ast.literal_eval()."


def test_sin_marcador_pero_con_bloque_de_codigo_usa_heuristica_de_respaldo():
    """Verifica que, sin el marcador FIX_MARKER pero con un bloque de código
    Markdown, se usa la heurística de respaldo y se separa antes del bloque."""
    content = (
        "Aquí tienes la explicación del problema con eval().\n\n"
        "```python\n"
        "safe_value = ast.literal_eval(user_input)\n"
        "```"
    )

    explanation, suggested_fix = _split_explanation_and_fix(content, _build_finding())

    assert explanation == "Aquí tienes la explicación del problema con eval()."
    assert suggested_fix.startswith("```python")
    assert "ast.literal_eval(user_input)" in suggested_fix


def test_sin_marcador_ni_bloque_de_codigo_todo_cae_en_explicacion_y_avisa(capsys):
    """Verifica que, sin marcador y sin bloque de código, no hay forma de separar
    la respuesta: todo el contenido cae en "explicación", el fix queda como
    cadena vacía, y se imprime el aviso esperado (comprobado con capsys)."""
    content = "Esta respuesta no tiene marcador ni bloques de código, solo texto plano."
    finding = _build_finding()

    explanation, suggested_fix = _split_explanation_and_fix(content, finding)

    assert explanation == content
    assert suggested_fix == ""

    captured = capsys.readouterr()
    assert (
        "[explainer] No se pudo separar explicación y fix para "
        f"{finding.rule_id} en {finding.file_path}:{finding.line}"
    ) in captured.out
