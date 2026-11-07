"""Proyecto ADA 2026-2 · Red. Autor: Jacobo Uribe Montoya (código 36921).

Selección de participantes (Parte 2, NP-difícil, voraz 1 - 1/e) y reparto del presupuesto de
ruido (Parte 1, voraz exacto con montículo).

La versión se lee del archivo VERSION de la raíz del proyecto (fuente única), y se estampa en
cada salida para que informe, código y resultados correspondan a la misma versión.
"""

import os

PROYECTO = "Proyecto ADA 2026-2"
AUTOR = "Jacobo Uribe Montoya"
CODIGO = "36921"


def _leer_version() -> str:
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "VERSION")
    try:
        with open(ruta, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:  # p. ej. si el paquete se copia sin la raíz del proyecto
        return "desconocida"


__version__ = _leer_version()
