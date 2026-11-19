# Prácticas de algoritmos genéticos

Repositorio local con el código, documentación, pruebas y datos de las prácticas.

| Directorio | Contenido |
|---|---|
| `proyect_1` | Optimización de funciones con representación binaria |
| `proyect_2` | Optimización con representación real |
| `queens` | N reinas con permutaciones |
| `arbol_expresiones` | Árboles de expresión, CSV y regresión simbólica genética |

Consulta el README de cada proyecto para ejecutarlo. Los entornos `.venv` y
archivos temporales se excluyen; los CSV de ejemplo y resultados se conservan.

La [clase sobre error y estancamiento](CLASE-ERROR-Y-REGRESION-SIMBOLICA.md)
explica la referencia de la media, las métricas y el diagnóstico de los CSV.

La [guía de programación genética](FUNDAMENTOS-PROGRAMACION-GENETICA.md)
reúne teoría, código aplicado, selección, cruces, las cuatro mutaciones de los
apuntes y el funcionamiento actual del ajuste híbrido de expresiones.

## Historial

```bash
git status
git log --oneline
```

El primer commit `2076471` conserva todos los proyectos antes de modificar la
selección y la búsqueda simbólica. El siguiente commit registra las mejoras,
pruebas y comparación reproducible. Para consultar una versión anterior sin
modificar los archivos actuales:

```bash
git show 2076471:arbol_expresiones/genetico.py
```

Este repositorio está en el equipo local; no se ha publicado ni configurado un
servidor remoto. Los futuros cambios se guardan con nuevos commits.
