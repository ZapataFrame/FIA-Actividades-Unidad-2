"""Métricas de error para comparar puntos observados con una función."""

import math


def calcular_metricas(observados, predichos):
    """Calcula MSE, NMSE, RMSE y R² sobre dos secuencias de igual tamaño.

    NMSE se normaliza con la varianza de los valores observados. Si todos los
    observados son iguales, NMSE y R² se devuelven como ``nan`` porque sus
    denominadores son cero, incluso cuando el ajuste es perfecto.
    """
    if len(observados) != len(predichos) or not observados:
        raise ValueError("Se necesitan secuencias no vacías y del mismo tamaño.")
    if not all(math.isfinite(v) for v in (*observados, *predichos)):
        raise ValueError("Las métricas requieren valores reales finitos.")
    errores = [(real - estimado) ** 2 for real, estimado in zip(observados, predichos)]
    mse = sum(errores) / len(errores)
    rmse = math.sqrt(mse)
    media = sum(observados) / len(observados)
    suma_total = sum((real - media) ** 2 for real in observados)
    suma_error = sum(errores)
    if suma_total == 0:
        r2 = math.nan
        nmse = math.nan
    else:
        r2 = 1.0 - suma_error / suma_total
        nmse = mse / (suma_total / len(observados))
    return {"mse": mse, "nmse": nmse, "rmse": rmse, "r2": r2}
