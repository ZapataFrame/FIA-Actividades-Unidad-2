"""Referencias de ajuste para distinguir progreso real de predecir la media.

La media es el mejor predictor constante bajo MSE. No es una nueva función
objetivo ni se introduce como solución correcta de los datos.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Diagnostico:
    cantidad: int
    media_y: float
    mse_media: float
    pendiente_recta: float
    intercepto_recta: float
    mse_recta: float
    cruces_media: int

    def explicar_ajuste(self, mse):
        if not math.isfinite(mse):
            return 'No hay un ajuste evaluable en todos los puntos.'
        if self.mse_media == 0:
            return 'Y es constante: compara MSE/RMSE con cero; R² y NMSE no están definidos.'
        mejora=1-mse/self.mse_media
        texto=f'Mejora frente a predecir la media: {mejora:.1%} (equivale a R²).'
        if mejora < 0:
            texto += ' El resultado es peor que la referencia constante.'
        elif mejora < .1:
            texto += ' Ajuste cercano a la media: aún no explica la forma de los datos.'
        return texto


def diagnosticar(puntos):
    pares=sorted((float(x),float(y)) for x,y in puntos)
    if len(pares)<2 or not all(math.isfinite(v) for par in pares for v in par):
        raise ValueError('Se requieren al menos dos puntos finitos para diagnosticar.')
    xs,ys=zip(*pares)
    n=len(pares)
    media_x=math.fsum(x/n for x in xs)
    media_y=math.fsum(y/n for y in ys)
    dy=[y-media_y for y in ys]
    dx=[x-media_x for x in xs]
    total_x=math.fsum(v*v for v in dx)
    a=math.fsum(u*v for u,v in zip(dx,dy))/total_x if total_x else 0.
    b=media_y-a*media_x
    mse_media=math.fsum(v*v/n for v in dy)
    mse_recta=math.fsum((y-(a*x+b))**2/n for x,y in pares)
    if not all(math.isfinite(v) for v in (media_y,mse_media,a,b,mse_recta)):
        raise ValueError('La escala de los datos desborda las referencias numéricas; revisa sus unidades.')
    cruces=sum(a*b<0 for a,b in zip(dy,dy[1:]))
    return Diagnostico(n,media_y,mse_media,a,b,mse_recta,cruces)
