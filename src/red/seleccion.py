"""PARTE 2 — Selección de k nodos participantes (maximizar la utilidad conjunta f).

Implementación: f(A) = |unión de las categorías de los nodos de A| (cobertura: normalizada,
monótona y submodular). Cada conjunto de categorías se guarda como un entero-bitmask, un bit por
categoría del universo::

    ganancia marginal de j  =  popcount(S_j & ~cubierto)      -> costo tau = O(|U| / w)

* ``seleccion_voraz``: k pasos x N candidatos => kN - k(k-1)/2 evaluaciones = Theta(N k).
  Garantía (Nemhauser, Wolsey y Fisher, 1978): f(voraz) >= (1 - 1/e) * f(óptimo).
  Empates en la ganancia: se prefiere el nodo de mayor peso (ganancia de su primera unidad de
  presupuesto), para que a igual cobertura entren los nodos que más aprovechan el reparto.
* ``seleccion_exacta``: árbol "incluir / no incluir" con poda. Evalúa f exactamente C(N, k) veces
  (recurrencia de Pascal L(n, r) = L(n-1, r-1) + L(n-1, r)). Solo para N pequeño.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# Un paso de la traza de selección:
#   paso, nodo, ganancia (Delta), acumulado (f(A) tras agregarlo),
#   nuevas (bitmask de las categorías que aporta), candidatos ({nodo: Delta} de todos los evaluados)
PasoSeleccion = Dict[str, Any]


def f_cobertura(masks: Sequence[int], A: Iterable[int]) -> int:
    """Utilidad conjunta f(A): número de categorías distintas que cubren los nodos de A."""
    cub = 0
    for i in A:
        cub |= masks[i]
    return cub.bit_count()


def seleccion_voraz(
    masks: Sequence[int],
    k: int,
    traza: Optional[List[PasoSeleccion]] = None,
    pesos: Optional[Sequence[float]] = None,
) -> Tuple[List[int], int]:
    """Elige k nodos agregando en cada paso el de mayor ganancia marginal.

    Args:
        masks: bitmask de categorías de cada nodo.
        k: número de nodos a elegir, ``0 <= k <= N``.
        traza: lista opcional; recibe un ``PasoSeleccion`` por paso. Solo observa: no cambia
            ninguna decisión.
        pesos: criterio de desempate opcional, uno por nodo (en la solución base, la ganancia de la
            primera unidad de presupuesto, u_i(1) - u_i(0), que es proporcional al coeficiente w_i).

    Returns:
        ``(A, f(A))`` con A en orden de elección. Empates en la ganancia: gana el de mayor peso y, si
        también empatan (o no hay pesos), el índice menor. Si ya nadie aporta, se siguen agregando
        nodos hasta |A| = k. El desempate no cambia f(A) en cada paso, así que la garantía
        1 - 1/e se mantiene.

    Raises:
        ValueError: si k no está en [0, N] o ``pesos`` no tiene N valores.

    Complejidad: Theta(N k) evaluaciones de la ganancia, cada una O(|U| / w).
    """
    N = len(masks)
    if k < 0 or k > N:
        raise ValueError(f"k debe cumplir 0 <= k <= N (k={k}, N={N}).")
    if pesos is not None and len(pesos) != N:
        raise ValueError(f"se esperaban {N} pesos y llegaron {len(pesos)}.")
    peso = pesos if pesos is not None else [0.0] * N
    elegido = [False] * N
    cubierto = 0
    A: List[int] = []
    for paso in range(1, k + 1):
        mejor, mejor_g = -1, -1
        candidatos: Dict[int, int] = {}
        for j in range(N):  # O(N) candidatos por paso
            if elegido[j]:
                continue
            g = (masks[j] & ~cubierto).bit_count()  # Delta_j(A): categorías nuevas de j
            if traza is not None:
                candidatos[j] = g
            # '>' estricto: con igual ganancia y peso se queda el índice menor
            if g > mejor_g or (g == mejor_g and peso[j] > peso[mejor]):
                mejor, mejor_g = j, g
        nuevas = masks[mejor] & ~cubierto
        elegido[mejor] = True
        cubierto |= masks[mejor]
        A.append(mejor)
        if traza is not None:
            traza.append({"paso": paso, "nodo": mejor, "ganancia": mejor_g,
                          "acumulado": cubierto.bit_count(), "nuevas": nuevas, "candidatos": candidatos})
    return A, cubierto.bit_count()


def seleccion_exacta(masks: Sequence[int], k: int) -> Tuple[List[int], int, int]:
    """Óptimo exacto con el árbol "incluir / no incluir" el nodo i, con poda.

    Casos de ``explorar(i, A)``:
      1. |A| = k: hoja; se evalúa f(A) desde cero (tau = O(k |U| / w)).
      2. quedan menos nodos que lugares libres: rama sin solución (poda).
      3. se ramifica: (a) incluir i, (b) no incluir i; gana la mejor (empate: la de incluir).

    Returns:
        ``(A*, f(A*), evaluaciones)``; ``evaluaciones`` es siempre C(N, k).

    Raises:
        ValueError: si k no está en [0, N].

    Complejidad: C(N, k) evaluaciones de f; O(C(N, k) (N + tau)) tiempo. Solo para N pequeño.
    """
    N = len(masks)
    if k < 0 or k > N:
        raise ValueError(f"k debe cumplir 0 <= k <= N (k={k}, N={N}).")
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 2 * N + 100))  # profundidad máxima: N
    evaluaciones = 0
    A: List[int] = []

    def explorar(i: int) -> Tuple[int, List[int]]:
        nonlocal evaluaciones
        if len(A) == k:  # caso 1: cupo lleno
            evaluaciones += 1
            return f_cobertura(masks, A), list(A)
        if N - i < k - len(A):  # caso 2: poda
            return -1, []
        A.append(i)  # caso 3a: incluir i
        v1, A1 = explorar(i + 1)
        A.pop()
        v2, A2 = explorar(i + 1)  # caso 3b: no incluir i
        return (v1, A1) if v1 >= v2 else (v2, A2)

    valor, mejor = explorar(0)
    return mejor, valor, evaluaciones


def desde_cobertura_maxima(
    universo: Iterable[Any],
    subconjuntos: Sequence[Iterable[Any]],
    k: int,
    t: int,
) -> Tuple[List[int], int, int]:
    """Reducción Cobertura Máxima -> Selección de participantes (prueba de NP-dureza).

    Un nodo por subconjunto, f(A) = |unión|, cupo k y umbral t; se construye en O(sum |S_i|).
    Devuelve ``(masks, k, t)``, la instancia de selección equivalente.
    """
    idx = {e: j for j, e in enumerate(universo)}
    masks = [sum(1 << idx[e] for e in set(S)) for S in subconjuntos]
    return masks, k, t
