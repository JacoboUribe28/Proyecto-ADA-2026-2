#!/usr/bin/env python3
"""Proyecto ADA 2026-2 — ejecuta la solución base sobre uno o varios casos y guarda resultados y trazas.

Uso (desde la raíz del proyecto):
    python src/ejecutar_casos.py                                   # todos los .json de casos/
    python src/ejecutar_casos.py --casos casos/ejemplos            # otra carpeta
    python src/ejecutar_casos.py --casos mi_caso.json --salida resultados_prueba
    python src/ejecutar_casos.py --utilidad raiz                   # otra forma de u_i

Por cada caso crea resultados/<caso>/ con salida.json (resultado, tiempo y verificación),
traza.json y traza.md (selección, ganancias marginales, reparto y restricciones) y las mismas
trazas en CSV; al final, resultados/resumen.md y resultados/resumen.csv.
Un caso inválido se informa y no detiene a los demás. Código de salida: 0 si todo cumple, 1 si no.
"""

import argparse
import csv
import glob
import json
import os
import platform
import sys

from red import AUTOR, CODIGO, PROYECTO, __version__
from red.io_casos import cargar_caso
from red.pipeline import resolver
from red.reporte import resumen_md, traza_md
from red.utilidad import TIPOS_COEFICIENTE

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raíz del proyecto


def escribir_caso(carpeta, caso, res, t_sel, t_rep):
    """Escribe salida.json, traza.json, traza.md y las dos trazas CSV del caso (nodos por su id)."""
    os.makedirs(carpeta, exist_ok=True)
    ids = caso["ids"]
    with open(os.path.join(carpeta, "salida.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(carpeta, "traza.json"), "w", encoding="utf-8") as fh:
        json.dump(traza_json(caso, res, t_sel, t_rep), fh, indent=2, ensure_ascii=False)
    with open(os.path.join(carpeta, "traza.md"), "w", encoding="utf-8") as fh:
        fh.write(traza_md(caso, res, t_sel, t_rep))
    with open(os.path.join(carpeta, "traza_seleccion.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["paso", "nodo", "ganancia_marginal", "f_acumulada", "categorias_nuevas"])
        for t in t_sel:
            nuevas = [caso["universo"][j] for j in range(t["nuevas"].bit_length()) if t["nuevas"] >> j & 1]
            w.writerow([t["paso"], ids[t["nodo"]], t["ganancia"], t["acumulado"], " ".join(nuevas)])
    with open(os.path.join(carpeta, "traza_reparto.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["unidad", "nodo", "ganancia_marginal", "unidades_del_nodo"])
        w.writerows([(p, ids[i], f"{g:.10f}", xv) for (p, i, g, xv) in t_rep])


def traza_json(caso, res, t_sel, t_rep):
    """Traza completa en formato máquina: selección (con la ganancia de todos los candidatos en cada
    paso), reparto unidad por unidad y verificación de restricciones. Nodos por su id."""
    ids = caso["ids"]

    def categorias(mask):
        return [caso["universo"][j] for j in range(mask.bit_length()) if mask >> j & 1]

    return {
        "version": res["version_codigo"], "caso": caso["nombre"],
        "seleccion": [{"paso": t["paso"], "elegido": ids[t["nodo"]], "ganancia": t["ganancia"],
                       "categorias_nuevas": categorias(t["nuevas"]), "f_acumulada": t["acumulado"],
                       "ganancias_candidatos": {str(ids[j]): g for j, g in t["candidatos"].items()}}
                      for t in t_sel],
        "reparto": [{"unidad": p, "nodo": ids[i], "ganancia": g, "unidades_del_nodo": xv}
                    for (p, i, g, xv) in t_rep],
        "verificacion": res["verificacion"],
    }


def fila_resumen(res):
    so = res.get("seleccion_optima")
    return {
        "caso": res["nombre"], "N": res["N"], "k": res["k"], "B": res["B"],
        "f_voraz": res["f_voraz"], "f_optimo": so["f_opt"] if so else "",
        "razon_vs_optimo": f"{so['razon_voraz_opt']:.4f}" if so else "",
        "utilidad_total": f"{res['utilidad_total']:.6f}",
        "t_seleccion_s": f"{res['tiempo_seleccion_s']:.6f}", "t_reparto_s": f"{res['tiempo_reparto_s']:.6f}",
        "t_total_s": f"{res['tiempo_total_s']:.6f}", "restricciones_ok": res["restricciones_ok"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--casos", nargs="+", default=[os.path.join(RAIZ, "casos")],
                    help="archivos .json y/o carpetas (por defecto casos/; no entra en subcarpetas)")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "resultados"), help="carpeta de resultados")
    ap.add_argument("--repeticiones", type=int, default=5, help="repeticiones para la mediana de tiempo")
    ap.add_argument("--utilidad", choices=sorted(TIPOS_COEFICIENTE),
                    help="forma de u_i para casos en formato de la profesora (por defecto log)")
    ap.add_argument("--sin-optimo", action="store_true", help="no calcular los óptimos exactos de verificación")
    a = ap.parse_args()
    if a.repeticiones < 1:
        sys.exit("--repeticiones debe ser >= 1")
    spec = {"tipo": a.utilidad} if a.utilidad else None

    rutas = []
    for e in a.casos:
        rutas += sorted(glob.glob(os.path.join(e, "*.json"))) if os.path.isdir(e) else [e]
    if not rutas:
        sys.exit("No se encontraron casos .json")

    print(f"{PROYECTO} v{__version__} · {AUTOR} ({CODIGO})")
    filas, errores = [], []
    for ruta in rutas:
        try:
            caso = cargar_caso(ruta, spec)
        except (ValueError, KeyError, TypeError, OSError) as err:  # incluye JSON inválido
            print(f"[ERROR] {os.path.basename(ruta)}: {err}", file=sys.stderr)
            errores.append((os.path.basename(ruta), str(err)))
            continue
        res, t_sel, t_rep = resolver(caso, repeticiones=a.repeticiones, verificar_optimo=not a.sin_optimo)
        escribir_caso(os.path.join(a.salida, caso["nombre"]), caso, res, t_sel, t_rep)
        filas.append(fila_resumen(res))
        print(f"  {caso['nombre']}: N={res['N']} k={res['k']} B={res['B']} | f(A)={res['f_voraz']} | "
              f"utilidad={res['utilidad_total']:.4f} | {res['tiempo_total_s'] * 1e3:.3f} ms | "
              f"{'cumple' if res['restricciones_ok'] else 'NO CUMPLE'}")
    if not filas:  # ningún caso válido: no se toca el resumen existente
        sys.exit(f"Ningún caso pudo ejecutarse ({len(errores)} con error).")
    entorno = f"Python {platform.python_version()}, {platform.system()}"
    with open(os.path.join(a.salida, "resumen.md"), "w", encoding="utf-8") as fh:
        fh.write(resumen_md(filas, errores, entorno))
    with open(os.path.join(a.salida, "resumen.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"Resultados en {a.salida}")
    if errores:
        print(f"{len(errores)} caso(s) con error; ver los mensajes [ERROR] y resumen.md", file=sys.stderr)
    sys.exit(0 if all(f["restricciones_ok"] for f in filas) and not errores else 1)


if __name__ == "__main__":
    main()
