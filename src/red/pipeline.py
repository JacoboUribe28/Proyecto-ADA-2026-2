"""Solución base completa de un caso: Parte 2 (elegir k nodos) y luego Parte 1 (repartir B).

Pasos de ``resolver``:
  1. Mide el tiempo de selección + reparto SIN traza (mediana de varias repeticiones).
  2. Si el caso es pequeño, calcula los óptimos exactos (árbol de selección y DP del reparto).
  3. Resuelve una vez CON traza (el algoritmo es determinista: decide igual que al medir).
  4. Verifica restricciones y propiedades (verificacion.py).
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Tuple

from . import __version__
from .reparto import repartir_dp, repartir_voraz
from .seleccion import seleccion_exacta, seleccion_voraz
from .verificacion import verificar

LIM_EXACTO = 500_000  # máximo de evaluaciones C(N, k) que se acepta para el óptimo exacto
LIM_DP = 3_000_000  # máximo de k * B^2 para la DP de verificación del reparto


def _mediana(v: List[float]) -> float:
    """Mediana de una lista de tiempos (robusta frente a valores atípicos)."""
    s = sorted(v)
    return s[len(s) // 2]


def _resolver_una_vez(caso: Dict[str, Any], traza_sel=None, traza_rep=None):
    """Selección voraz y reparto voraz entre los elegidos. Devuelve (A, f(A), x global, utilidad)."""
    A, f_val = seleccion_voraz(caso["masks"], caso["k"], traza_sel, caso.get("pesos"))
    sub_u = [caso["utils"][i] for i in A]
    sub_c = None if caso["caps"] is None else [caso["caps"][i] for i in A]
    xs, total = repartir_voraz(sub_u, caso["B"], sub_c, traza_rep)
    x = [0] * caso["N"]
    for pos, i in enumerate(A):
        x[i] = xs[pos]
    return A, f_val, x, total


def resolver(
    caso: Dict[str, Any],
    repeticiones: int = 5,
    verificar_optimo: bool = True,
) -> Tuple[Dict[str, Any], List[Any], List[Any]]:
    """Resuelve un caso cargado.

    Args:
        caso: diccionario devuelto por ``io_casos.parsear_caso``.
        repeticiones: repeticiones para medir el tiempo (se reporta la mediana).
        verificar_optimo: si es True y el caso es pequeño, calcula los óptimos exactos.

    Returns:
        ``(resultado, traza_seleccion, traza_reparto)``. En ambas trazas los nodos van por índice
        global (posición en el archivo).
    """
    N, k, B = caso["N"], caso["k"], caso["B"]

    # 1. tiempos, sin traza
    t_sel, t_rep = [], []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        A, _ = seleccion_voraz(caso["masks"], k, None, caso.get("pesos"))
        t1 = time.perf_counter()
        repartir_voraz([caso["utils"][i] for i in A], B,
                       None if caso["caps"] is None else [caso["caps"][i] for i in A])
        t2 = time.perf_counter()
        t_sel.append(t1 - t0)
        t_rep.append(t2 - t1)

    # 2. óptimo exacto de la selección (solo si es viable)
    exacto: Optional[Dict[str, Any]] = None
    if verificar_optimo and math.comb(N, k) <= LIM_EXACTO:
        t0 = time.perf_counter()
        A_opt, f_opt, evals = seleccion_exacta(caso["masks"], k)
        exacto = {"f_opt": f_opt, "A_opt": [caso["ids"][i] for i in A_opt], "evaluaciones": evals,
                  "tiempo_s": time.perf_counter() - t0}

    # 3. corrida con traza
    traza_sel: List[Any] = []
    traza_rep_local: List[Any] = []
    A, f_val, x, util_total = _resolver_una_vez(caso, traza_sel, traza_rep_local)
    traza_rep = [(p, A[loc], g, xv) for (p, loc, g, xv) in traza_rep_local]  # índice local -> global

    res: Dict[str, Any] = {
        "version_codigo": __version__,
        "nombre": caso["nombre"],
        "formato": caso["formato"],
        "N": N, "k": k, "B": B,
        "utilidad_individual": caso["utilidad_desc"],
        "origen_categorias": caso.get("origen_categorias", ""),
        "desempate_seleccion": "mayor ganancia de la primera unidad u_i(1) - u_i(0); luego, menor posición",
        "seleccion": [caso["ids"][i] for i in A],
        "f_voraz": f_val,
        "categorias_universo": len(caso["universo"]),
        "reparto": {str(caso["ids"][i]): x[i] for i in A},
        "utilidad_total": util_total,
        "tiempo_seleccion_s": _mediana(t_sel),
        "tiempo_reparto_s": _mediana(t_rep),
        "tiempo_total_s": _mediana(t_sel) + _mediana(t_rep),
        "repeticiones": repeticiones,
    }
    if exacto is not None:
        razon = f_val / exacto["f_opt"] if exacto["f_opt"] else 1.0
        exacto.update(razon_voraz_opt=razon, cota_1_menos_1_sobre_e=1 - 1 / math.e,
                      cumple_cota=razon >= 1 - 1 / math.e - 1e-12)
        res["seleccion_optima"] = exacto

    # 4. verificación
    chk, ok = verificar(caso, A, x, util_total, traza_sel, traza_rep,
                        exacto["f_opt"] if exacto else None)
    res["verificacion"] = {nombre: {"cumple": v[0], "detalle": v[1]} for nombre, v in chk.items()}
    res["restricciones_ok"] = ok

    # reparto óptimo por DP (solo verificación, casos pequeños)
    if verificar_optimo and k * B * B <= LIM_DP:
        sub_u = [caso["utils"][i] for i in A]
        sub_c = None if caso["caps"] is None else [caso["caps"][i] for i in A]
        _, tot_dp = repartir_dp(sub_u, B, sub_c)
        tot_dp -= sum(u.valor(0) for u in sub_u)
        res["reparto_optimo_dp"] = {"utilidad_dp": tot_dp, "diferencia": tot_dp - util_total,
                                    "voraz_es_optimo": abs(tot_dp - util_total) <= 1e-7}
    return res, traza_sel, traza_rep
