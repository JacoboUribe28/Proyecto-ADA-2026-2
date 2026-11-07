"""Verificación de restricciones y propiedades teóricas de una solución (selección + reparto).

Cada chequeo queda como ``{nombre: (cumple, detalle)}``. Si alguno falla, el caso se marca con
``restricciones_ok = False`` y ``src/ejecutar_casos.py`` termina con código 1.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .seleccion import f_cobertura

EPS = 1e-9
Resultado = Dict[str, Tuple[bool, str]]


def verificar(
    caso: Dict[str, Any],
    A: Sequence[int],
    x: Sequence[int],
    util_total: float,
    traza_sel: Sequence[Dict[str, Any]] = (),
    traza_rep: Sequence[Tuple[int, int, float, int]] = (),
    f_opt: Optional[int] = None,
) -> Tuple[Resultado, bool]:
    """Comprueba que el resultado cumple el problema y lo que predice la teoría.

    Selección: |A| = k, nodos válidos y distintos, f(A) de la traza = f(A) recalculada desde cero,
    ganancias no crecientes (submodularidad) y, si se conoce el óptimo, f(A) >= (1 - 1/e) f*.
    Reparto: x_i entero >= 0, x_i = 0 fuera de A, suma(x) <= B, x_i <= cap_i, utilidad recalculada,
    ganancias no crecientes (concavidad), ninguna transferencia de una unidad mejora la utilidad
    (con u_i cóncavas eso equivale a ser óptimo) y no sobra presupuesto que algún nodo aproveche.

    Args:
        f_opt: valor óptimo de la selección, o None si no se calculó.

    Returns:
        ``(detalle, ok)``.

    Complejidad: O(k^2 + B + N) más una evaluación de f.
    """
    N, k, B = caso["N"], caso["k"], caso["B"]
    caps = caso["caps"]
    utils = caso["utils"]
    sel = set(A)
    r: Resultado = {}

    # --- selección
    r["|A| = k"] = (len(A) == k and len(sel) == k, f"|A| = {len(A)}, k = {k}")
    r["nodos de A válidos y sin repetir"] = (all(0 <= i < N for i in A) and len(sel) == len(A), "")
    f_A = f_cobertura(caso["masks"], A)
    if traza_sel:
        f_traza = traza_sel[-1]["acumulado"]
        r["f(A) de la traza = f(A) recalculada"] = (f_traza == f_A, f"{f_traza} vs {f_A}")
        g = [t["ganancia"] for t in traza_sel]
        r["ganancias de la selección no crecientes"] = (all(g[j + 1] <= g[j] for j in range(len(g) - 1)),
                                                         "consecuencia de la submodularidad")
    if f_opt is not None:
        cota = (1 - 1 / math.e) * f_opt
        r["garantía f(voraz) >= (1 - 1/e) f(óptimo)"] = (f_A >= cota - EPS, f"{f_A} >= {cota:.4f}")

    # --- reparto
    r["x_i entero >= 0"] = (all(isinstance(v, int) and v >= 0 for v in x), "")
    r["x_i = 0 si el nodo no participa"] = (all(x[i] == 0 for i in range(N) if i not in sel), "")
    r["suma de x_i <= B"] = (sum(x) <= B, f"suma = {sum(x)}, B = {B}")
    tope = caps if caps is not None else [10**9] * N
    if caps is not None:
        r["x_i <= tope del nodo"] = (all(x[i] <= caps[i] for i in range(N)), "")
    rec = sum(utils[i].valor(x[i]) - utils[i].valor(0) for i in A)
    r["utilidad recalculada coincide"] = (abs(rec - util_total) <= 1e-6 * max(1.0, abs(rec)),
                                          f"{rec:.6f} vs {util_total:.6f}")
    if traza_rep:
        g2: List[float] = [t[2] for t in traza_rep]
        r["ganancias del reparto no crecientes"] = (all(g2[j + 1] <= g2[j] + EPS for j in range(len(g2) - 1)),
                                                     "consecuencia de la concavidad")
    # Optimalidad: mover una unidad de i a j nunca mejora (para u cóncavas, equivale al óptimo global).
    mejora = 0.0
    for i in A:
        if x[i] == 0:
            continue
        pierde = utils[i].valor(x[i]) - utils[i].valor(x[i] - 1)
        for j in A:
            if j != i and x[j] < tope[j]:
                mejora = max(mejora, utils[j].marginal(x[j]) - pierde)
    r["ninguna transferencia de una unidad mejora el reparto"] = (mejora <= EPS, f"mejor cambio = {mejora:.2e}")
    # Si sobró presupuesto, debe ser porque ningún nodo elegido puede aprovecharlo.
    sobra = B - sum(x)
    aprovecha = [i for i in A if x[i] < tope[i] and utils[i].marginal(x[i]) > EPS]
    r["no sobra presupuesto que algún nodo aproveche"] = (sobra <= 0 or not aprovecha,
                                                          f"sobran {sobra} unidades")
    return r, all(v[0] for v in r.values())
