"""Generador de instancias sintéticas reproducibles (semilla fija)."""

import random


def generar_caso(nombre, N, k, B, U, tam_medio=None, semilla=0, con_caps=False):
    """Caso con N nodos, universo de U elementos, cupo k y presupuesto B.

    Cada nodo cubre ~tam_medio elementos del universo y tiene una utilidad cóncava
    aleatoria (log, raíz o saturada). Devuelve un dict listo para guardarse como JSON."""
    rnd = random.Random(semilla)
    tam_medio = tam_medio or max(2, U // 10)
    nodos = []
    for i in range(N):
        m = max(1, min(U, int(rnd.gauss(tam_medio, tam_medio / 3))))
        cobertura = sorted(rnd.sample(range(U), m))
        t = rnd.choice(["log", "raiz", "saturada"])
        a = round(rnd.uniform(1.0, 10.0), 3)
        if t == "saturada":
            util = {"tipo": t, "a": a * 5, "b": round(rnd.uniform(0.01, 0.2), 4)}
        else:
            util = {"tipo": t, "a": a}
        nodo = {"id": i, "cobertura": cobertura, "utilidad": util}
        if con_caps:
            nodo["cap"] = rnd.randint(max(1, B // N), max(2, 3 * B // N))
        nodos.append(nodo)
    return {"nombre": nombre, "N": N, "k": k, "B": B, "universo": U, "nodos": nodos}


def completar_categorias(nodos, universo=20, minimo=3, maximo=7, semilla=36921, reemplazar=False):
    """Agrega a cada nodo una lista de categorías sintéticas ("K01", "K02", ...) reproducible.

    Sirve para casos que traen solo el coeficiente de utilidad de cada nodo: la selección necesita
    saber qué categorías de datos aporta cada uno. Misma semilla => mismas categorías.

    Args:
        nodos: lista de dicts de nodo (se modifica en el lugar).
        universo: cuántas categorías distintas existen.
        minimo, maximo: rango de categorías por nodo (1 <= minimo <= maximo <= universo).
        semilla: semilla del generador (por defecto, el código del autor).
        reemplazar: si es False, respeta los nodos que ya traen "categorias".

    Returns:
        Cuántos nodos recibieron categorías nuevas.
    """
    if not 1 <= minimo <= maximo <= universo:
        raise ValueError("se exige 1 <= minimo <= maximo <= universo")
    rnd = random.Random(semilla)
    nombres = [f"K{j:02d}" for j in range(1, universo + 1)]
    cambiados = 0
    for n in nodos:
        cantidad = rnd.randint(minimo, maximo)
        elegidas = sorted(rnd.sample(nombres, cantidad))   # se sortea siempre: el resultado no depende
        if reemplazar or "categorias" not in n:            # de qué nodos ya traían categorías
            n["categorias"] = elegidas
            cambiados += 1
    return cambiados
