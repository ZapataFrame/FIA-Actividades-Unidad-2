"""Simplificación y ajuste opcional de salida para regresión simbólica.

No adivina la función objetivo: sólo reduce ramas constantes y calcula dos
coeficientes a,b para a*f(x)+b por mínimos cuadrados sobre los datos de ajuste.
"""
import math
from algoritmo import Nodo, ExpressionEvaluator, ExpresionError


def constante(valor):
    return Nodo(format(valor,'.17g'),tipo='numero')


def simplificar(raiz):
    if raiz.es_hoja:
        return raiz
    izq = simplificar(raiz.izquierdo) if raiz.izquierdo else None
    der = simplificar(raiz.derecho) if raiz.derecho else None
    nuevo = Nodo(raiz.valor,izq,der,raiz.tipo)
    # Sólo se colapsan ramas numéricas evaluables. No se usa x/x=1 ni
    # 0*exp(x)=0: esas reglas ocultarían restricciones de dominio.
    if izq is not None and izq.tipo=='numero' and (der is None or der.tipo=='numero'):
        try:
            return constante(ExpressionEvaluator().evaluate(nuevo))
        except (ExpresionError, OverflowError):
            return nuevo
    if der is not None and der.tipo=='numero':
        valor=float(der.valor)
        if raiz.valor in ('+','-') and valor==0:
            return izq
        if raiz.valor in ('*','/') and valor==1:
            return izq
    if izq is not None and izq.tipo=='numero':
        if raiz.valor=='+' and float(izq.valor)==0:
            return der
        if raiz.valor=='*' and float(izq.valor)==1:
            return der
    return nuevo


def nucleo_lineal(raiz):
    """Retira envolturas lineales existentes para no acumular a*(b*f+c)+d."""
    while raiz.derecho is not None:
        a,b=raiz.izquierdo,raiz.derecho
        if raiz.valor in ('+','-','*'):
            if a.tipo=='numero' and b.tipo!='numero':
                raiz=b
                continue
            if b.tipo=='numero' and a.tipo!='numero':
                raiz=a
                continue
        if raiz.valor=='/' and b.tipo=='numero' and float(b.valor)!=0:
            raiz=a
            continue
        break
    return raiz


def ajustar_salida(raiz, xs, ys, evaluador, altura_maxima, cancelar=None):
    nucleo=nucleo_lineal(raiz)
    pred=evaluador.predecir(nucleo,xs,cancelar,altura_maxima)
    n=len(ys)
    media_y=math.fsum(y/n for y in ys)
    media_f=math.fsum(y/n for y in pred)
    df=[v-media_f for v in pred]
    escala=max(abs(v) for v in df)
    if escala==0:
        return constante(media_y)
    # Normalizar df evita elevar al cuadrado valores muy grandes.
    normal=[v/escala for v in df]
    denominador=math.fsum(v*v for v in normal)
    a=math.fsum(v*(y-media_y) for v,y in zip(normal,ys))/denominador/escala
    b=media_y-a*media_f
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError('Ajuste lineal no finito.')
    resultado=nucleo if a==1 else Nodo('*',constante(a),nucleo)
    if a==0:
        return constante(b)
    if b!=0:
        resultado=Nodo('+',resultado,constante(b))
    return simplificar(resultado)
