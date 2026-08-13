# ai-vuln-scanner

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Status: en desarrollo](https://img.shields.io/badge/status-en%20desarrollo-yellow)

**Escáner de vulnerabilidades para código Python que combina Semgrep con explicaciones generadas por IA local (Ollama), para que los hallazgos sean fáciles de entender y de arreglar.**

## ¿Por qué?

Los escáneres estáticos como Semgrep son muy buenos detectando patrones inseguros, pero sus resultados suelen ser mensajes técnicos (nombres de reglas, jerga de seguridad) que un desarrollador junior no siempre sabe interpretar ni traducir en una solución concreta. `ai-vuln-scanner` toma esos hallazgos y les añade una explicación en lenguaje natural y un fix de ejemplo, generados por un modelo de IA que corre **localmente y de forma gratuita** con Ollama, sin depender de una API de pago ni enviar código a terceros.

## Características

- **Escaneo estático con Semgrep**, que soporta múltiples lenguajes a través de sus reglas (`--config=auto`).
- **Explicaciones y fixes generados por IA local** vía Ollama (modelo `qwen2.5-coder:7b`), sin necesidad de API keys ni conexión a servicios externos.
- **Salida en terminal coloreada por severidad** (rojo para CRITICAL/HIGH, amarillo para MEDIUM, verde para LOW).
- **Generación de informes en Markdown o HTML** (autocontenido, con CSS embebido y tema oscuro tipo "consola de seguridad"), con resumen por severidad y una sección/tarjeta detallada por hallazgo. El formato se elige automáticamente según la extensión de `--output` (`.html` → HTML, cualquier otra, incl. `.md` → Markdown).
- **Parseo robusto de la respuesta del LLM**: usa una expresión regular tolerante a variaciones de formato y una heurística de respaldo (basada en bloques de código Markdown) para separar explicación y fix aunque el modelo no siga el formato pedido al pie de la letra.
- **Modo `--skip-ai`** para ejecutar solo el escaneo, sin pasar por la IA, útil para pruebas rápidas.

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

# 8. Instalar el proyecto en modo desarrollo (necesario para que
#    `import src...` funcione correctamente al correr los tests)
pip install -e .
```

## Uso

```bash
# Escaneo completo, con explicaciones y fixes generados por IA
python3 -m src.cli <ruta_a_escanear>

# Escaneo rápido, solo Semgrep, sin pasar por la IA
python3 -m src.cli <ruta_a_escanear> --skip-ai

# Generar además un informe en Markdown
python3 -m src.cli <ruta_a_escanear> --output informe.md

# Generar un informe en HTML (autocontenido, listo para abrir en el navegador)
python3 -m src.cli <ruta_a_escanear> --output informe.html

# Combinar ambas opciones
python3 -m src.cli <ruta_a_escanear> --skip-ai --output informe.md
```

Puedes probarlo directamente contra la app de ejemplo incluida en el repo:

```bash
python3 -m src.cli examples/vulnerable_app
```

## Tests

El proyecto usa `pytest`. Los tests usan datos de ejemplo (dicts que simulan
resultados de Semgrep, respuestas de ejemplo de un LLM) y no requieren tener
Semgrep ni Ollama corriendo.

```bash
# Requiere haber instalado el proyecto en modo desarrollo (ver Instalación, paso 8)
pytest
```

## Arquitectura

El proyecto está organizado en capas con responsabilidades separadas:

```
Scanner (Semgrep)  →  Modelos de datos (Pydantic)  →  Capa de IA (Ollama)  →  CLI (Click)  →  Generador de informes (Markdown / HTML)
```

- **`src/scanner/semgrep_runner.py`** — ejecuta Semgrep sobre la ruta indicada y parsea su salida JSON.
- **`src/scanner/models.py`** — modelos Pydantic (`Finding`, `ExplainedFinding`, `Severity`) que dan forma y validación a los datos que circulan entre capas.
- **`src/ai/`** — construcción del prompt (`prompts.py`) y llamada al modelo local vía Ollama, con parseo de la respuesta (`explainer.py`).
- **`src/cli.py`** — punto de entrada de línea de comandos (Click), que orquesta el escaneo, la explicación por IA y la impresión de resultados.
- **`src/report.py`** — genera el informe en Markdown o HTML a partir de los hallazgos explicados (la lógica de ordenamiento y conteo por severidad se comparte entre ambos formatos).

## Limitaciones conocidas

- No está diseñado para detectar secretos hardcodeados (API keys, contraseñas) de forma fiable; depende enteramente de las reglas de Semgrep para ese tipo de hallazgo.
- El procesamiento de los hallazgos por parte de la IA es **secuencial**, no paralelo, por lo que escanear un proyecto con muchos findings puede tardar.
- Las explicaciones generadas por IA están pensadas y probadas principalmente para **código Python y en español**; en otros lenguajes o idiomas la calidad puede variar.
- Requiere tener **Ollama corriendo localmente** con el modelo descargado; sin él, la capa de IA no funciona (aunque el modo `--skip-ai` sigue disponible).

## Stack tecnológico

- **Python** — lenguaje del proyecto.
- **Semgrep** — motor de análisis estático.
- **Ollama** — ejecución local del modelo de IA (`qwen2.5-coder:7b`).
- **Pydantic** — validación y modelado de datos.
- **Click** — construcción de la interfaz de línea de comandos.
- **pytest** — tests unitarios del parseo de Semgrep, del parseo de respuestas del LLM y de la generación de informes.

## Posibles mejoras futuras

- Modo `--fix` que aplique automáticamente los fixes sugeridos sobre el código.
- Soporte configurable para usar la API de Claude como alternativa a Ollama.
- Filtrado de resultados por severidad mínima (por ejemplo, `--min-severity HIGH`).
- Exportación de informes a otros formatos, como JSON.
