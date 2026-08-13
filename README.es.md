<div align="center">

# ai-vuln-scanner

**Escáner de vulnerabilidades para código Python que combina el análisis estático de Semgrep con explicaciones de IA locales y privadas, para que los hallazgos sean fáciles de entender y de arreglar.**

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Estado: en desarrollo](https://img.shields.io/badge/status-en%20desarrollo-yellow)
![Tests: pytest](https://img.shields.io/badge/tests-pytest-0A9EDC)
![IA: local vía Ollama](https://img.shields.io/badge/IA-local%20v%C3%ADa%20Ollama-4dd8c0)

🇬🇧 [English](README.md)&nbsp;&nbsp;·&nbsp;&nbsp;🇪🇸 Español

</div>

---

## Índice

- [¿Por qué?](#por-qué)
- [Características](#características)
- [Instalación](#instalación)
- [Uso](#uso)
  - [Opciones de la CLI](#opciones-de-la-cli)
  - [Ejemplos](#ejemplos)
- [Tests](#tests)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Stack tecnológico](#stack-tecnológico)
- [Roadmap](#roadmap)

## ¿Por qué?

Los escáneres estáticos como Semgrep son muy buenos detectando patrones inseguros, pero sus resultados suelen ser mensajes técnicos (nombres de reglas, jerga de seguridad) que un desarrollador junior no siempre sabe interpretar ni traducir en una solución concreta. `ai-vuln-scanner` toma esos hallazgos y les añade una explicación en lenguaje natural y un fix de ejemplo, generados por un modelo de IA que corre **localmente y de forma gratuita** con [Ollama](https://ollama.com), sin depender de una API de pago ni enviar código a terceros.

## Características

- **Escaneo estático con Semgrep**, usando su set de reglas automático (`--config=auto`), con soporte para múltiples lenguajes.
- **Explicaciones y fixes generados por IA local** vía Ollama (`qwen2.5-coder:7b`), sin API keys ni servicios externos.
- **Filtrado por severidad** con `--min-severity` (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`), para centrarte en lo que importa.
- **Salida en terminal coloreada por severidad** (rojo para CRITICAL/HIGH, amarillo para MEDIUM, verde para LOW).
- **Informes en Markdown o HTML** — el informe HTML es totalmente autocontenido (CSS embebido, tema oscuro tipo "consola de seguridad", sin dependencias externas) — el formato se elige automáticamente según la extensión de `--output`.
- **Parseo robusto de la respuesta del LLM**: una expresión regular tolerante a variaciones de formato más una heurística de respaldo basada en bloques de código Markdown, para que la separación explicación/fix siga funcionando aunque el modelo no siga el formato pedido al pie de la letra.
- **Modo `--skip-ai`** para ejecutar solo el escáner, útil para iteración rápida o checks estilo CI.

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd ai-vuln-scanner

# 2. Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar las dependencias de Python
pip install -r requirements.txt

# 4. Instalar Semgrep (incluido en requirements.txt, pero puede instalarse aparte)
pip install semgrep

# 5. Instalar Ollama
# Ver https://ollama.com/download para instrucciones según tu sistema operativo

# 6. Arrancar el servicio de Ollama (si no arranca automáticamente)
ollama serve

# 7. Descargar el modelo usado para las explicaciones
ollama pull qwen2.5-coder:7b

# 8. Instalar el proyecto en modo desarrollo
#    (necesario para que `import src...` funcione correctamente, p. ej. al correr los tests)
pip install -e .
```

## Uso

```bash
python3 -m src.cli RUTA_A_ESCANEAR [OPCIONES]
```

### Opciones de la CLI

| Opción | Descripción | Por defecto |
| --- | --- | --- |
| `--skip-ai` | Omite la capa de IA y solo ejecuta el escáner. | desactivado |
| `--min-severity [low\|medium\|high\|critical]` | Severidad mínima a incluir (no distingue mayúsculas/minúsculas). Los hallazgos por debajo de ese nivel se filtran **antes** de pasar por la IA o de imprimirse. | `low` (no filtra nada) |
| `--output RUTA` | Guarda el informe en `RUTA`. El formato se decide por la extensión: `.html` → informe HTML autocontenido, cualquier otra (incl. `.md`) → Markdown. | ninguno (no se genera informe) |

### Ejemplos

```bash
# Escaneo completo, con explicaciones y fixes generados por IA
python3 -m src.cli <ruta>

# Escaneo rápido, solo Semgrep, sin IA
python3 -m src.cli <ruta> --skip-ai

# Mostrar solo hallazgos HIGH y CRITICAL
python3 -m src.cli <ruta> --min-severity high

# Generar un informe en Markdown
python3 -m src.cli <ruta> --output informe.md

# Generar un informe HTML autocontenido
python3 -m src.cli <ruta> --output informe.html

# Combinar opciones: escaneo rápido solo de CRITICAL, exportado a HTML
python3 -m src.cli <ruta> --skip-ai --min-severity critical --output informe.html
```

Puedes probarlo directamente contra la app de ejemplo incluida en el repo:

```bash
python3 -m src.cli examples/vulnerable_app
```

## Tests

El proyecto usa `pytest`. Los tests ejercitan la lógica de parseo (parseo de resultados de Semgrep, separación de respuestas del LLM) con datos de ejemplo en memoria — no requieren tener Semgrep ni Ollama corriendo.

```bash
# Requiere instalación en modo desarrollo (ver Instalación, paso 8)
pytest
```

## Arquitectura

El proyecto está organizado en capas con responsabilidades separadas:

```
Scanner (Semgrep)  →  Modelos de datos (Pydantic)  →  Capa de IA (Ollama)  →  CLI (Click)  →  Generador de informes (Markdown / HTML)
```

- **`src/scanner/semgrep_runner.py`** — ejecuta Semgrep sobre la ruta indicada y parsea su salida JSON a objetos `Finding`.
- **`src/scanner/models.py`** — modelos Pydantic (`Finding`, `ExplainedFinding`, `Severity`) que dan forma y validación a los datos que circulan entre capas.
- **`src/ai/`** — construcción del prompt (`prompts.py`) y llamada al modelo local vía Ollama, con parseo tolerante de la respuesta (`explainer.py`).
- **`src/cli.py`** — punto de entrada de línea de comandos (Click); orquesta el escaneo, el filtrado por severidad, la explicación por IA y la impresión de resultados.
- **`src/report.py`** — genera el informe en Markdown o HTML a partir de los hallazgos explicados; la lógica de ordenamiento y conteo por severidad se comparte entre ambos formatos.

## Estructura del proyecto

```
ai-vuln-scanner/
├── examples/
│   └── vulnerable_app/       # app de ejemplo con vulnerabilidades intencionadas, para demos
├── src/
│   ├── ai/
│   │   ├── explainer.py      # llamada a Ollama + parseo tolerante de la respuesta
│   │   └── prompts.py        # construcción del prompt
│   ├── scanner/
│   │   ├── models.py         # Finding, ExplainedFinding, Severity
│   │   └── semgrep_runner.py # ejecuta Semgrep, parsea su salida JSON
│   ├── cli.py                # punto de entrada de la CLI (Click)
│   └── report.py             # generación de informes Markdown / HTML
├── tests/
│   ├── test_explainer.py
│   └── test_scanner.py
├── pyproject.toml
└── requirements.txt
```

## Limitaciones conocidas

- No está diseñado para detectar secretos hardcodeados (API keys, contraseñas) de forma fiable; depende enteramente de las reglas de Semgrep para ese tipo de hallazgo.
- El procesamiento de los hallazgos por parte de la IA es **secuencial**, no paralelo, por lo que escanear un proyecto con muchos findings puede tardar.
- Las explicaciones generadas por IA están pensadas y probadas principalmente para **código Python y en español**; en otros lenguajes la calidad puede variar.
- Requiere tener **Ollama corriendo localmente** con el modelo descargado; sin él, la capa de IA no funciona (aunque el modo `--skip-ai` sigue disponible).

## Stack tecnológico

- **Python** — lenguaje del proyecto.
- **Semgrep** — motor de análisis estático.
- **Ollama** — ejecución local del modelo de IA (`qwen2.5-coder:7b`).
- **Pydantic** — validación y modelado de datos.
- **Click** — construcción de la interfaz de línea de comandos.
- **pytest** — tests unitarios del parseo de Semgrep, del parseo de respuestas del LLM y de la generación de informes.

## Roadmap

- Modo `--fix` que aplique automáticamente los fixes sugeridos sobre el código.
- Soporte configurable para usar la API de Claude como alternativa a Ollama.
- Nuevos formatos de informe, como JSON.
