"""Lectura y validación de casos (JSON) -> diccionario interno del caso.

Se aceptan dos formatos (ver docs/manual_tecnico.md, sección 7):

* **Formato de la profesora** (tiene la clave ``"parametros"``)::

      {"parametros": {"numero_nodos": 15, "cupo_participantes_por_ronda_k": 5,
                      "presupuesto_ruido_por_ronda_B": 30},
       "funcion_utilidad": {"tipo": "log"},                       # opcional
       "nodos": [{"id": "N01", "coeficiente_utilidad": 8.5, "categorias": ["C11", "C17"]}, ...]}

  La utilidad de cada nodo es u_i(x) = w_i * ln(1 + x) con w_i = coeficiente_utilidad
  (o la forma elegida en "funcion_utilidad" o con --utilidad). La clave "categorias" es opcional:
  el archivo de la profesora no la trae, así que a los nodos que no la tengan se les generan
  categorías sintéticas reproducibles (semilla 36921) en memoria; el archivo no se modifica.

* **Formato extendido** (propio del proyecto; cada nodo trae su propia utilidad y un tope)::

      {"nombre": "ej01", "k": 3, "B": 20,
       "nodos": [{"id": 0, "cobertura": [1, 5, 7], "utilidad": {"tipo": "log", "a": 3.0}, "cap": 20}]}

Las claves desconocidas (p. ej. de variantes futuras: grafo, rondas, costos) se ignoran.
Todo dato inválido produce ``ValueError`` con un mensaje en español que nombra el caso y el nodo.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional

from .generador import completar_categorias
from .utilidad import Utilidad, describir, desde_dict, para_coeficiente

Caso = Dict[str, Any]

# Parámetros de las categorías sintéticas (los mismos de src/completar_categorias.py).
CATEGORIAS_UNIVERSO, CATEGORIAS_MIN, CATEGORIAS_MAX, CATEGORIAS_SEMILLA = 20, 3, 7, 36921


def cargar_caso(ruta: str, utilidad: Optional[Mapping[str, Any]] = None) -> Caso:
    """Lee un archivo JSON y devuelve el caso validado.

    Args:
        ruta: archivo ``.json``.
        utilidad: forma de u_i para el formato de la profesora; si no es None, tiene prioridad
            sobre la clave ``funcion_utilidad`` del archivo.
    """
    with open(ruta, encoding="utf-8") as fh:
        d = json.load(fh)
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    return parsear_caso(d, nombre=nombre, utilidad=utilidad)


# ----------------------------------------------------------------------------- ayudas de validación
def _exigir(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _es_entero(v: Any) -> bool:
    """Entero de JSON. Se excluye bool porque en Python True es un int."""
    return isinstance(v, int) and not isinstance(v, bool)


def _es_numero(v: Any) -> bool:
    """Número real finito (int o float), sin bool, NaN ni infinito."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _validar_k_B(ctx: str, k: Any, B: Any, N: int) -> None:
    _exigir(_es_entero(k) and 1 <= k <= N, f"{ctx}: se exige 1 <= k <= N (k={k}, N={N})")
    _exigir(_es_entero(B) and B >= 0, f"{ctx}: B debe ser un entero >= 0 (B={B})")


def _validar_ids(ctx: str, ids: List[Any]) -> None:
    _exigir(all(isinstance(i, str) or _es_entero(i) for i in ids),
            f"{ctx}: cada 'id' debe ser un texto (p. ej. \"N01\") o un entero")
    _exigir(len(set(map(str, ids))) == len(ids), f"{ctx}: hay 'id' de nodos repetidos")


# ----------------------------------------------------------------------------- entrada principal
def parsear_caso(d: Any, nombre: str = "caso", utilidad: Optional[Mapping[str, Any]] = None) -> Caso:
    """Valida el diccionario del caso y construye las estructuras que usan los algoritmos.

    Returns:
        dict con: nombre, formato, N, k, B, ids, masks (bitmask de categorías por nodo),
        universo (nombre de cada bit), utils (una Utilidad por nodo), caps (topes o None),
        coef (coeficientes o None), pesos (desempate de la selección: u_i(1) - u_i(0)),
        utilidad_desc (fórmula legible) y origen_categorias (de dónde salen las categorías).
    """
    _exigir(isinstance(d, dict), f"Caso '{nombre}': el archivo debe contener un objeto JSON {{...}}")
    nombre = str(d.get("nombre", nombre))
    if "parametros" in d:
        return _formato_profesora(d, nombre, utilidad)
    return _formato_extendido(d, nombre)


def _formato_profesora(d: Mapping[str, Any], nombre: str, utilidad: Optional[Mapping[str, Any]]) -> Caso:
    ctx = f"Caso '{nombre}'"
    p = d["parametros"]
    _exigir(isinstance(p, dict), f"{ctx}: 'parametros' debe ser un objeto {{...}}")
    for clave in ("numero_nodos", "cupo_participantes_por_ronda_k", "presupuesto_ruido_por_ronda_B"):
        _exigir(clave in p, f"{ctx}: falta parametros.{clave}")
    nodos: Any = d.get("nodos")
    _exigir(isinstance(nodos, list) and len(nodos) > 0 and all(isinstance(n, dict) for n in nodos),
            f"{ctx}: 'nodos' debe ser una lista no vacía de objetos {{...}}")
    N = len(nodos)
    _exigir(p["numero_nodos"] == N, f"{ctx}: numero_nodos={p['numero_nodos']} pero la lista tiene {N} nodos")
    k, B = p["cupo_participantes_por_ronda_k"], p["presupuesto_ruido_por_ronda_B"]
    _validar_k_B(ctx, k, B, N)
    for pos, n in enumerate(nodos, start=1):
        for clave in ("id", "coeficiente_utilidad"):
            _exigir(clave in n, f"{ctx}: al nodo número {pos} le falta '{clave}'")
    ids = [n["id"] for n in nodos]
    _validar_ids(ctx, ids)
    coef = [n["coeficiente_utilidad"] for n in nodos]
    malos = [ids[i] for i, c in enumerate(coef) if not (_es_numero(c) and c > 0)]
    _exigir(not malos, f"{ctx}: coeficiente_utilidad debe ser un número > 0 (nodos {malos[:5]})")

    sin_cat = [n["id"] for n in nodos if "categorias" not in n]
    if sin_cat:
        # El archivo no trae categorías (como el de la profesora): se generan en una copia, en memoria.
        nodos = [dict(n) for n in nodos]
        completar_categorias(nodos, CATEGORIAS_UNIVERSO, CATEGORIAS_MIN, CATEGORIAS_MAX, CATEGORIAS_SEMILLA)
        origen = (f"sintéticas, generadas al leer el caso para {len(sin_cat)} de {N} nodos (semilla "
                  f"{CATEGORIAS_SEMILLA}, universo {CATEGORIAS_UNIVERSO}, entre {CATEGORIAS_MIN} y "
                  f"{CATEGORIAS_MAX} por nodo); el archivo de entrada no se modifica")
    else:
        origen = str(d.get("origen_categorias", "dadas en el archivo de entrada"))
    # Debe ser una LISTA de textos: un texto suelto ("C11") se partiría en letras y daría una f(A) falsa.
    malos = [n["id"] for n in nodos
             if not isinstance(n["categorias"], list) or not all(isinstance(c, str) for c in n["categorias"])]
    _exigir(not malos, f"{ctx}: 'categorias' debe ser una lista de textos, p. ej. [\"C01\", \"C02\"] "
                       f"(nodos {malos[:5]})")
    vacios = [n["id"] for n in nodos if not n["categorias"]]
    _exigir(not vacios, f"{ctx}: hay nodos sin categorías: {vacios[:5]}")

    universo = sorted({c for n in nodos for c in n["categorias"]})
    bit = {c: j for j, c in enumerate(universo)}
    masks = [sum(1 << bit[c] for c in set(n["categorias"])) for n in nodos]

    spec = dict(utilidad or d.get("funcion_utilidad") or {"tipo": "log"})
    try:
        utils: List[Utilidad] = [para_coeficiente(w, spec) for w in coef]
    except ValueError as err:
        raise ValueError(f"{ctx}: {err}") from None
    return {
        "nombre": nombre, "formato": "profesora", "N": N, "k": k, "B": B, "ids": ids,
        "masks": masks, "universo": universo, "utils": utils, "caps": None, "coef": coef,
        "pesos": [u.marginal(0) for u in utils], "utilidad_desc": describir(spec),
        "origen_categorias": origen, "categorias": [list(n["categorias"]) for n in nodos],
    }


def _formato_extendido(d: Mapping[str, Any], nombre: str) -> Caso:
    ctx = f"Caso '{nombre}'"
    nodos: Any = d.get("nodos")
    _exigir(isinstance(nodos, list) and len(nodos) > 0 and all(isinstance(n, dict) for n in nodos),
            f"{ctx}: 'nodos' debe ser una lista no vacía de objetos {{...}}")
    N = len(nodos)
    for clave in ("k", "B"):
        _exigir(clave in d, f"{ctx}: falta el campo obligatorio '{clave}'")
    _validar_k_B(ctx, d["k"], d["B"], N)

    masks: List[int] = []
    utils: List[Utilidad] = []
    caps: List[int] = []
    hay_caps = any("cap" in n for n in nodos)
    for pos, n in enumerate(nodos):
        c = f"{ctx}, nodo en posición {pos}"
        _exigir("utilidad" in n, f"{c}: falta 'utilidad'")
        cobertura = n.get("cobertura", [])
        _exigir(isinstance(cobertura, list) and all(_es_entero(e) and e >= 0 for e in cobertura),
                f"{c}: 'cobertura' debe ser una lista de enteros >= 0")
        masks.append(sum(1 << e for e in set(cobertura)))
        try:
            u = desde_dict(n["utilidad"])
        except (ValueError, TypeError) as err:
            raise ValueError(f"{c}: {err}") from None
        # comprobación numérica de concavidad en el rango de unidades que se usará
        _exigir(u.es_concava(x_max=min(max(d["B"], 1), 64) + 1), f"{c}: la utilidad no es creciente y cóncava")
        utils.append(u)
        if "cap" in n:
            _exigir(_es_entero(n["cap"]) and n["cap"] >= 0, f"{c}: 'cap' debe ser un entero >= 0")
            caps.append(n["cap"])
        else:
            caps.append(10**9)  # sin tope efectivo
    ids = [n.get("id", pos) for pos, n in enumerate(nodos)]
    _validar_ids(ctx, ids)
    ancho = max((m.bit_length() for m in masks), default=0)
    caps_ef = caps if hay_caps else None
    # Desempate: ganancia de la primera unidad; 0 si el tope del nodo no le deja recibir nada.
    pesos = [u.marginal(0) if caps_ef is None or caps_ef[i] > 0 else 0.0 for i, u in enumerate(utils)]
    return {
        "nombre": nombre, "formato": "extendido", "N": N, "k": d["k"], "B": d["B"], "ids": ids,
        "masks": masks, "universo": [str(j) for j in range(ancho)], "utils": utils,
        "caps": caps_ef, "coef": None, "pesos": pesos, "utilidad_desc": "propia de cada nodo",
        "origen_categorias": "dadas en el archivo de entrada (campo cobertura)",
    }
