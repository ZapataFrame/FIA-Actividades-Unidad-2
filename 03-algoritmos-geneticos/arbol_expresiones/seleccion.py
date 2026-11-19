"""Selección de padres para una pérdida que se minimiza. No depende de Qt."""

import math

METODOS = {'torneo': 'Torneo', 'ruleta': 'Ruleta', 'rango': 'Rango', 'uniforme': 'Aleatoria uniforme'}


def seleccionar(poblacion, azar, metodo='torneo', torneo=3, cancelar=None):
    if not poblacion:
        raise ValueError('La población no puede estar vacía.')
    if metodo not in METODOS:
        raise ValueError('Método de selección desconocido.')
    if metodo == 'torneo':
        # Con reposición: el tamaño del torneo no tiene tope de población.
        mejor=None
        for _ in range(torneo):
            if cancelar is not None and cancelar():
                raise InterruptedError('Selección cancelada.')
            elegido=poblacion[math.floor(azar.random()*len(poblacion))]
            if mejor is None or elegido.orden<mejor.orden:
                mejor=elegido
        return mejor
    if metodo == 'uniforme':
        return azar.choice(poblacion)
    validos = [i for i in poblacion if i.valido]
    if not validos:
        return azar.choice(poblacion)
    if metodo == 'ruleta':
        # Pérdidas pequeñas tienen mayor peso. Cero no causa una división por
        # cero y los inválidos no participan mientras haya soluciones válidas.
        positivas = sorted(i.perdida for i in validos if i.perdida > 0)
        escala = positivas[len(positivas)//2] if positivas else 1.
        pesos = [1/(1+i.perdida/escala) for i in validos]
    elif metodo == 'rango':
        validos = sorted(validos,key=lambda i:i.orden)
        n = len(validos)
        grupos = {orden: n-j for j,orden in enumerate(sorted({i.orden for i in validos}))}
        pesos = [grupos[i.orden] for i in validos]
    else:
        raise ValueError('Método de selección desconocido.')
    if not math.isfinite(sum(pesos)) or sum(pesos) == 0:
        return azar.choice(validos)
    return azar.choices(validos,weights=pesos,k=1)[0]
