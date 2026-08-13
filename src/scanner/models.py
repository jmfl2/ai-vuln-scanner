"""Modelos de datos para la capa de escaneo."""

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    """Nivel de severidad de un hallazgo."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Finding(BaseModel):
    """Representa un hallazgo individual reportado por Semgrep."""

    file_path: str
    line: int
    rule_id: str
    severity: Severity
    message: str
    code_snippet: str
