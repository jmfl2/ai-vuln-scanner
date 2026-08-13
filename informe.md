# Informe de Seguridad

**Ruta escaneada:** `examples/vulnerable_app`

## Resumen

**Total de hallazgos:** 2

- 🔴 **HIGH:** 1
- 🟡 **MEDIUM:** 1

## Hallazgos

## 🔴 python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query

**Archivo:** `examples/vulnerable_app/app.py:7`

**Mensaje:** Avoiding SQL string concatenation: untrusted input concatenated with raw SQL query can result in SQL Injection. In order to execute raw query safely, prepared statement should be used. SQLAlchemy provides TextualSQL to easily used prepared statement with named parameters. For complex SQL composition, use SQL Expression Language or Schema Definition Language. In most cases, SQLAlchemy ORM will be a better option.

**Explicación IA:**

1. Este hallazgo representa un riesgo de seguridad porque la concatenación directa de cadenas SQL no solo puede hacer que el código sea difícil de mantener y entender, sino que también facilita las inyecciones SQL si algún dato de entrada no se ha validado adecuadamente. Las inyecciones SQL ocurren cuando un atacante puede alterar la estructura de la consulta SQL enviada al servidor, lo cual puede llevar a pérdida de datos, revelación de información sensible o incluso el control total sobre la base de datos.

**Fix sugerido:**

```
Para mitigar este riesgo, se recomienda usar consultas preparadas (prepared statements). SQLAlchemy proporciona una funcionalidad llamada `TextualSQL` que facilita el uso de consultas preparadas con parámetros nombrados. Aquí tienes un ejemplo de cómo podrías corregir el código:

```python
from sqlalchemy import text

# Código original incorrecto (potencialmente vulnerable a inyecciones SQL)
sql = "SELECT * FROM users WHERE username = '" + username + "'"
result = engine.execute(sql)

# Código corregido usando consultas preparadas
sql_query = text("SELECT * FROM users WHERE username = :username")
result = engine.execute(sql_query, username=username)
```

En este ejemplo, `:username` es un parámetro nombrado en la consulta SQL. Cuando ejecutes esta consulta con el método `execute`, SQLAlchemy se encargará de escapar cualquier carácter especial en el valor del parámetro `username`, lo que prevenirá las inyecciones SQL.
```

## 🟡 python.lang.security.audit.eval-detected.eval-detected

**Archivo:** `examples/vulnerable_app/app.py:13`

**Mensaje:** Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.

**Explicación IA:**

1. El hallazgo representa un riesgo de seguridad porque `eval()` ejecuta dinámicamente cualquier expresión pasada como una cadena de texto. Si esta cadena proviene de una fuente externa (como una entrada del usuario), podría ser utilizada para ejecutar código perjudicial o inesperado, lo que conduce a vulnerabilidades de inyección de código.

2.
---

Para corregir este problema, se debe evitar el uso de `eval()`. En su lugar, se pueden usar métodos más seguros como `ast.literal_eval()` para evaluar solo expresiones literales seguras. Aquí hay un ejemplo de cómo podrías hacerlo:

**Fix sugerido:**

```
```python
import ast

# Supongamos que tienes una entrada del usuario que contiene una expresión a evaluar
user_input = "{'key': 'value'}"

try:
    # Usando ast.literal_eval para evaluar la expresión de forma segura
    safe_result = ast.literal_eval(user_input)
    print(safe_result)
except (ValueError, SyntaxError):
    print("La entrada no es una expresión literal segura.")
```

Este enfoque garantiza que solo se evalúen valores literales y no código arbitrario.
```
