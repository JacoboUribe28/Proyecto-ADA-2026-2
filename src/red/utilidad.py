"""Funciones de utilidad u_i(x): crecientes y cóncavas sobre enteros x >= 0.

Cada utilidad expone dos operaciones:

* ``valor(x)``    -> u(x)
* ``marginal(x)`` -> u(x+1) - u(x), la ganancia de la (x+1)-ésima unidad de presupuesto.

Concavidad  <=>  ``marginal(x)`` es no creciente en x (rendimientos decrecientes).
Esa es la única propiedad que el algoritmo voraz del reparto necesita para ser óptimo.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence


class Utilidad:
    """Clase base de las utilidades cóncavas y crecientes sobre los enteros no negativos."""

    def valor(self, x: int) -> float:
        """Utilidad u(x) al asignar ``x`` unidades al nodo."""
        raise NotImplementedError

    def marginal(self, x: int) -> float:
        """Ganancia marginal u(x+1) - u(x). Las subclases la sobrescriben si hay forma cerrada."""
        return self.valor(x + 1) - self.valor(x)

    def es_concava(self, x_max: int = 200, tol: float = 1e-12) -> bool:
        """Verifica numéricamente (x = 0..x_max) que las ganancias sean >= 0 y no crecientes."""
        g = [self.marginal(x) for x in range(x_max)]
        no_crece = all(g[x + 1] <= g[x] + tol for x in range(x_max - 1))
        creciente = all(v >= -tol for v in g)
        return no_crece and creciente


class Log(Utilidad):
    """u(x) = a * ln(1 + x), con a >= 0."""

    def __init__(self, a: float) -> None:
        if a < 0:
            raise ValueError("Log: el parámetro 'a' debe ser >= 0.")
        self.a = a

    def valor(self, x: int) -> float:
        return self.a * math.log1p(x)

    def marginal(self, x: int) -> float:
        return self.a * (math.log1p(x + 1) - math.log1p(x))


class Raiz(Utilidad):
    """u(x) = a * sqrt(x), con a >= 0."""

    def __init__(self, a: float) -> None:
        if a < 0:
            raise ValueError("Raiz: el parámetro 'a' debe ser >= 0.")
        self.a = a

    def valor(self, x: int) -> float:
        return self.a * math.sqrt(x)

    def marginal(self, x: int) -> float:
        return self.a * (math.sqrt(x + 1) - math.sqrt(x))


class Saturada(Utilidad):
    """u(x) = a * (1 - exp(-b x)), con a >= 0 y b > 0 (satura en ``a``)."""

    def __init__(self, a: float, b: float) -> None:
        if a < 0 or b <= 0:
            raise ValueError("Saturada: se requiere a >= 0 y b > 0.")
        self.a, self.b = a, b

    def valor(self, x: int) -> float:
        return self.a * (1.0 - math.exp(-self.b * x))

    def marginal(self, x: int) -> float:
        return self.a * (math.exp(-self.b * x) - math.exp(-self.b * (x + 1)))


class Tabla(Utilidad):
    """Utilidad definida por sus ganancias marginales g[0] >= g[1] >= ... >= 0.

    Más allá de la tabla la ganancia es 0 (el nodo está saturado).
    """

    def __init__(self, ganancias: Sequence[float]) -> None:
        g = [float(v) for v in ganancias]
        if any(v < 0 for v in g):
            raise ValueError("Tabla: las ganancias marginales deben ser >= 0 (utilidad creciente).")
        if any(g[i + 1] > g[i] + 1e-12 for i in range(len(g) - 1)):
            raise ValueError("Tabla: las ganancias marginales deben ser no crecientes (concavidad).")
        self.g = g
        self.acum = [0.0]  # acum[x] = u(x) = suma de las x primeras ganancias
        for v in g:
            self.acum.append(self.acum[-1] + v)

    def valor(self, x: int) -> float:
        return self.acum[min(x, len(self.g))]

    def marginal(self, x: int) -> float:
        return self.g[x] if x < len(self.g) else 0.0


def desde_dict(d: Mapping[str, Any]) -> Utilidad:
    """Construye una utilidad desde un diccionario JSON, p. ej. ``{"tipo": "log", "a": 3.0}``.

    Tipos: ``log``, ``raiz`` (o ``sqrt``), ``saturada`` (o ``exp``), ``tabla``.
    Lanza ``ValueError`` si el tipo es desconocido o faltan parámetros.
    """
    if "tipo" not in d:
        raise ValueError("La utilidad no tiene el campo 'tipo'.")
    t = str(d["tipo"]).lower()
    try:
        if t == "log":
            return Log(d["a"])
        if t in ("raiz", "sqrt"):
            return Raiz(d["a"])
        if t in ("saturada", "exp"):
            return Saturada(d["a"], d["b"])
        if t == "tabla":
            return Tabla(d["ganancias"])
    except KeyError as e:
        raise ValueError(f"A la utilidad de tipo '{t}' le falta el parámetro {e}.") from None
    raise ValueError(f"Tipo de utilidad desconocido: '{t}'.")


# Tipos disponibles cuando cada nodo trae solo su coeficiente w_i (formato de la profesora).
TIPOS_COEFICIENTE = {
    "log": "w_i * ln(1 + x)",
    "raiz": "w_i * sqrt(x)",
    "saturada": "w_i * (1 - exp(-b x))",
}


def para_coeficiente(w: float, spec: Mapping[str, Any] | None = None) -> Utilidad:
    """Utilidad de un nodo a partir de su coeficiente ``w`` (``coeficiente_utilidad``).

    ``spec`` elige la forma, p. ej. ``{"tipo": "log"}`` (por defecto) o
    ``{"tipo": "saturada", "b": 0.3}``. Todas son crecientes, cóncavas y valen 0 en x = 0.
    """
    spec = dict(spec or {"tipo": "log"})
    tipo = str(spec.get("tipo", "log")).lower()
    if tipo == "log":
        return Log(w)
    if tipo in ("raiz", "sqrt"):
        return Raiz(w)
    if tipo in ("saturada", "exp"):
        return Saturada(w, spec.get("b", 0.2))
    raise ValueError(f"tipo de utilidad desconocido '{tipo}'; opciones: {', '.join(TIPOS_COEFICIENTE)}")


def describir(spec: Mapping[str, Any] | None) -> str:
    """Fórmula legible de la utilidad elegida, para la salida y la traza."""
    spec = dict(spec or {"tipo": "log"})
    tipo = str(spec.get("tipo", "log")).lower()
    tipo = {"sqrt": "raiz", "exp": "saturada"}.get(tipo, tipo)
    texto = TIPOS_COEFICIENTE.get(tipo, tipo)
    return texto.replace("-b x", f"-{spec.get('b', 0.2)} x") if tipo == "saturada" else texto
