#!/usr/bin/env python3
"""Agrega categorías de datos sintéticas a un caso que trae solo el coeficiente de cada nodo.

La selección maximiza f(A) = |categorías distintas cubiertas|, así que cada nodo necesita su lista
de categorías. Este script las genera de forma reproducible (misma semilla => mismas categorías) y
deja anotado el origen en la clave "origen_categorias" del archivo nuevo. El original no se toca.

No es obligatorio: src/ejecutar_casos.py genera las mismas categorías (con los valores por defecto)
al leer un caso que no las trae. Sirve para verlas en un archivo o para usar otros parámetros.

Uso (desde la carpeta del proyecto):
    python src/completar_categorias.py casos/entrada_G2_red_15_nodos.json -o con_categorias.json
    python src/completar_categorias.py caso.json -o nuevo.json --universo 30 --min 4 --max 8 --semilla 7
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # carpeta src/
from red.generador import completar_categorias  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", help="caso .json recibido")
    ap.add_argument("-o", "--salida", required=True, help="archivo .json nuevo")
    ap.add_argument("--universo", type=int, default=20, help="categorías distintas posibles (20)")
    ap.add_argument("--min", type=int, default=3, dest="minimo", help="mínimo por nodo (3)")
    ap.add_argument("--max", type=int, default=7, dest="maximo", help="máximo por nodo (7)")
    ap.add_argument("--semilla", type=int, default=36921, help="semilla (36921)")
    ap.add_argument("--reemplazar", action="store_true", help="reemplazar categorías que ya existan")
    a = ap.parse_args()
    if not 1 <= a.minimo <= a.maximo <= a.universo:
        ap.error("se exige 1 <= --min <= --max <= --universo")
    with open(a.entrada, encoding="utf-8") as fh:
        d = json.load(fh)
    n = completar_categorias(d["nodos"], a.universo, a.minimo, a.maximo, a.semilla, a.reemplazar)
    d["origen_categorias"] = (f"Sintéticas (la entrada recibida no las trae): src/completar_categorias.py, "
                              f"semilla {a.semilla}, universo {a.universo}, entre {a.minimo} y {a.maximo} por nodo")
    with open(a.salida, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
    print(f"{n} nodos con categorías nuevas -> {a.salida}")


if __name__ == "__main__":
    main()
