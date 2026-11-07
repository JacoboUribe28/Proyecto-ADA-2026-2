#!/usr/bin/env python3
"""Genera los casos sintéticos de ejemplo (semillas fijas) en casos/ejemplos/."""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)  # carpeta src/
DESTINO = os.path.join(os.path.dirname(AQUI), "casos", "ejemplos")
from red.generador import generar_caso  # noqa: E402

CASOS = [  # nombre, N, k, B, U, semilla, con_caps
    ("ej01_pequeno", 8, 3, 20, 30, 1, False),
    ("ej02_pequeno_caps", 10, 4, 25, 40, 2, True),
    ("ej03_mediano", 14, 5, 40, 80, 3, False),
    ("ej04_grande", 500, 20, 2000, 400, 4, False),
    ("ej05_grande_caps", 2000, 40, 10000, 800, 5, True),
]
os.makedirs(DESTINO, exist_ok=True)
for nombre, N, k, B, U, s, caps in CASOS:
    c = generar_caso(nombre, N, k, B, U, semilla=s, con_caps=caps)
    with open(os.path.join(DESTINO, f"{nombre}.json"), "w", encoding="utf-8") as fh:
        json.dump(c, fh)
    print("generado", nombre)
