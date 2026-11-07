"""Reportes legibles: la traza de un caso (traza.md) y el resumen de una ejecución (resumen.md).

La traza responde, en orden, las tres preguntas del caso: quiénes participan (selección, con la
ganancia marginal de cada paso), cuánto recibe cada uno (reparto, unidad por unidad) y si se
cumplen las restricciones.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import AUTOR, CODIGO, PROYECTO, __version__

FILAS_MAX_REPARTO = 120  # con más unidades, la tabla muestra el inicio y el final (el CSV tiene todo)


def _celda(texto: Any) -> str:
    """Texto seguro para una celda de tabla Markdown: escapa '|' (p. ej. en «|A| = k»)."""
    return str(texto).replace("|", "\\|")


def _categorias(caso: Dict[str, Any], mask: int) -> str:
    nombres = [caso["universo"][j] for j in range(mask.bit_length()) if mask >> j & 1]
    return ", ".join(nombres) if nombres else "ninguna"


def traza_md(caso: Dict[str, Any], res: Dict[str, Any], traza_sel: Sequence[Dict[str, Any]],
             traza_rep: Sequence[tuple]) -> str:
    """Texto Markdown de la traza de un caso."""
    ids = caso["ids"]
    so = res.get("seleccion_optima")
    L: List[str] = [
        f"# Traza del caso «{caso['nombre']}»",
        "",
        f"*{PROYECTO} · {AUTOR} ({CODIGO}) · versión {__version__}*",
        "",
        "| Dato | Valor |",
        "|---|---|",
        f"| Nodos (N), cupo (k), presupuesto (B) | {caso['N']}, {caso['k']}, {caso['B']} |",
        f"| Utilidad individual u_i(x) | {caso['utilidad_desc']} |",
        f"| Categorías de datos | {_celda(caso.get('origen_categorias', ''))} |",
        f"| Nodos elegidos | {', '.join(map(str, res['seleccion']))} |",
        f"| Categorías cubiertas f(A) | {res['f_voraz']} de {len(caso['universo'])} |",
    ]
    if so:
        L.append(f"| Óptimo exacto f* | {so['f_opt']} (razón {so['razon_voraz_opt']:.4f}; "
                 f"mínimo garantizado 0.6321) |")
    L += [
        f"| Utilidad total del reparto | {res['utilidad_total']:.4f} |",
        f"| Tiempo (selección + reparto) | {res['tiempo_total_s'] * 1e3:.3f} ms, mediana de {res['repeticiones']} |",
        f"| ¿Cumple todo? | {'Sí' if res['restricciones_ok'] else '**NO**'} |",
        "",
        "## A. ¿Quiénes participan? Selección voraz",
        "",
        "En cada paso se agrega el nodo que aporta más categorías **nuevas** (Δ). Δ se recalcula en cada "
        "paso, porque lo ya cubierto deja de contar. Empates en Δ: gana el nodo que más aprovecha su primera "
        "unidad de presupuesto (mayor u_i(1) − u_i(0), es decir, mayor coeficiente); si también empatan, "
        "el que aparece primero en el archivo.",
        "",
        "| Paso | Elegido | Δ | Categorías nuevas | f(A) acumulada | Segundo mejor (Δ) |",
        "|---|---|---|---|---|---|",
    ]
    for t in traza_sel:
        otros = sorted(((d, j) for j, d in t["candidatos"].items() if j != t["nodo"]), key=lambda p: (-p[0], p[1]))
        segundo = f"{ids[otros[0][1]]} ({otros[0][0]})" if otros else "—"
        L.append(f"| {t['paso']} | {ids[t['nodo']]} | {t['ganancia']} | {_categorias(caso, t['nuevas'])} | "
                 f"{t['acumulado']} | {segundo} |")
    L += [
        "",
        "## B. ¿Cuánto recibe cada uno? Reparto voraz con montículo",
        "",
        "Cada unidad de presupuesto va al nodo elegido cuya siguiente unidad aporta más (g). "
        "Como u_i es cóncava, las ganancias de la columna g nunca suben.",
        "",
        "| Unidad | Para | g (ganancia) | Unidades del nodo |",
        "|---|---|---|---|",
    ]
    filas: List[Optional[tuple]] = list(traza_rep)
    if len(filas) > FILAS_MAX_REPARTO:
        mitad = FILAS_MAX_REPARTO // 2
        mostrar = filas[:mitad] + [None] + filas[-mitad:]
    else:
        mostrar = filas
    for f in mostrar:
        if f is None:
            L.append(f"| … | … {len(filas) - FILAS_MAX_REPARTO} unidades más en traza_reparto.csv … | | |")
            continue
        p, i, g, xv = f
        L.append(f"| {p} | {ids[i]} | {g:.4f} | {xv} |")
    L += ["", "| Nodo | Unidades recibidas | Utilidad u_i(x_i) |", "|---|---|---|"]
    for nodo, unidades in res["reparto"].items():
        i = [str(v) for v in ids].index(nodo)
        L.append(f"| {nodo} | {unidades} | {caso['utils'][i].valor(unidades):.4f} |")
    L += ["", "## C. ¿Se cumplen las restricciones?", "", "| # | Comprobación | ¿Cumple? | Detalle |",
          "|---|---|---|---|"]
    for n, (nombre, v) in enumerate(res["verificacion"].items(), start=1):
        L.append(f"| {n} | {_celda(nombre)} | {'Sí' if v['cumple'] else '**NO**'} | {_celda(v['detalle'])} |")
    return "\n".join(L) + "\n"


def resumen_md(filas: Sequence[Dict[str, Any]], errores: Sequence[tuple], entorno: str) -> str:
    """Texto Markdown del resumen de una ejecución (una fila por caso)."""
    L = [
        "# Resumen de la ejecución",
        "",
        f"*{PROYECTO} · {AUTOR} ({CODIGO}) · versión {__version__} · {entorno}*",
        "",
        "Tiempo = mediana de las repeticiones de selección + reparto, sin escribir trazas.",
        "",
        "| Caso | N | k | B | f(A) | f óptimo | Utilidad | Tiempo (ms) | ¿Cumple? |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for f in filas:
        L.append(f"| {f['caso']} | {f['N']} | {f['k']} | {f['B']} | {f['f_voraz']} | {f['f_optimo']} | "
                 f"{float(f['utilidad_total']):.4f} | {float(f['t_total_s']) * 1e3:.3f} | "
                 f"{'Sí' if f['restricciones_ok'] else '**NO**'} |")
    if errores:
        L += ["", "## Casos que no se pudieron ejecutar", "", "| Archivo | Motivo |", "|---|---|"]
        L += [f"| {_celda(n)} | {_celda(m)} |" for n, m in errores]
    return "\n".join(L) + "\n"
