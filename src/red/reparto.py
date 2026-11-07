"""PARTE 1 — Reparto óptimo del presupuesto B entre N nodos con utilidades cóncavas.

Algoritmo voraz por ganancia marginal con montículo (cola de prioridad)::

    construcción del montículo ........ O(N)
    B extracciones/reinserciones ...... O(B log N)
    T(N, B) = O(N + B log N)           (= O(B log N) cuando B >= N)

La cota es pseudo-polinomial: B aparece como valor numérico, no como número de bits.
"""

from __future__ import annotations

import heapq
from typing import List, Optional, Sequence, Tuple

from .utilidad import Utilidad

# (paso, nodo, ganancia_marginal, unidades_del_nodo_tras_asignar)
PasoReparto = Tuple[int, int, float, int]


def repartir_voraz(
    utilidades: Sequence[Utilidad],
    B: int,
    caps: Optional[Sequence[int]] = None,
    traza: Optional[List[PasoReparto]] = None,
) -> Tuple[List[int], float]:
    """Reparte hasta ``B`` unidades enteras maximizando la suma de utilidades.

    Args:
        utilidades: una utilidad cóncava y creciente por nodo.
        B: presupuesto total (entero >= 0).
        caps: tope opcional de unidades por nodo (presupuesto de ruido tolerable).
        traza: si se pasa una lista, se le agregan tuplas ``PasoReparto`` (una por unidad).

    Returns:
        ``(x, total)``: ``x[i]`` unidades del nodo i y utilidad ganada sobre u_i(0).

    Complexity: O(N + B log N) tiempo, O(N) espacio.
    """
    if B < 0:
        raise ValueError("El presupuesto B debe ser >= 0.")
    N = len(utilidades)
    x = [0] * N
    total = 0.0
    # Montículo de MÍNIMOS de Python: se guarda -ganancia; el índice i rompe empates (menor primero).
    heap: List[Tuple[float, int]] = []
    for i, u in enumerate(utilidades):
        if caps is None or caps[i] > 0:
            heap.append((-u.marginal(0), i))
    heapq.heapify(heap)  # O(N)
    paso = 0
    while paso < B and heap:  # a lo sumo B iteraciones
        neg_g, i = heap[0]
        g = -neg_g
        if g <= 0:  # nadie aporta ya nada: se detiene
            break
        x[i] += 1
        total += g
        paso += 1
        if traza is not None:
            traza.append((paso, i, g, x[i]))
        if caps is not None and x[i] >= caps[i]:
            heapq.heappop(heap)  # nodo saturado: sale del montículo
        else:
            # Reemplaza el tope por la siguiente ganancia del mismo nodo en una sola operación O(log N).
            heapq.heapreplace(heap, (-utilidades[i].marginal(x[i]), i))
    return x, total


def repartir_dp(
    utilidades: Sequence[Utilidad],
    B: int,
    caps: Optional[Sequence[int]] = None,
) -> Tuple[List[int], float]:
    """Óptimo exacto por programación dinámica, O(N * B^2).

    Solo para VERIFICAR en instancias pequeñas que el voraz es óptimo.
    ``dp[i][b]`` = mejor utilidad usando los i primeros nodos con exactamente b unidades.
    """
    N = len(utilidades)
    NEG = float("-inf")
    dp = [[NEG] * (B + 1) for _ in range(N + 1)]
    elec = [[0] * (B + 1) for _ in range(N + 1)]
    dp[0][0] = 0.0
    for i in range(1, N + 1):
        u = utilidades[i - 1]
        tope = B if caps is None else min(B, caps[i - 1])
        for b in range(B + 1):
            for xi in range(0, min(b, tope) + 1):
                prev = dp[i - 1][b - xi]
                if prev == NEG:
                    continue
                v = prev + u.valor(xi)
                if v > dp[i][b]:
                    dp[i][b] = v
                    elec[i][b] = xi
    b_best = max(range(B + 1), key=lambda b: dp[N][b])
    x = [0] * N
    b = b_best
    for i in range(N, 0, -1):  # reconstrucción hacia atrás
        x[i - 1] = elec[i][b]
        b -= x[i - 1]
    return x, dp[N][b_best]
