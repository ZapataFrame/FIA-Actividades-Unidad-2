"""Regresión simbólica con programación genética, sin dependencias de Qt.

Cada individuo es un árbol inmutable. La población evoluciona por torneo,
cruce de subárboles, mutaciones y elitismo. El ajuste lineal de salida es opcional;
no introduce la función objetivo en la población inicial.
"""

from dataclasses import dataclass
import math
import random

from algoritmo import (Nodo, OPERACIONES, ExpresionError, ExpressionEvaluator,
                       texto_inorder, validar_arbol)
from biblioteca import altura_arbol
from metricas import calcular_metricas
from seleccion import seleccionar, METODOS
from mejoras_geneticas import simplificar, ajustar_salida

# Un conjunto reducido aumenta la probabilidad de obtener funciones evaluables.
OPERACIONES_BASE = tuple(o for o in OPERACIONES if o.simbolo in ('+', '-', '*', '/', 'sin', 'cos'))
MUTACIONES = ('terminal', 'operacion', 'intercambio', 'subarbol')
SELECCIONES = tuple(METODOS)


@dataclass(frozen=True)
class Parametros:
    poblacion: int = 80
    generaciones: int = 100
    altura_maxima: int = 5
    prob_cruce: float = .85
    prob_mutacion: float = .35
    elitismo: int = 2
    torneo: int = 3
    metrica: str = 'mse'
    objetivo: float = 1e-6
    semilla: int = 42
    seleccion: str = 'torneo'
    inmigracion: float = .1
    ajuste_lineal: bool = True
    refinar_constantes: bool = True
    pesos_mutacion: tuple = (3., 3., 1., 3.)
    operaciones: tuple = OPERACIONES_BASE

    def __post_init__(self):
        for nombre in ('poblacion', 'generaciones', 'altura_maxima', 'elitismo', 'torneo', 'semilla'):
            if type(getattr(self, nombre)) is not int:
                raise ValueError(f'{nombre} debe ser entero.')
        if self.poblacion < 2 or self.generaciones < 0 or self.altura_maxima < 1:
            raise ValueError('Usa población ≥ 2, generaciones ≥ 0 y altura ≥ 1.')
        if not 0 <= self.elitismo < self.poblacion or (self.seleccion=='torneo' and self.torneo < 2):
            raise ValueError('Elitismo menor que población; torneo al menos 2.')
        if self.seleccion not in SELECCIONES:
            raise ValueError('Método de selección desconocido.')
        if any(not math.isfinite(p) or not 0 <= p <= 1 for p in (self.prob_cruce, self.prob_mutacion, self.inmigracion)):
            raise ValueError('Las probabilidades deben estar entre 0 y 1.')
        if self.metrica not in ('mse', 'nmse', 'rmse', 'r2'):
            raise ValueError('Métrica desconocida.')
        if not math.isfinite(self.objetivo) or self.objetivo < 0:
            raise ValueError('La tolerancia objetivo debe ser finita y no negativa.')
        if len(self.pesos_mutacion) != 4 or any((not isinstance(p,int) and not math.isfinite(p)) or p < 0 for p in self.pesos_mutacion) or sum(self.pesos_mutacion) <= 0:
            raise ValueError('Cuatro pesos de mutación no negativos; al menos uno positivo.')
        if not self.operaciones or any(o not in OPERACIONES for o in self.operaciones):
            raise ValueError('Selecciona operaciones válidas del catálogo del intérprete.')


def clonar(nodo):
    """Copia cada instancia; dos posiciones nunca comparten identidad."""
    if nodo is None:
        return None
    return Nodo(nodo.valor, clonar(nodo.izquierdo), clonar(nodo.derecho), nodo.tipo)


def ubicaciones(raiz, ruta=()):
    """Pares (ruta, nodo); () es la raíz, 0/1 indican izquierdo/derecho."""
    yield ruta, raiz
    for lado, hijo in enumerate((raiz.izquierdo, raiz.derecho)):
        if hijo is not None:
            yield from ubicaciones(hijo, ruta + (lado,))


def sustituir(raiz, ruta, nuevo):
    if not ruta:
        return clonar(nuevo)
    izquierdo, derecho = raiz.izquierdo, raiz.derecho
    if ruta[0] == 0:
        izquierdo = sustituir(izquierdo, ruta[1:], nuevo)
        derecho = clonar(derecho)
    else:
        izquierdo = clonar(izquierdo)
        derecho = sustituir(derecho, ruta[1:], nuevo)
    return Nodo(raiz.valor, izquierdo, derecho, raiz.tipo)


def terminal(azar):
    if azar.random() < .55:
        return Nodo('x', tipo='variable')
    # Mezcla constantes simples y decimales de ambos signos.
    valor = azar.choice((-2., -1., 0., 1., 2., 3., 4.)) if azar.random() < .5 else azar.uniform(-5,5)
    return Nodo(format(valor,'.17g'), tipo='numero')


def generar_arbol(azar, altura, operaciones=OPERACIONES_BASE, forzar=False, completo=False, cancelar=None):
    if cancelar is not None and cancelar():
        raise InterruptedError('Generación de árbol cancelada.')
    if altura == 1 or (not completo and not forzar and azar.random() < .28):
        return terminal(azar)
    operacion = azar.choice(operaciones)
    izquierdo = generar_arbol(azar, altura-1, operaciones, completo=completo,cancelar=cancelar)
    if operacion.simbolo=='^' and azar.random()<.8:
        # Potencias enteras comunes admiten X negativos; un exponente decimal
        # aleatorio invalidaría gran parte de una muestra que cruza el cero.
        derecho=Nodo(str(azar.choice((2,3,4))),tipo='numero')
    else:
        derecho = generar_arbol(azar, altura-1, operaciones, completo=completo,cancelar=cancelar) if operacion.aridad == 2 else None
    return Nodo(operacion.simbolo, izquierdo, derecho, operacion.tipo)


def cruzar(padre, madre, azar, altura_maxima):
    """Intercambia dos subárboles, incluyendo la posibilidad de elegir raíz.

    Si el intercambio excede la altura, se buscan otros cortes. Al agotar los
    intentos se conservan copias de los padres: se evita truncar y cambiar la
    semántica arbitrariamente. Nunca se modifica un padre ni la élite.
    """
    a, b = list(ubicaciones(padre)), list(ubicaciones(madre))
    for _ in range(16):
        ruta_a, nodo_a = azar.choice(a)
        ruta_b, nodo_b = azar.choice(b)
        if len(ruta_a)+altura_arbol(nodo_b) <= altura_maxima and len(ruta_b)+altura_arbol(nodo_a) <= altura_maxima:
            return sustituir(padre, ruta_a, nodo_b), sustituir(madre, ruta_b, nodo_a)
    return clonar(padre), clonar(madre)


def mutar(raiz, tipo, azar, altura_maxima, operaciones=OPERACIONES_BASE, cancelar=None):
    """Cuatro mutaciones que conservan aridad y límite de altura.

    terminal: cambia constante/variable; operacion: mismo número de hijos;
    intercambio: permuta hijos de un nodo binario; subarbol: rama nueva.
    La raíz es una posición válida y puede reemplazarse en su totalidad.
    """
    if cancelar is not None and cancelar():
        raise InterruptedError('Mutación cancelada.')
    posiciones = list(ubicaciones(raiz))
    if tipo == 'terminal':
        candidatos = [(r,n) for r,n in posiciones if n.es_hoja]
    elif tipo == 'operacion':
        candidatos = [(r,n) for r,n in posiciones if not n.es_hoja]
    elif tipo == 'intercambio':
        candidatos = [(r,n) for r,n in posiciones if n.derecho is not None and n.valor not in ('+','*')]
    elif tipo == 'subarbol':
        candidatos = posiciones
    else:
        raise ValueError('Tipo de mutación desconocido.')
    if not candidatos:
        return clonar(raiz)
    ruta, nodo = azar.choice(candidatos)
    if tipo == 'terminal':
        padre=dict(posiciones).get(ruta[:-1]) if ruta else None
        exponente=padre is not None and padre.valor=='^' and ruta[-1]==1
        if nodo.tipo=='numero' and exponente:
            nuevo=Nodo(str(round(float(nodo.valor))+azar.choice((-2,-1,1,2))),tipo='numero')
        elif nodo.tipo == 'numero' and azar.random() < .8:
            valor = float(nodo.valor)
            escala = max(abs(valor),1.) * azar.choice((.01,.1,1.))
            nuevo = Nodo(format(valor + azar.gauss(0,escala),'.17g'), tipo='numero')
        else:
            nuevo = terminal(azar)
    elif tipo == 'operacion':
        aridad = 2 if nodo.derecho is not None else 1
        compatibles = [o for o in operaciones if o.aridad == aridad and o.simbolo != nodo.valor]
        if not compatibles:
            return clonar(raiz)
        op = azar.choice(compatibles)
        nuevo = Nodo(op.simbolo, nodo.izquierdo, nodo.derecho, op.tipo)
    elif tipo == 'intercambio':
        nuevo = Nodo(nodo.valor, nodo.derecho, nodo.izquierdo, nodo.tipo)
    else:
        disponible = altura_maxima-len(ruta)
        modo = azar.random()
        binarias = [o for o in operaciones if o.aridad==2]
        if modo < .4 and binarias and altura_arbol(nodo)<disponible:
            # Inserción: conserva una rama ya aprendida y añade otra, en lugar
            # de destruir siempre el material útil con una sustitución total.
            op=azar.choice(binarias)
            otra=generar_arbol(azar,disponible-1,operaciones,cancelar=cancelar)
            nuevo=Nodo(op.simbolo,clonar(nodo),otra,op.tipo)
        elif modo < .6 and not nodo.es_hoja:
            # Poda/hoist: elimina complejidad manteniendo un subárbol válido.
            nuevo=azar.choice([h for h in (nodo.izquierdo,nodo.derecho) if h is not None])
        else:
            nuevo = generar_arbol(azar, disponible, operaciones,cancelar=cancelar)
    return sustituir(raiz, ruta, nuevo)


@dataclass(frozen=True)
class Individuo:
    raiz: Nodo
    perdida: float
    metricas: tuple = ()
    error: str = ''
    nodos: int = 0

    @property
    def expresion(self):
        return texto_inorder(self.raiz)

    @property
    def valido(self):
        return math.isfinite(self.perdida)

    @property
    def orden(self):
        # Menos nodos desempata errores iguales, sin distorsionar las métricas.
        return self.perdida, self.nodos


@dataclass(frozen=True)
class Generacion:
    numero: int
    individuos: tuple
    mejor_historico: Individuo
    media: float
    validos: int
    diversidad: float = 0.
    evaluaciones: int = 0

    @property
    def mejor(self):
        return self.individuos[0]


class RegresionSimbolica:
    def __init__(self, puntos, parametros=None):
        self.parametros = parametros or Parametros()
        self.puntos = tuple((float(x), float(y)) for x,y in puntos)
        if len(self.puntos) < 2 or not all(math.isfinite(v) for par in self.puntos for v in par):
            raise ValueError('Se requieren al menos dos puntos X,Y finitos.')
        self.xs, self.ys = zip(*self.puntos)
        if len(set(self.xs)) < 2:
            raise ValueError('El CSV debe contener al menos dos valores X diferentes.')
        if self.parametros.metrica in ('nmse','r2') and len(set(self.ys)) == 1:
            raise ValueError('NMSE y R² no están definidas para Y constante; selecciona MSE o RMSE.')
        self.azar = random.Random(self.parametros.semilla)
        self.evaluador = ExpressionEvaluator()
        self.cache = {}
        self.evaluaciones = 0

    def evaluar(self, raiz, cancelar=None):
        clave = texto_inorder(raiz)
        nodos = sum(1 for _ in ubicaciones(raiz))
        if clave in self.cache:
            previo = self.cache[clave]
            return Individuo(raiz, previo.perdida, previo.metricas, previo.error, nodos)
        self.evaluaciones += 1
        try:
            validar_arbol(raiz, self.parametros.altura_maxima)
            predichos = self.evaluador.predecir(raiz, self.xs, cancelar, self.parametros.altura_maxima)
            metricas = calcular_metricas(self.ys, predichos)
            valor = metricas[self.parametros.metrica]
            perdida = 1-valor if self.parametros.metrica == 'r2' else valor
            if not math.isfinite(perdida):
                raise ValueError('La métrica no es finita.')
            resultado = Individuo(raiz, max(0., perdida), tuple(metricas.items()), nodos=nodos)
        except (ExpresionError, ValueError, OverflowError) as error:
            resultado = Individuo(raiz, math.inf, error=str(error), nodos=nodos)
        self.cache[clave] = resultado
        return resultado

    def seleccionar(self, poblacion):
        return seleccionar(poblacion,self.azar,self.parametros.seleccion,self.parametros.torneo,
                           getattr(self,'_cancelar',None))

    def refinar(self, poblacion, cancelar):
        if not self.parametros.ajuste_lineal and not self.parametros.refinar_constantes:
            return poblacion
        simbolos={o.simbolo for o in self.parametros.operaciones}
        poblacion.sort(key=lambda i:i.orden)
        # Sólo tres candidatos: ajusta a,b sin reemplazar la búsqueda de estructura.
        for j in range(min(3,len(poblacion))):
            if cancelar():
                raise InterruptedError('Evolución cancelada.')
            individuo=poblacion[j]
            if not individuo.valido:
                continue
            try:
                if self.parametros.ajuste_lineal and {'+', '*'}.issubset(simbolos):
                    raiz=ajustar_salida(individuo.raiz,self.xs,self.ys,self.evaluador,
                                        self.parametros.altura_maxima,cancelar)
                    if altura_arbol(raiz)<=self.parametros.altura_maxima:
                        mejorado=self.evaluar(raiz,cancelar)
                        if mejorado.orden < individuo.orden:
                            poblacion[j]=mejorado
                if j==0 and self.parametros.refinar_constantes:
                    poblacion[j]=self.refinar_coeficientes(poblacion[j],cancelar)
            except (ValueError,ExpresionError,OverflowError):
                continue
        return poblacion

    def refinar_coeficientes(self, individuo, cancelar):
        """Un paso por coordenada sobre constantes del mejor árbol.

        Derivada central numérica y paso de mínimos cuadrados. La estructura
        no cambia, y cada propuesta debe reducir la pérdida real en TODOS los
        puntos. Es un refinamiento local opcional, no otra función objetivo.
        """
        mejor=individuo
        for ruta,nodo in list(ubicaciones(individuo.raiz)):
            if cancelar():
                raise InterruptedError('Refinamiento cancelado.')
            if nodo.tipo!='numero':
                continue
            c=float(nodo.valor)
            h=max(abs(c),1.)*1e-4
            try:
                base=self.evaluador.predecir(mejor.raiz,self.xs,cancelar,self.parametros.altura_maxima)
                mas=sustituir(mejor.raiz,ruta,Nodo(format(c+h,'.17g'),tipo='numero'))
                menos=sustituir(mejor.raiz,ruta,Nodo(format(c-h,'.17g'),tipo='numero'))
                fp=self.evaluador.predecir(mas,self.xs,cancelar,self.parametros.altura_maxima)
                fm=self.evaluador.predecir(menos,self.xs,cancelar,self.parametros.altura_maxima)
                d=[(a-b)/(2*h) for a,b in zip(fp,fm)]
                norma=math.fsum(v*v for v in d)
                if not math.isfinite(norma) or norma==0:
                    continue
                paso=math.fsum(v*(y-f) for v,y,f in zip(d,self.ys,base))/norma
                for factor in (1.,.5,.25):
                    valor=c+paso*factor
                    if not math.isfinite(valor):
                        continue
                    raiz=sustituir(mejor.raiz,ruta,Nodo(format(valor,'.17g'),tipo='numero'))
                    candidato=self.evaluar(raiz,cancelar)
                    if candidato.orden < mejor.orden:
                        mejor=candidato
                        break
            except (ValueError,ExpresionError,OverflowError):
                continue
        return mejor

    def evolucionar(self, cancelar=None):
        """Generador de estados inmutables, desde generación 0 hasta el límite.

        Cada individuo se evalúa contra TODOS los datos. Una sola muestra fuera
        del dominio recibe pérdida infinita. La semilla controla todo el azar.
        """
        p, azar = self.parametros, self.azar
        cancelar = cancelar or (lambda: False)
        self._cancelar = cancelar
        poblacion = []
        for indice in range(p.poblacion):
            if cancelar():
                return
            # Ramped half-and-half: profundidades variadas, mitad full/mitad grow.
            altura = 1 + indice % p.altura_maxima
            raiz = generar_arbol(azar, altura, p.operaciones, forzar=altura>1,
                                 completo=(indice // p.altura_maxima) % 2 == 0,cancelar=cancelar)
            raiz = simplificar(raiz)
            poblacion.append(self.evaluar(raiz, cancelar))
        historico = min(poblacion,key=lambda i:i.orden)
        for numero in range(p.generaciones+1):
            if cancelar():
                return
            poblacion = self.refinar(poblacion,cancelar)
            poblacion.sort(key=lambda i:i.orden)
            if poblacion[0].orden < historico.orden:
                historico = poblacion[0]
            finitos = [i.perdida for i in poblacion if i.valido]
            media = sum(v/len(finitos) for v in finitos) if finitos else math.inf
            diversidad=len({i.expresion for i in poblacion})/len(poblacion)
            yield Generacion(numero, tuple(poblacion), historico, media, len(finitos),
                             diversidad,self.evaluaciones)
            if historico.perdida <= p.objetivo or numero == p.generaciones:
                return
            self.cache = {}  # caché acotada a una generación
            nueva = poblacion[:p.elitismo]
            claves = {i.expresion for i in nueva}
            # Inmigrantes aleatorios preservan diversidad sin reemplazar la élite.
            cantidad = min(p.poblacion-len(nueva), round(p.poblacion*p.inmigracion))
            for _ in range(cantidad):
                if cancelar():
                    return
                raiz=simplificar(generar_arbol(azar,azar.randint(1,p.altura_maxima),p.operaciones,cancelar=cancelar))
                nuevo=self.evaluar(raiz,cancelar)
                nueva.append(nuevo)
                claves.add(nuevo.expresion)
            while len(nueva) < p.poblacion:
                if cancelar():
                    return
                padre, madre = self.seleccionar(poblacion), self.seleccionar(poblacion)
                if azar.random() < p.prob_cruce:
                    hijos = cruzar(padre.raiz, madre.raiz, azar, p.altura_maxima)
                else:
                    hijos = clonar(padre.raiz), clonar(madre.raiz)
                for raiz in hijos:
                    tipo = None
                    if azar.random() < p.prob_mutacion:
                        escala=max(p.pesos_mutacion)
                        tipo = azar.choices(MUTACIONES, weights=[v/escala for v in p.pesos_mutacion])[0]
                        raiz = mutar(raiz, tipo, azar, p.altura_maxima, p.operaciones,cancelar)
                    raiz=simplificar(raiz)
                    # No llenar la población de clones; reintentos finitos.
                    for _ in range(3):
                        if tipo is None or texto_inorder(raiz) not in claves:
                            break
                        raiz=simplificar(mutar(raiz,tipo,azar,p.altura_maxima,p.operaciones,cancelar))
                    nueva.append(self.evaluar(raiz, cancelar))
                    claves.add(texto_inorder(raiz))
                    if len(nueva) == p.poblacion:
                        break
            poblacion = nueva
