#!/usr/bin/env python3
"""Validación experimental: mide tiempos para tamaños crecientes y los contrasta con T(n) teórico.

python Informe/code/experimentos.py     # genera Informe/img/*.png e Informe/code/experimentos*.csv
"""

import csv
import gc
import math
import os
import random
import time
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

CODE = os.path.dirname(os.path.abspath(__file__))               # Informe/code
INFORME = os.path.dirname(CODE)                                    # Informe
sys.path.insert(0, os.path.join(os.path.dirname(INFORME), "src"))  # código del proyecto
from red.utilidad import Log, Raiz, Saturada  # noqa: E402
from red.reparto import repartir_voraz  # noqa: E402
from red.seleccion import seleccion_voraz  # noqa: E402

REP = 7
os.makedirs(os.path.join(INFORME, "img"), exist_ok=True)


def mediana_tiempo(fn):
    """Mediana de REP mediciones de fn(), tras una ejecución de calentamiento que no se mide.

    El calentamiento evita que el primer tamaño salga inflado por cachés frías o por la frecuencia
    del procesador aún baja; el recolector de basura se apaga mientras se mide (como hace timeit).
    """
    fn()  # calentamiento (no se mide)
    t = []
    gc_activo = gc.isenabled()
    gc.disable()
    try:
        for _ in range(REP):
            t0 = time.perf_counter()
            fn()
            t.append(time.perf_counter() - t0)
    finally:
        if gc_activo:
            gc.enable()
    return sorted(t)[len(t) // 2]


def utils(N, rnd):
    f = [
        lambda: Log(rnd.uniform(1, 9)),
        lambda: Raiz(rnd.uniform(1, 9)),
        lambda: Saturada(rnd.uniform(5, 30), rnd.uniform(0.01, 0.2)),
    ]
    return [rnd.choice(f)() for _ in range(N)]


def masks(N, U, rnd):
    return [sum(1 << e for e in rnd.sample(range(U), max(1, U // 10))) for _ in range(N)]


def ajustar(xs, ts, teo):
    """Mínimos cuadrados de t ≈ c * teo(x). Devuelve c y R² de ese ajuste."""
    th = [teo(x) for x in xs]
    c = sum(t * h for t, h in zip(ts, th)) / sum(h * h for h in th)
    pred = [c * h for h in th]
    media = sum(ts) / len(ts)
    ss_res = sum((t - p) ** 2 for t, p in zip(ts, pred))
    ss_tot = sum((t - media) ** 2 for t in ts)
    return c, 1 - ss_res / ss_tot


def experimento(nombre, xlabel, titulo, xs, medir, teo, teo_label, archivo, filas):
    ts = [medir(x) for x in xs]
    c, r2 = ajustar(xs, ts, teo)
    for x, t in zip(xs, ts):
        filas.append([nombre, x, t, c * teo(x), t / teo(x)])
    print(f"{nombre:28s} c={c:.3e}  R²={r2:.5f}")
    plt.figure(figsize=(6, 4))
    plt.plot(xs, ts, "o-", label="medido")
    xx = [xs[0] + i * (xs[-1] - xs[0]) / 200 for i in range(201)]
    plt.plot(xx, [c * teo(x) for x in xx], "--", label=f"c·{teo_label}  (R²={r2:.4f})")
    plt.xlabel(xlabel)
    plt.ylabel("tiempo (s)")
    plt.title(titulo)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(INFORME, "img", archivo), dpi=150)
    plt.close()
    return c, r2


def main():
    rnd = random.Random(2026)
    filas = []
    resumen = []

    # Parte 1 — vs B (N fijo): T = O(N + B log N) ~ lineal en B
    N0 = 2000
    U0 = utils(N0, rnd)
    Bs = [20000, 40000, 80000, 160000, 320000, 640000]
    resumen.append(
        ("Parte 1: tiempo vs B (N=2000)",)
        + experimento(
            "reparto_vs_B",
            "B (presupuesto)",
            "Reparto voraz: tiempo vs B  (N=2000)",
            Bs,
            lambda B: mediana_tiempo(lambda: repartir_voraz(U0, B)),
            lambda B: N0 + B * math.log(N0),
            "(N + B ln N)",
            "reparto_vs_B.png",
            filas,
        )
    )

    # Parte 1 — vs N con B = 20N: T = O(N + 20N log N) = O(N log N)
    Ns = [2000, 4000, 8000, 16000, 32000, 64000]
    cache = {N: utils(N, rnd) for N in Ns}
    resumen.append(
        ("Parte 1: tiempo vs N (B=20N)",)
        + experimento(
            "reparto_vs_N",
            "N (nodos)",
            "Reparto voraz: tiempo vs N  (B=20N)",
            Ns,
            lambda N: mediana_tiempo(lambda: repartir_voraz(cache[N], 20 * N)),
            lambda N: N + 20 * N * math.log(N),
            "(N + 20N ln N)",
            "reparto_vs_N.png",
            filas,
        )
    )

    # Parte 2 — vs N (k fijo, universo fijo): T = O(N k tau)
    U, k0 = 1000, 20
    Ns2 = [1000, 2000, 4000, 8000, 16000, 32000]
    mk = {N: masks(N, U, rnd) for N in Ns2}
    # Pesos de desempate (como en la solución base); generador aparte para no cambiar las instancias.
    rnd_p = random.Random(7)
    pw = {N: [rnd_p.uniform(1, 9) for _ in range(N)] for N in Ns2}
    resumen.append(
        ("Parte 2: tiempo vs N (k=20)",)
        + experimento(
            "seleccion_vs_N",
            "N (nodos)",
            "Selección voraz: tiempo vs N  (k=20)",
            Ns2,
            lambda N: mediana_tiempo(lambda: seleccion_voraz(mk[N], k0, None, pw[N])),
            lambda N: N * k0,
            "(N·k)",
            "seleccion_vs_N.png",
            filas,
        )
    )

    # Parte 2 — vs k (N fijo)
    N2 = 8000
    mk2 = masks(N2, U, rnd)
    pw2 = [rnd_p.uniform(1, 9) for _ in range(N2)]
    ks = [5, 10, 20, 40, 80, 160]
    resumen.append(
        ("Parte 2: tiempo vs k (N=8000)",)
        + experimento(
            "seleccion_vs_k",
            "k (cupo)",
            "Selección voraz: tiempo vs k  (N=8000)",
            ks,
            lambda k: mediana_tiempo(lambda: seleccion_voraz(mk2, k, None, pw2)),
            lambda k: N2 * k,
            "(N·k)",
            "seleccion_vs_k.png",
            filas,
        )
    )

    with open(os.path.join(CODE, "experimentos.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["experimento", "x", "t_medido_s", "t_teorico_ajustado_s", "t_medido/T_teorico"])
        w.writerows(filas)
    with open(os.path.join(CODE, "experimentos_ajuste.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["experimento", "constante_c", "R2"])
        w.writerows(resumen)


if __name__ == "__main__":
    main()
