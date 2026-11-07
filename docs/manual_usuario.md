# Manual de usuario · Proyecto ADA 2026-2 (Red)

> **Autor:** Jacobo Uribe Montoya · **Código:** 36921 · **Versión:** 1.1.0 (archivo `VERSION`)
> Análisis y Diseño de Algoritmos 2026-2 · Universidad de Caldas

Este manual explica cómo **usar** el programa sin entrar en el código. Cómo funciona por dentro está en el [manual técnico](manual_tecnico.md).

**Índice:** [1 Qué hace](#1-qué-hace) · [2 Antes de empezar](#2-antes-de-empezar) · [3 Primer uso](#3-primer-uso-en-tres-pasos) · [4 Leer los resultados](#4-cómo-leer-los-resultados) · [5 Tutorial](#5-tutorial-un-caso-de-tres-nodos) · [6 Casos de la profesora](#6-casos-de-la-profesora) · [7 Caso propio](#7-escribir-un-caso-propio) · [8 Opciones](#8-opciones) · [9 Problemas](#9-solución-de-problemas) · [10 Preguntas](#10-preguntas-frecuentes) · [11 Chuleta](#11-chuleta-de-comandos)

---

## 1. Qué hace

Una red de N nodos entrena un modelo en conjunto, y en cada ronda hay que decidir dos cosas:

- **Quiénes participan.** Solo caben k nodos. Cada nodo aporta ciertas **categorías de datos** (K01, K07…) y unas se repiten entre nodos. El programa elige los k nodos que juntos cubren **más categorías distintas**.
- **Cuánto presupuesto recibe cada uno.** Hay B unidades de presupuesto de ruido, y cada unidad extra le sirve un poco menos a un mismo nodo. El programa las reparte para obtener la **mayor utilidad total**.

Para cada caso entrega la decisión, el tiempo, una **traza** paso a paso y la **verificación** de 12 condiciones.

## 2. Antes de empezar

| Necesito | Para qué | Cómo comprobarlo |
|---|---|---|
| Python 3.10 o superior | Todo | `python --version` |
| Nada más | Ejecutar casos y pruebas | Solo usa la biblioteca estándar |
| `matplotlib` y `numpy` (opcional) | Gráficas de tiempo | `pip install -r requirements.txt` |

**Obtener el proyecto.** En GitHub: **Code → Download ZIP**, y descomprimir. Después, abrir una terminal **dentro de la carpeta del proyecto** (la que tiene `README.md`, `src/` y `casos/`). En Windows: abrir la carpeta, escribir `cmd` en la barra de direcciones y presionar Enter. Si `python` no se reconoce, usar `py` en todos los comandos.

## 3. Primer uso en tres pasos

**Paso 1 · Comprobar que todo funciona**

```bash
python -m unittest discover -s tests
```

Debe terminar con `Ran 33 tests … OK`.

**Paso 2 · Ejecutar el caso de la profesora**

```bash
python src/ejecutar_casos.py
```

```
Proyecto ADA 2026-2 v1.1.0 · Jacobo Uribe Montoya (36921)
  entrada_G2_red_15_nodos: N=15 k=5 B=30 | f(A)=20 | utilidad=99.5821 | 0.018 ms | cumple
Resultados en .../resultados
```

El tiempo cambia según el equipo. La palabra que importa es **cumple**.

**Paso 3 · Ver los resultados.** Abrir `resultados/resumen.md` y `resultados/entrada_G2_red_15_nodos/traza.md`. En GitHub o en VS Code se ven como tablas.

## 4. Cómo leer los resultados

```
resultados/
├── resumen.md · resumen.csv          ← una fila por caso
└── entrada_G2_red_15_nodos/
    ├── traza.md                      ← para leer y explicar
    ├── salida.json                   ← resultado, tiempo y verificación
    ├── traza.json                    ← la traza completa, para otros programas
    ├── traza_seleccion.csv           ← selección paso a paso (Excel)
    └── traza_reparto.csv             ← reparto unidad por unidad (Excel)
```

`traza.md` empieza con una **ficha** del caso y sigue con tres partes:

| Parte | Responde | En el caso de la profesora |
|---|---|---|
| **A · Selección** | ¿Quiénes participan? Cada fila es un nodo elegido; **Δ** = categorías **nuevas** que aporta | N04 (7), N15 (6), N14 (4), N13 (2), N06 (1): 20 de 20 categorías, igual al óptimo |
| **B · Reparto** | ¿Cuánto recibe cada uno? Cada fila es una unidad; **g** = lo que aporta | N04 = 7, N15 = 5, N14 = 6, N13 = 5, N06 = 7; utilidad 99.5821 |
| **C · Verificación** | ¿Se cumple todo? 12 comprobaciones | Las 12 dicen **Sí** |

Las columnas Δ y g nunca suben de una fila a la siguiente: cada nodo o unidad nueva aporta igual o menos que la anterior. Es lo esperado.

En `resumen.md`, **f óptimo** solo aparece en casos pequeños: si hay más de 500 000 combinaciones posibles, no se calcula y queda vacío.

## 5. Tutorial: un caso de tres nodos

`casos/ejemplos/ej00_tres_nodos.json`:

| Nodo | Categorías | Coeficiente |
|---|---|---|
| N1 | K1, K2, K3, K4 | 4.0 |
| N2 | K1, K2, K5 | 6.0 |
| N3 | K3, K4, K6 | 5.0 |

Con k = 2 y B = 6.

**1 · Ejecutar en una carpeta de prueba** (así no se toca `resultados/`):

```bash
python src/ejecutar_casos.py --casos casos/ejemplos/ej00_tres_nodos.json --salida resultados_tutorial
```

```
  ej00_tres_nodos: N=3 k=2 B=6 | f(A)=5 | utilidad=14.0511 | 0.006 ms | cumple
```

**2 · Selección** (`resultados_tutorial/ej00_tres_nodos/traza.md`, parte A):

| Paso | Elegido | Δ | Categorías nuevas | f(A) acumulada | Segundo mejor (Δ) |
|---|---|---|---|---|---|
| 1 | N1 | 4 | K1, K2, K3, K4 | 4 | N2 (3) |
| 2 | N2 | 1 | K5 | 5 | N3 (1) |

N1 aporta más al principio. En el paso 2, N2 y N3 aportan solo una categoría nueva cada uno; empatan y gana N2 porque su coeficiente es mayor (6.0 frente a 5.0): a igual cobertura, se prefiere el nodo que más aprovecha el presupuesto.

**3 · ¿Es lo mejor?** La ficha dice `Óptimo exacto f* = 6 (razón 0.8333)`: N2 y N3 juntos cubren las 6. El método rápido **no siempre** encuentra el óptimo, pero garantiza al menos el 63 %; aquí logró el 83 %.

**4 · Reparto** (parte B): las 6 unidades quedan N1 = 2 y N2 = 4 (utilidad 14.0511). N2 recibe más porque su coeficiente es mayor (6.0 frente a 4.0).

## 6. Casos de la profesora

1. Copiar el `.json` **tal como se recibió** en `casos/`. No hay que editarlo.
2. Ejecutar `python src/ejecutar_casos.py`. Se procesan todos los `.json` de `casos/` (no entra en `casos/ejemplos/`).

Si el caso **no trae categorías** (como `entrada_G2_red_15_nodos.json`), el programa las genera al leerlo, siempre iguales (semilla 36921, 20 categorías, entre 3 y 7 por nodo), sin modificar el archivo. La traza lo dice en la fila «Categorías de datos». Si el caso sí trae `categorias`, se usan las suyas.

Para ver esas categorías en un archivo (opcional):

```bash
python src/completar_categorias.py casos/entrada_G2_red_15_nodos.json -o con_categorias.json
```

Si un caso tiene un error, se informa con `[ERROR]`, **los demás siguen** y el programa termina con código 1.

## 7. Escribir un caso propio

```json
{
  "parametros": {
    "numero_nodos": 3,
    "cupo_participantes_por_ronda_k": 2,
    "presupuesto_ruido_por_ronda_B": 6
  },
  "nodos": [
    {"id": "N1", "coeficiente_utilidad": 4.0, "categorias": ["K1", "K2", "K3", "K4"]},
    {"id": "N2", "coeficiente_utilidad": 6.0, "categorias": ["K1", "K2", "K5"]},
    {"id": "N3", "coeficiente_utilidad": 5.0, "categorias": ["K3", "K4", "K6"]}
  ]
}
```

| Campo | Regla |
|---|---|
| `numero_nodos` | Igual a la cantidad de nodos |
| `cupo_participantes_por_ronda_k` | Entero, al menos 1 y **menor** que el número de nodos |
| `presupuesto_ruido_por_ronda_B` | Entero, 0 o más |
| `id` | Texto o entero, sin repetir |
| `coeficiente_utilidad` | Número mayor que 0 |
| `categorias` | **Lista** de textos, no vacía: `["K1"]`, no `"K1"` |
| `funcion_utilidad` (opcional) | `{"tipo": "log"}` (por defecto), `"raiz"` o `"saturada"` |

El nombre del archivo es el nombre del caso. Las claves que el programa no conoce se ignoran. Existe también un formato extendido, en el que cada nodo trae su propia utilidad y un tope (ver el manual técnico, §7).

## 8. Opciones

### `python src/ejecutar_casos.py`

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--casos A B …` | Archivos `.json` o carpetas a ejecutar (no entra en subcarpetas como `casos/ejemplos/`) | `casos` |
| `--salida CARPETA` | Dónde guardar los resultados | `resultados` |
| `--repeticiones N` | Veces que se mide el tiempo (se reporta la mediana) | 5 |
| `--utilidad log·raiz·saturada` | Forma de u_i para todos los casos de la profesora | `log` |
| `--sin-optimo` | No calcular los óptimos exactos (más rápido en casos grandes) | — |
| `--help` | Ver todas las opciones | — |

**Importante:** cada ejecución reescribe `resumen.md` de la carpeta de salida. Para pruebas, usar `--salida resultados_algo`. Las carpetas `resultados_*` no se suben a Git.

### `python src/completar_categorias.py`

| Opción | Por defecto | Qué hace |
|---|---|---|
| `-o ARCHIVO` | (obligatoria) | Archivo nuevo con categorías (opcional: el programa ya las genera al leer el caso) |
| `--universo` | 20 | Cuántas categorías distintas existen |
| `--min` · `--max` | 3 · 7 | Categorías por nodo |
| `--semilla` | 36921 | Misma semilla, mismas categorías |
| `--reemplazar` | — | Reemplazar las categorías que ya existan |

## 9. Solución de problemas

| Mensaje o síntoma | Qué pasa | Qué hacer |
|---|---|---|
| `python` no se reconoce | Python no está en el PATH (Windows) | Usar `py`, o reinstalar marcando *Add Python to PATH* |
| `can't open file '…ejecutar_casos.py'` | La terminal no está en la carpeta del proyecto | Entrar a la carpeta que tiene `src/` y `casos/` |
| `No se encontraron casos .json` | La carpeta no tiene `.json` | Revisar la ruta de `--casos` |
| `'categorias' debe ser una lista de textos` | Se escribió `"K1"` en vez de `["K1"]` | Usar corchetes |
| `se exige 1 <= k <= N (k=16, N=15)` | El cupo es mayor que el número de nodos, o es 0 | Corregir `cupo_participantes_por_ronda_k` |
| `B debe ser un entero >= 0` | Presupuesto negativo, decimal o `true` | Usar un entero, p. ej. `30` |
| `numero_nodos=… pero la lista tiene … nodos` | El parámetro no coincide | Corregir `numero_nodos` |
| `hay 'id' de nodos repetidos` | Dos nodos con el mismo id | Cambiar uno |
| `coeficiente_utilidad debe ser un número > 0` | 0, negativo o texto | Usar un número positivo |
| `Expecting value: line …` | El JSON está mal escrito | Revisar comas, llaves y comillas |
| `Ningún caso pudo ejecutarse` | Todos los casos tenían error | Leer los `[ERROR]` de arriba |
| `NO CUMPLE` en la terminal | Falló una verificación | Ver la parte C de `traza.md` |
| `ModuleNotFoundError: matplotlib` | Falta la librería de gráficas | `pip install -r requirements.txt` |

## 10. Preguntas frecuentes

- **¿Por qué cambia el tiempo?** Depende del equipo; por eso se reporta la mediana. Los nodos y el reparto siempre salen iguales.
- **¿Siempre encuentra la mejor selección?** No siempre (§5), pero garantiza al menos el 63 % del óptimo; en el caso de la profesora coincide con el óptimo. El reparto sí es siempre el mejor posible.
- **¿Hay que tocar el código para un caso nuevo?** No: basta con el `.json`.
- **¿Qué pasa si hay empate?** Si dos nodos aportan las mismas categorías nuevas, gana el de mayor coeficiente; si también empatan, el que aparece primero en el archivo.
- **¿Por qué las categorías son sintéticas?** La entrada de la profesora no las trae. El programa las genera con la semilla 36921 al leer el caso y la salida lo declara en `origen_categorias`.

## 11. Chuleta de comandos

| Quiero… | Comando |
|---|---|
| Probar la instalación | `python -m unittest discover -s tests` |
| Ejecutar los casos de la profesora | `python src/ejecutar_casos.py` |
| Ejecutar los ejemplos | `python src/ejecutar_casos.py --casos casos/ejemplos --salida resultados_ejemplos` |
| Un caso sin tocar `resultados/` | `python src/ejecutar_casos.py --casos mi_caso.json --salida resultados_prueba` |
| Otra utilidad | `python src/ejecutar_casos.py --utilidad raiz` |
| Ver las categorías sintéticas en un archivo | `python src/completar_categorias.py entrada.json -o salida.json` |
| Gráficas de tiempo | `python Informe/code/experimentos.py` |
| Leer el informe | Abrir `Informe/main.pdf` |
| Recompilar el informe | `cd Informe` y `pdflatex main.tex` (dos veces) |
| Regenerar los ejemplos | `python src/generar_casos_ejemplo.py` |
