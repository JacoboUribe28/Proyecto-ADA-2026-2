#!/usr/bin/env python3
"""Diagnóstico del crecimiento de 'Reparto vs N': ¿es del algoritmo o del montículo de Python?

Compara el costo por unidad de ``repartir_voraz`` (B fijo, N creciente) con el de ``heapq.heapreplace``
aislado (sin utilidades). Si ambos crecen parecido, el exceso sobre log N es del montículo/memoria.

    python Informe/code/diagnostico_heap.py
"""

import heapq
import math
import random
import time

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
from red.reparto import repartir_voraz
from red.utilidad import Log

B = 800_000
rnd = random.Random(1)


def mediana(f, rep=3):
    ts = []
    for _ in range(rep):
        t0 = time.perf_counter()
        f()
        ts.append(time.perf_counter() - t0)
    return sorted(ts)[len(ts) // 2]


print(f"{'N':>7} {'log2 N':>7} {'reparto us/unidad':>18} {'solo heap us/op':>16}")
base = None
for N in [2000, 8000, 32000, 64000]:
    utils = [Log(rnd.uniform(1, 9)) for _ in range(N)]
    t_rep = mediana(lambda: repartir_voraz(utils, B)) / B * 1e6
    h = [(-rnd.random() * 10, i) for i in range(N)]
    heapq.heapify(h)

    def solo_heap():
        hh = list(h)
        for _ in range(B):
            g, i = hh[0]
            heapq.heapreplace(hh, (g * 0.98, i))

    t_h = mediana(solo_heap) / B * 1e6
    base = base or (t_rep, t_h, math.log2(N))
    r1, r2 = t_rep / base[0], t_h / base[1]
    print(f"{N:>7} {math.log2(N):>7.1f} {t_rep:>12.3f} (x{r1:.2f}) {t_h:>9.3f} (x{r2:.2f})")
print(f"Crecimiento esperado por log N entre N=2000 y N=64000: x{math.log2(64000) / math.log2(2000):.2f}")
