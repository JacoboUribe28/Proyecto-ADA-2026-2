# Traza del caso «entrada_G2_red_15_nodos»

*Proyecto ADA 2026-2 · Jacobo Uribe Montoya (36921) · versión 1.1.0*

| Dato | Valor |
|---|---|
| Nodos (N), cupo (k), presupuesto (B) | 15, 5, 30 |
| Utilidad individual u_i(x) | w_i * ln(1 + x) |
| Categorías de datos | sintéticas, generadas al leer el caso para 15 de 15 nodos (semilla 36921, universo 20, entre 3 y 7 por nodo); el archivo de entrada no se modifica |
| Nodos elegidos | N04, N15, N14, N13, N06 |
| Categorías cubiertas f(A) | 20 de 20 |
| Óptimo exacto f* | 20 (razón 1.0000; mínimo garantizado 0.6321) |
| Utilidad total del reparto | 99.5821 |
| Tiempo (selección + reparto) | 0.018 ms, mediana de 5 |
| ¿Cumple todo? | Sí |

## A. ¿Quiénes participan? Selección voraz

En cada paso se agrega el nodo que aporta más categorías **nuevas** (Δ). Δ se recalcula en cada paso, porque lo ya cubierto deja de contar. Empates en Δ: gana el nodo que más aprovecha su primera unidad de presupuesto (mayor u_i(1) − u_i(0), es decir, mayor coeficiente); si también empatan, el que aparece primero en el archivo.

| Paso | Elegido | Δ | Categorías nuevas | f(A) acumulada | Segundo mejor (Δ) |
|---|---|---|---|---|---|
| 1 | N04 | 7 | K01, K02, K06, K09, K12, K13, K14 | 7 | N06 (7) |
| 2 | N15 | 6 | K03, K08, K10, K16, K17, K19 | 13 | N13 (6) |
| 3 | N14 | 4 | K04, K07, K11, K15 | 17 | N03 (3) |
| 4 | N13 | 2 | K05, K20 | 19 | N03 (1) |
| 5 | N06 | 1 | K18 | 20 | N05 (1) |

## B. ¿Cuánto recibe cada uno? Reparto voraz con montículo

Cada unidad de presupuesto va al nodo elegido cuya siguiente unidad aporta más (g). Como u_i es cóncava, las ganancias de la columna g nunca suben.

| Unidad | Para | g (ganancia) | Unidades del nodo |
|---|---|---|---|
| 1 | N04 | 8.3178 | 1 |
| 2 | N06 | 7.6939 | 1 |
| 3 | N14 | 7.0008 | 1 |
| 4 | N15 | 6.5849 | 1 |
| 5 | N13 | 5.7531 | 1 |
| 6 | N04 | 4.8656 | 2 |
| 7 | N06 | 4.5007 | 2 |
| 8 | N14 | 4.0952 | 2 |
| 9 | N15 | 3.8519 | 2 |
| 10 | N04 | 3.4522 | 3 |
| 11 | N13 | 3.3654 | 2 |
| 12 | N06 | 3.1933 | 3 |
| 13 | N14 | 2.9056 | 3 |
| 14 | N15 | 2.7330 | 3 |
| 15 | N04 | 2.6777 | 4 |
| 16 | N06 | 2.4769 | 4 |
| 17 | N13 | 2.3878 | 3 |
| 18 | N14 | 2.2537 | 4 |
| 19 | N04 | 2.1879 | 5 |
| 20 | N15 | 2.1199 | 4 |
| 21 | N06 | 2.0238 | 5 |
| 22 | N13 | 1.8521 | 4 |
| 23 | N04 | 1.8498 | 6 |
| 24 | N14 | 1.8414 | 5 |
| 25 | N15 | 1.7321 | 5 |
| 26 | N06 | 1.7111 | 6 |
| 27 | N04 | 1.6024 | 7 |
| 28 | N14 | 1.5569 | 6 |
| 29 | N13 | 1.5133 | 5 |
| 30 | N06 | 1.4822 | 7 |

| Nodo | Unidades recibidas | Utilidad u_i(x_i) |
|---|---|---|
| N04 | 7 | 24.9533 |
| N15 | 5 | 17.0217 |
| N14 | 6 | 19.6537 |
| N13 | 5 | 14.8716 |
| N06 | 7 | 23.0818 |

## C. ¿Se cumplen las restricciones?

| # | Comprobación | ¿Cumple? | Detalle |
|---|---|---|---|
| 1 | \|A\| = k | Sí | \|A\| = 5, k = 5 |
| 2 | nodos de A válidos y sin repetir | Sí |  |
| 3 | f(A) de la traza = f(A) recalculada | Sí | 20 vs 20 |
| 4 | ganancias de la selección no crecientes | Sí | consecuencia de la submodularidad |
| 5 | garantía f(voraz) >= (1 - 1/e) f(óptimo) | Sí | 20 >= 12.6424 |
| 6 | x_i entero >= 0 | Sí |  |
| 7 | x_i = 0 si el nodo no participa | Sí |  |
| 8 | suma de x_i <= B | Sí | suma = 30, B = 30 |
| 9 | utilidad recalculada coincide | Sí | 99.582111 vs 99.582111 |
| 10 | ganancias del reparto no crecientes | Sí | consecuencia de la concavidad |
| 11 | ninguna transferencia de una unidad mejora el reparto | Sí | mejor cambio = 0.00e+00 |
| 12 | no sobra presupuesto que algún nodo aproveche | Sí | sobran 0 unidades |
