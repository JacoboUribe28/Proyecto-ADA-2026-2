"""Pruebas automáticas del Proyecto ADA 2026-2 · Red (solo biblioteca estándar).

Ejecutar desde la carpeta del proyecto:
    python -m unittest discover -s tests -v
"""

import copy
import itertools
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from red import __version__  # noqa: E402
from red.generador import completar_categorias  # noqa: E402
from red.io_casos import cargar_caso, parsear_caso  # noqa: E402
from red.pipeline import resolver  # noqa: E402
from red.reparto import repartir_dp, repartir_voraz  # noqa: E402
from red.seleccion import (desde_cobertura_maxima, f_cobertura, seleccion_exacta,  # noqa: E402
                           seleccion_voraz)
from red.utilidad import Log, Raiz, Saturada, Tabla, para_coeficiente  # noqa: E402
from red.verificacion import verificar  # noqa: E402

CASO_PROFESORA = os.path.join(RAIZ, "casos", "entrada_G2_red_15_nodos.json")  # tal como se recibió
# Resultado publicado en el informe (sección 7.1) y en el README.
SELECCION = ["N04", "N15", "N14", "N13", "N06"]
REPARTO = {"N04": 7, "N15": 5, "N14": 6, "N13": 5, "N06": 7}
UTILIDAD = 99.5821


def utils_aleatorias(rnd, n):
    out = []
    for _ in range(n):
        t = rnd.choice(["log", "raiz", "sat", "tabla"])
        if t == "log":
            out.append(Log(rnd.uniform(1, 9)))
        elif t == "raiz":
            out.append(Raiz(rnd.uniform(1, 9)))
        elif t == "sat":
            out.append(Saturada(rnd.uniform(5, 30), rnd.uniform(0.05, 0.5)))
        else:
            out.append(Tabla(sorted([rnd.uniform(0, 10) for _ in range(rnd.randint(1, 8))], reverse=True)))
    return out


def masks_aleatorias(rnd, N, U):
    return [sum(1 << e for e in rnd.sample(range(U), rnd.randint(1, U // 2 + 1))) for _ in range(N)]


# ------------------------------------------------------------------------------------------------ Parte 1
class TestReparto(unittest.TestCase):
    def test_voraz_igual_a_programacion_dinamica(self):  # teorema de optimalidad
        rnd = random.Random(7)
        for _ in range(300):
            n, B = rnd.randint(1, 5), rnd.randint(0, 12)
            u = utils_aleatorias(rnd, n)
            caps = [rnd.randint(0, 6) for _ in range(n)] if rnd.random() < 0.5 else None
            x, tv = repartir_voraz(u, B, caps)
            _, td = repartir_dp(u, B, caps)
            self.assertAlmostEqual(tv, td, places=7)
            self.assertLessEqual(sum(x), B)
            if caps:
                self.assertTrue(all(x[i] <= caps[i] for i in range(n)))

    def test_presupuesto_cero(self):
        self.assertEqual(repartir_voraz([Log(1), Log(2)], 0), ([0, 0], 0.0))

    def test_utilidades_crecientes_y_concavas(self):
        for u in [Log(3), Raiz(2), Saturada(10, 0.2), Tabla([5, 3, 3, 1])]:
            self.assertTrue(u.es_concava(60))
        for tipo in ("log", "raiz", "saturada"):
            u = para_coeficiente(7.5, {"tipo": tipo})
            self.assertEqual(u.valor(0), 0)
            self.assertTrue(u.es_concava(60), tipo)

    def test_utilidad_no_concava_rompe_el_voraz(self):
        """Por qué se exige concavidad: con ganancias que suben, el voraz deja de ser óptimo."""
        class Convexa(Tabla):
            def __init__(self, g):
                self.g = g
                self.acum = [0.0]
                for v in g:
                    self.acum.append(self.acum[-1] + v)
        u = [Convexa([1.0, 10.0]), Convexa([2.0, 0.0])]
        _, voraz = repartir_voraz(u, 2)
        self.assertEqual(voraz, 3.0)
        self.assertEqual(max(u[0].valor(a) + u[1].valor(2 - a) for a in range(3)), 11.0)


# ------------------------------------------------------------------------------------------------ Parte 2
class TestSeleccion(unittest.TestCase):
    def test_cota_1_menos_1_sobre_e(self):  # Nemhauser, Wolsey y Fisher (1978)
        rnd = random.Random(11)
        for _ in range(300):
            N = rnd.randint(3, 10)
            masks, k = masks_aleatorias(rnd, N, 20), rnd.randint(1, N - 1)
            _, fg = seleccion_voraz(masks, k)
            _, fo, _ = seleccion_exacta(masks, k)
            self.assertLessEqual(fg, fo)
            self.assertGreaterEqual(fg, (1 - 1 / math.e) * fo - 1e-9)

    def test_contraejemplo_voraz_no_optimo(self):
        masks, k, _ = desde_cobertura_maxima(range(1, 7), [{1, 2, 3, 4}, {1, 2, 5}, {3, 4, 6}], 2, 6)
        self.assertEqual(seleccion_voraz(masks, k), ([0, 1], 5))
        self.assertEqual(seleccion_exacta(masks, k)[:2], ([1, 2], 6))

    def test_exacto_hace_C_N_k_evaluaciones_y_es_optimo(self):  # recurrencia de Pascal
        rnd = random.Random(12)
        for _ in range(100):
            N = rnd.randint(2, 11)
            masks, k = masks_aleatorias(rnd, N, 15), rnd.randint(0, N)
            A, v, evaluaciones = seleccion_exacta(masks, k)
            self.assertEqual(evaluaciones, math.comb(N, k))
            fuerza_bruta = max(f_cobertura(masks, c) for c in itertools.combinations(range(N), k))
            self.assertEqual(v, fuerza_bruta)
            self.assertEqual((len(A), f_cobertura(masks, A)), (k, v))

    def test_voraz_cuenta_kN_menos_k_k_menos_1_sobre_2_evaluaciones(self):
        rnd = random.Random(14)
        for _ in range(50):
            N = rnd.randint(2, 30)
            masks, k = masks_aleatorias(rnd, N, 25), rnd.randint(1, N)
            traza = []
            seleccion_voraz(masks, k, traza)
            self.assertEqual(sum(len(t["candidatos"]) for t in traza), k * N - k * (k - 1) // 2)

    def test_traza_no_creciente_y_coherente(self):
        rnd = random.Random(21)
        for _ in range(100):
            masks = masks_aleatorias(rnd, 12, 30)
            traza = []
            A, fA = seleccion_voraz(masks, 5, traza)
            g = [t["ganancia"] for t in traza]
            self.assertEqual(g, sorted(g, reverse=True))  # submodularidad
            self.assertEqual(traza[-1]["acumulado"], fA)
            self.assertEqual(sum(t["nuevas"].bit_count() for t in traza), fA)

    def test_cobertura_monotona_y_submodular(self):
        rnd = random.Random(5)
        masks = masks_aleatorias(rnd, 8, 15)
        for _ in range(300):
            A = set(rnd.sample(range(8), rnd.randint(0, 4)))
            B = A | set(rnd.sample(range(8), rnd.randint(0, 4)))
            fuera = [v for v in range(8) if v not in B]
            if not fuera:
                continue
            v = rnd.choice(fuera)
            gA = f_cobertura(masks, A | {v}) - f_cobertura(masks, A)
            gB = f_cobertura(masks, B | {v}) - f_cobertura(masks, B)
            self.assertGreaterEqual(gB, 0)
            self.assertGreaterEqual(gA, gB)

    def test_reduccion_desde_cobertura_maxima(self):
        """SÍ en Cobertura Máxima <=> SÍ en la instancia construida (150 instancias)."""
        rnd = random.Random(3)
        for _ in range(150):
            U, N = rnd.randint(4, 12), rnd.randint(3, 8)
            S = [set(rnd.sample(range(U), rnd.randint(1, U))) for _ in range(N)]
            k, t = rnd.randint(1, N - 1), rnd.randint(1, U)
            si_cm = any(len(set().union(*(S[i] for i in c))) >= t for c in itertools.combinations(range(N), k))
            masks, k2, t2 = desde_cobertura_maxima(range(U), S, k, t)
            self.assertEqual(si_cm, seleccion_exacta(masks, k2)[1] >= t2)

    def test_desempate_por_peso(self):
        """Con igual ganancia gana el de mayor peso; sin pesos, el índice menor. f(A) no cambia."""
        masks = [0b0011, 0b1100, 0b0110]
        self.assertEqual(seleccion_voraz(masks, 2), ([0, 1], 4))
        self.assertEqual(seleccion_voraz(masks, 1, pesos=[1.0, 5.0, 2.0]), ([1], 2))
        self.assertEqual(seleccion_voraz(masks, 1, pesos=[3.0, 3.0, 3.0]), ([0], 2))
        with self.assertRaises(ValueError):
            seleccion_voraz(masks, 1, pesos=[1.0])

    def test_cota_con_desempate_por_peso(self):
        rnd = random.Random(13)
        for _ in range(200):
            N = rnd.randint(3, 10)
            masks, k = masks_aleatorias(rnd, N, 12), rnd.randint(1, N)
            pesos = [rnd.choice([1.0, 2.0, 3.0]) for _ in range(N)]
            A, fg = seleccion_voraz(masks, k, pesos=pesos)
            fo = seleccion_exacta(masks, k)[1]
            self.assertEqual((len(set(A)), f_cobertura(masks, A)), (k, fg))
            self.assertGreaterEqual(fg, (1 - 1 / math.e) * fo - 1e-9)

    def test_k_invalido(self):
        for k in (-1, 4):
            with self.assertRaises(ValueError):
                seleccion_voraz([1, 2, 3], k)
            with self.assertRaises(ValueError):
                seleccion_exacta([1, 2, 3], k)


# ------------------------------------------------------------------------------------------------ Entrada
class TestFormatoProfesora(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CASO_PROFESORA, encoding="utf-8") as fh:
            cls.base = json.load(fh)

    def rechaza(self, modificar, fragmento, base=None):
        d = copy.deepcopy(self.base if base is None else base)
        modificar(d)
        with self.assertRaises(ValueError) as cm:
            parsear_caso(d, "prueba")
        self.assertIn(fragmento, str(cm.exception))

    def test_valido_y_claves_desconocidas_ignoradas(self):
        d = copy.deepcopy(self.base)
        d["numero_rondas"] = 4
        caso = parsear_caso(d, "prueba")
        self.assertEqual((caso["N"], caso["k"], caso["B"], caso["formato"]), (15, 5, 30, "profesora"))

    def test_parametros(self):
        p = "parametros"
        self.rechaza(lambda d: d[p].__setitem__("cupo_participantes_por_ronda_k", 16), "1 <= k <= N")
        self.rechaza(lambda d: d[p].__setitem__("cupo_participantes_por_ronda_k", 0), "1 <= k <= N")
        d = copy.deepcopy(self.base)
        d[p]["cupo_participantes_por_ronda_k"] = 15  # k = N es válido: participan todos
        res, _, _ = resolver(parsear_caso(d, "todos"), repeticiones=1)
        self.assertEqual((len(res["seleccion"]), res["restricciones_ok"]), (15, True))
        self.rechaza(lambda d: d[p].__setitem__("presupuesto_ruido_por_ronda_B", -1), "B debe ser un entero")
        self.rechaza(lambda d: d[p].__setitem__("presupuesto_ruido_por_ronda_B", True), "B debe ser un entero")
        self.rechaza(lambda d: d[p].__setitem__("numero_nodos", 14), "numero_nodos=14")
        self.rechaza(lambda d: d[p].pop("presupuesto_ruido_por_ronda_B"), "falta parametros.presupuesto")

    def test_nodos(self):
        self.rechaza(lambda d: d.__setitem__("nodos", {"a": 1}), "lista no vacía")
        self.rechaza(lambda d: d["nodos"][1].__setitem__("id", "N01"), "repetidos")
        self.rechaza(lambda d: d["nodos"][0].pop("id"), "le falta 'id'")
        self.rechaza(lambda d: d["nodos"][0].__setitem__("coeficiente_utilidad", "ocho"), "número > 0")
        self.rechaza(lambda d: d["nodos"][0].__setitem__("coeficiente_utilidad", 0), "número > 0")

    def test_categorias(self):
        con = copy.deepcopy(self.base)
        completar_categorias(con["nodos"])
        self.rechaza(lambda d: d["nodos"][0].__setitem__("categorias", "K01"), "lista de textos", con)
        self.rechaza(lambda d: d["nodos"][0].__setitem__("categorias", ["K01", 5]), "lista de textos", con)
        self.rechaza(lambda d: d["nodos"][0].__setitem__("categorias", []), "sin categorías", con)

    def test_categorias_faltantes_se_generan_en_memoria(self):
        """El archivo de la profesora no trae categorías: se generan al leerlo, sin tocar el archivo."""
        with open(CASO_PROFESORA, "rb") as fh:
            antes = fh.read()
        caso = cargar_caso(CASO_PROFESORA)
        self.assertIn("sintéticas", caso["origen_categorias"])
        with open(CASO_PROFESORA, "rb") as fh:
            self.assertEqual(fh.read(), antes)
        # Si un archivo ya trae categorías, se usan las suyas.
        d = copy.deepcopy(self.base)
        for n in d["nodos"]:
            n["categorias"] = ["Z1"]
        caso2 = parsear_caso(d, "con_categorias")
        self.assertEqual((caso2["universo"], caso2["origen_categorias"]), (["Z1"], "dadas en el archivo de entrada"))

    def test_utilidad(self):
        self.rechaza(lambda d: d.__setitem__("funcion_utilidad", {"tipo": "cubica"}), "desconocido")
        caso = parsear_caso(self.base, "x", utilidad={"tipo": "raiz"})
        self.assertAlmostEqual(caso["utils"][0].valor(4), 2 * caso["coef"][0])


class TestFormatoExtendido(unittest.TestCase):
    @staticmethod
    def caso(**cambios):
        d = {"nombre": "t", "k": 1, "B": 5,
             "nodos": [{"id": 0, "cobertura": [0, 1], "utilidad": {"tipo": "log", "a": 2.0}},
                       {"id": 1, "cobertura": [1, 2], "utilidad": {"tipo": "raiz", "a": 1.0}}]}
        d.update(cambios)
        return d

    def test_valido(self):
        self.assertEqual(parsear_caso(self.caso())["formato"], "extendido")

    def test_invalidos(self):
        self.assertEqual(parsear_caso(self.caso(k=2))["k"], 2)  # k = N es válido
        for malo in [self.caso(k=3), self.caso(k=0), self.caso(B=-1), self.caso(nodos=[])]:
            with self.assertRaises(ValueError):
                parsear_caso(malo)
        d = self.caso()
        del d["B"]
        with self.assertRaisesRegex(ValueError, "falta el campo obligatorio 'B'"):
            parsear_caso(d)
        d = self.caso()
        d["nodos"][1]["id"] = 0
        with self.assertRaisesRegex(ValueError, "repetidos"):
            parsear_caso(d)
        d = self.caso()
        d["nodos"][0]["cobertura"] = [-1]
        with self.assertRaisesRegex(ValueError, "enteros >= 0"):
            parsear_caso(d)
        d = self.caso()
        d["nodos"][0]["utilidad"] = {"tipo": "tabla", "ganancias": [1, 2]}
        with self.assertRaisesRegex(ValueError, "no crecientes"):
            parsear_caso(d)


class TestCompletarCategorias(unittest.TestCase):
    def test_reproducible_en_rango_y_respeta_existentes(self):
        a = [{} for _ in range(10)]
        b = [{} for _ in range(10)]
        completar_categorias(a, semilla=36921)
        completar_categorias(b, semilla=36921)
        self.assertEqual(a, b)
        self.assertTrue(all(3 <= len(n["categorias"]) <= 7 for n in a))
        c = [{"categorias": ["X"]}] + [{} for _ in range(9)]
        self.assertEqual(completar_categorias(c, semilla=36921), 9)
        self.assertEqual(c[0]["categorias"], ["X"])
        self.assertEqual(c[1:], a[1:])  # lo que reciben los demás no depende del nodo que ya tenía

    def test_la_lectura_y_el_script_generan_las_mismas_categorias(self):
        with open(CASO_PROFESORA, encoding="utf-8") as fh:
            recibido = json.load(fh)
        completar_categorias(recibido["nodos"], semilla=36921)
        self.assertEqual(cargar_caso(CASO_PROFESORA)["categorias"], [n["categorias"] for n in recibido["nodos"]])


# ------------------------------------------------------------------------------------------------ Solución
class TestVerificacion(unittest.TestCase):
    def test_detecta_un_reparto_que_no_es_optimo(self):
        caso = cargar_caso(CASO_PROFESORA)
        res, t_sel, _ = resolver(caso, repeticiones=1)
        A = [caso["ids"].index(n) for n in res["seleccion"]]
        x = [0] * caso["N"]
        for nodo, u in res["reparto"].items():
            x[caso["ids"].index(nodo)] = u
        x[A[0]] -= 1  # se mueve una unidad del nodo de mayor peso al de menor
        x[A[-1]] += 1
        total = sum(caso["utils"][i].valor(x[i]) for i in A)
        chk, ok = verificar(caso, A, x, total, t_sel)
        self.assertFalse(ok)
        self.assertFalse(chk["ninguna transferencia de una unidad mejora el reparto"][0])

    def test_detecta_presupuesto_sin_usar(self):
        caso = cargar_caso(CASO_PROFESORA)
        A = list(range(caso["k"]))
        x = [0] * caso["N"]
        x[0] = 1
        chk, ok = verificar(caso, A, x, caso["utils"][0].valor(1))
        self.assertFalse(chk["no sobra presupuesto que algún nodo aproveche"][0])


class TestCasoProfesora(unittest.TestCase):
    def test_resultado_publicado(self):
        res, _, _ = resolver(cargar_caso(CASO_PROFESORA), repeticiones=1)
        self.assertEqual(res["seleccion"], SELECCION)
        self.assertEqual((res["f_voraz"], res["seleccion_optima"]["f_opt"]), (20, 20))
        self.assertEqual(res["seleccion_optima"]["evaluaciones"], math.comb(15, 5))
        self.assertEqual(res["reparto"], REPARTO)
        self.assertAlmostEqual(res["utilidad_total"], UTILIDAD, places=4)
        self.assertTrue(res["restricciones_ok"])
        self.assertTrue(res["reparto_optimo_dp"]["voraz_es_optimo"])

    def test_la_traza_no_cambia_las_decisiones(self):
        caso = cargar_caso(CASO_PROFESORA)
        self.assertEqual(seleccion_voraz(caso["masks"], caso["k"], None, caso["pesos"]),
                         seleccion_voraz(caso["masks"], caso["k"], [], caso["pesos"]))


# ------------------------------------------------------------------------------------------------ Programa
class TestLineaDeComandos(unittest.TestCase):
    def correr(self, *args):
        return subprocess.run([sys.executable, os.path.join(RAIZ, "src", "ejecutar_casos.py"), *args],
                              capture_output=True, text=True, cwd=RAIZ)

    def test_caso_de_la_profesora(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.correr("--salida", tmp, "--repeticiones", "1")
            self.assertEqual(r.returncode, 0, r.stderr)
            carpeta = os.path.join(tmp, "entrada_G2_red_15_nodos")
            for archivo in ("salida.json", "traza.json", "traza.md", "traza_seleccion.csv", "traza_reparto.csv"):
                self.assertTrue(os.path.exists(os.path.join(carpeta, archivo)), archivo)
            for archivo in ("resumen.md", "resumen.csv"):
                self.assertTrue(os.path.exists(os.path.join(tmp, archivo)), archivo)
            with open(os.path.join(carpeta, "salida.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["version_codigo"], __version__)

    def test_un_caso_malo_no_detiene_a_los_demas(self):
        with tempfile.TemporaryDirectory() as tmp:
            entradas = os.path.join(tmp, "casos")
            os.makedirs(entradas)
            with open(CASO_PROFESORA, encoding="utf-8") as fh:
                d = json.load(fh)
            with open(os.path.join(entradas, "b_bueno.json"), "w", encoding="utf-8") as fh:
                json.dump(d, fh)
            d["parametros"]["cupo_participantes_por_ronda_k"] = 16
            with open(os.path.join(entradas, "a_malo.json"), "w", encoding="utf-8") as fh:
                json.dump(d, fh)
            salida = os.path.join(tmp, "out")
            r = self.correr("--casos", entradas, "--salida", salida, "--repeticiones", "1")
            self.assertEqual(r.returncode, 1)
            self.assertIn("1 <= k <= N", r.stderr)
            self.assertTrue(os.path.exists(os.path.join(salida, "b_bueno", "salida.json")))
            with open(os.path.join(salida, "resumen.md"), encoding="utf-8") as fh:
                self.assertIn("no se pudieron ejecutar", fh.read())

    def test_solo_casos_malos_no_escribe_resumen(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "malo.json")
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write("{ esto no es JSON")
            r = self.correr("--casos", ruta, "--salida", os.path.join(tmp, "out"))
            self.assertEqual(r.returncode, 1)
            self.assertFalse(os.path.exists(os.path.join(tmp, "out", "resumen.md")))

    def test_completar_categorias_desde_la_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = os.path.join(tmp, "c.json")
            r = subprocess.run([sys.executable, os.path.join(RAIZ, "src", "completar_categorias.py"),
                                CASO_PROFESORA, "-o", salida], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(salida, encoding="utf-8") as fh:
                self.assertIn("origen_categorias", json.load(fh))


class TestVersion(unittest.TestCase):
    def test_version_unica(self):
        """VERSION, el código, pyproject.toml y cada salida deben decir la misma versión."""
        with open(os.path.join(RAIZ, "VERSION"), encoding="utf-8") as fh:
            version = fh.read().strip()
        self.assertEqual(__version__, version)
        with open(os.path.join(RAIZ, "pyproject.toml"), encoding="utf-8") as fh:
            self.assertIn(f'version = "{version}"', fh.read())
        res, _, _ = resolver(cargar_caso(CASO_PROFESORA), repeticiones=1)
        self.assertEqual(res["version_codigo"], version)


if __name__ == "__main__":
    unittest.main()
