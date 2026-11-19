"""Árboles de expresión: parser pequeño, evaluación y recorridos.

La parte didáctica importante está en parsear una expresión y convertirla en
un árbol binario. La interfaz únicamente consume los nodos y las instantáneas
que produce este módulo.
"""

from dataclasses import dataclass
import math
import re


class ExpresionError(ValueError):
    """Error de sintaxis o de evaluación explicado para el usuario."""


@dataclass(frozen=True, eq=False)
class Nodo:
    """Un nodo físico del árbol.

    ``eq=False`` es intencional: dos nodos pueden mostrar el mismo valor
    (por ejemplo, las dos apariciones de ``x`` en ``x + x``), pero siguen
    siendo posiciones distintas del árbol. Así los recorridos, coordenadas y
    estados de animación trabajan por identidad, no por el texto mostrado.
    """
    valor: str
    izquierdo: "Nodo | None" = None
    derecho: "Nodo | None" = None
    tipo: str = "operador"  # numero, variable, operador, funcion

    @property
    def es_hoja(self):
        return self.izquierdo is None and self.derecho is None


@dataclass(frozen=True)
class PasoRecorrido:
    numero: int
    recorrido: str
    nodo: Nodo
    visitados: tuple[Nodo, ...]
    mensaje: str


TOKEN_RE = re.compile(r"\s*(?:((?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)|([A-Za-z_]\w*)|(.))")
FUNCIONES = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "exp": math.exp, "log": math.log,
    "ln": math.log, "log10": math.log10, "abs": abs,
    "floor": math.floor, "ceil": math.ceil,
}
CONSTANTES = {"pi": math.pi, "e": math.e}


@dataclass(frozen=True)
class Operacion:
    simbolo: str
    aridad: int
    tipo: str = "operador"


# Fuente única para validar árboles y generar individuos con la misma gramática.
OPERACIONES = tuple(Operacion(s, 2) for s in "+-*/^") + (
    Operacion("u-", 1), Operacion("u+", 1),
) + tuple(Operacion(s, 1, "funcion") for s in FUNCIONES)


def validar_arbol(raiz, altura_maxima=64):
    """Rechaza hijos faltantes, ciclos y nodos compartidos antes de usarlos."""
    vistos = set()
    catalogo = {(o.tipo, o.simbolo): o.aridad for o in OPERACIONES}
    pendientes = [(raiz, 1)]
    while pendientes:
        nodo, altura = pendientes.pop()
        if not isinstance(nodo, Nodo) or nodo in vistos:
            raise ExpresionError("El árbol contiene un nodo inválido, compartido o un ciclo.")
        vistos.add(nodo)
        if altura_maxima is not None and altura > altura_maxima:
            raise ExpresionError(f"La altura del árbol supera {altura_maxima} niveles.")
        hijos = [h for h in (nodo.izquierdo, nodo.derecho) if h is not None]
        if nodo.tipo in ("numero", "variable"):
            aridad = 0
        else:
            aridad = catalogo.get((nodo.tipo, nodo.valor))
        if aridad is None or len(hijos) != aridad or (aridad == 1 and nodo.izquierdo is None):
            raise ExpresionError(f"Aridad o tipo incorrecto en {nodo.valor!r}.")
        pendientes.extend((h, altura + 1) for h in hijos)
    return raiz


def _tokenizar(texto):
    """Convierte texto a tokens y rechaza caracteres que no pertenecen al lenguaje."""
    tokens = []
    posicion = 0
    while posicion < len(texto):
        coincidencia = TOKEN_RE.match(texto, posicion)
        if not coincidencia:
            if texto[posicion:].strip() == "":
                break
            raise ExpresionError(f"Carácter inesperado en la posición {posicion + 1}.")
        numero, nombre, simbolo = coincidencia.groups()
        posicion = coincidencia.end()
        if numero:
            tokens.append(("numero", numero))
        elif nombre:
            tokens.append(("nombre", nombre))
        elif simbolo in "+-*/^(),":
            tokens.append((simbolo, simbolo))
        elif not simbolo.isspace():
            raise ExpresionError(f"Símbolo no permitido: {simbolo!r}.")
    tokens.append(("fin", ""))
    return tokens


class ExpressionParser:
    # Precedencias: potencia > producto > suma. La potencia es asociativa a la derecha.
    PRECEDENCIA = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}

    def __init__(self, texto):
        self.tokens = _tokenizar(texto)
        self.indice = 0

    def actual(self):
        return self.tokens[self.indice]

    def avanzar(self, esperado=None):
        token = self.actual()
        if esperado is not None and token[0] != esperado:
            raise ExpresionError(f"Se esperaba {esperado!r}, pero apareció {token[1] or 'fin'}.")
        self.indice += 1
        return token

    def parse(self):
        self.indice = 0
        if len(self.tokens) > 512:
            raise ExpresionError("La expresión supera el límite de 511 tokens.")
        if self.actual()[0] == "fin":
            raise ExpresionError("La expresión está vacía.")
        try:
            raiz = self.expresion(0)
        except RecursionError as error:
            raise ExpresionError("La expresión tiene demasiados niveles anidados.") from error
        if self.actual()[0] != "fin":
            raise ExpresionError(f"Token inesperado: {self.actual()[1]!r}.")
        return validar_arbol(raiz)

    # Alias en español para conservar el vocabulario usado en clase.
    def parsear(self):
        return self.parse()

    def expresion(self, minimo):
        izquierdo = self.prefijo()
        while self.actual()[0] in self.PRECEDENCIA:
            operador = self.actual()[0]
            precedencia = self.PRECEDENCIA[operador]
            if precedencia < minimo:
                break
            self.avanzar()
            # ^ es derecha-asociativo: 2^3^2 significa 2^(3^2).
            siguiente_minimo = precedencia if operador == "^" else precedencia + 1
            derecho = self.expresion(siguiente_minimo)
            izquierdo = Nodo(operador, izquierdo, derecho)
        return izquierdo

    def prefijo(self):
        tipo, valor = self.actual()
        if tipo == "numero":
            self.avanzar()
            return Nodo(valor, tipo="numero")
        if tipo == "nombre":
            self.avanzar()
            if self.actual()[0] == "(":
                if valor not in FUNCIONES:
                    raise ExpresionError(f"Función desconocida: {valor}.")
                self.avanzar("(")
                argumento = self.expresion(0)
                self.avanzar(")")
                return Nodo(valor, argumento, tipo="funcion")
            if valor in FUNCIONES:
                raise ExpresionError(f"La función {valor} necesita paréntesis, por ejemplo {valor}(x).")
            return Nodo(valor, tipo="variable")
        if tipo in ("+", "-"):
            self.avanzar()
            # El menos unario se representa como nodo operador con un solo hijo.
            return Nodo("u" + tipo, self.expresion(3), tipo="operador")
        if tipo == "(":
            self.avanzar("(")
            resultado = self.expresion(0)
            self.avanzar(")")
            return resultado
        raise ExpresionError(f"Se esperaba un número, variable o paréntesis; apareció {valor or 'fin'}.")


def construir_arbol(texto):
    """Interpreta una expresión y devuelve su raíz."""
    return ExpressionParser(texto).parse()


def texto_inorder(nodo):
    if nodo is None:
        return ""
    if nodo.tipo == "operador" and nodo.valor in ("u+", "u-"):
        return "(" + nodo.valor[1] + texto_inorder(nodo.izquierdo) + ")"
    if nodo.tipo == "funcion":
        return f"{nodo.valor}({texto_inorder(nodo.izquierdo)})"
    if nodo.es_hoja:
        return nodo.valor
    return f"({texto_inorder(nodo.izquierdo)} {nodo.valor} {texto_inorder(nodo.derecho)})"


class TreeTraverser:
    """Realiza recorridos sobre cualquier árbol de nodos compatible."""

    ORDENES = {"preorder", "inorder", "postorder"}

    def __init__(self, raiz):
        self.raiz = raiz

    def recorrer(self, orden):
        if orden not in self.ORDENES:
            raise ValueError("El orden debe ser preorder, inorder o postorder.")
        salida = []

        def visitar(nodo):
            if nodo is None:
                return
            if orden == "preorder":
                salida.append(nodo)
            visitar(nodo.izquierdo)
            if orden == "inorder":
                salida.append(nodo)
            visitar(nodo.derecho)
            if orden == "postorder":
                salida.append(nodo)

        visitar(self.raiz)
        return tuple(salida)

    def pasos(self, orden):
        nombres = {"preorder": "preorden", "inorder": "inorden", "postorder": "postorden"}
        visitados = []
        for numero, nodo in enumerate(self.recorrer(orden), 1):
            visitados.append(nodo)
            yield PasoRecorrido(numero, orden, nodo, tuple(visitados),
                                f"Paso {numero}: visitar {nodo.valor!r} en recorrido {nombres[orden]}.")


def recorrer(raiz, orden):
    """Devuelve los nodos en preorder, inorder o postorder."""
    if orden not in {"preorder", "inorder", "postorder"}:
        raise ValueError("El orden debe ser preorder, inorder o postorder.")
    return TreeTraverser(raiz).recorrer(orden)


def pasos_recorrido(raiz, orden):
    """Genera una instantánea por nodo visitado, útil para animar la interfaz."""
    yield from TreeTraverser(raiz).pasos(orden)


def variables_en_arbol(nodo):
    """Devuelve variables libres; ``pi`` y ``e`` son constantes, no asignaciones."""
    if nodo is None:
        return set()
    propias = {nodo.valor} if nodo.tipo == "variable" and nodo.valor not in CONSTANTES else set()
    return propias | variables_en_arbol(nodo.izquierdo) | variables_en_arbol(nodo.derecho)


class ExpressionEvaluator:
    """Evalúa un árbol sin ``eval`` y centraliza la política de dominio."""

    def __init__(self, variables=None, tolerancia=1e-12):
        if not math.isfinite(tolerancia) or tolerancia < 0:
            raise ValueError("La tolerancia debe ser no negativa.")
        self.variables = {} if variables is None else dict(variables)
        for nombre, valor in self.variables.items():
            try:
                numero = float(valor)
            except (TypeError, ValueError) as error:
                raise ExpresionError(f"El valor de la variable {nombre!r} debe ser numérico.") from error
            if not math.isfinite(numero):
                raise ExpresionError(f"El valor de la variable {nombre!r} debe ser finito.")
            self.variables[nombre] = numero
        self.tolerancia = tolerancia

    @staticmethod
    def _real(valor):
        if isinstance(valor, complex) or not math.isfinite(valor):
            raise ExpresionError("La operación no produce un número real finito.")
        return valor

    def evaluate(self, nodo):
        validar_arbol(nodo, None)
        return self._evaluate(nodo)

    def predecir(self, nodo, valores_x, cancelar=None, altura_maxima=None):
        """Evalúa un individuo sobre todos los X validando su estructura una vez.

        Un error invalida la predicción completa: el ajuste genético no puede
        mejorar su puntuación omitiendo los puntos difíciles del CSV.
        """
        validar_arbol(nodo, altura_maxima)
        predichos = []
        for x in valores_x:
            if cancelar is not None and cancelar():
                raise InterruptedError("Evaluación cancelada.")
            self.variables['x'] = x
            predichos.append(self._evaluate(nodo))
        return tuple(predichos)

    def _evaluate(self, nodo):
        """Evalúa el árbol sin ``eval()`` y protege divisiones exactas o casi nulas.

        La tolerancia evita resultados engañosos como 1/1e-16 = 10^16.
        """
        if nodo is None:
            raise ExpresionError("No se puede evaluar un árbol vacío.")
        if nodo.tipo == "numero":
            try:
                return self._real(float(nodo.valor))
            except (TypeError, ValueError) as error:
                raise ExpresionError(f"Número inválido: {nodo.valor!r}.") from error
        if nodo.tipo == "variable":
            if nodo.valor in CONSTANTES:
                return CONSTANTES[nodo.valor]
            if nodo.valor not in self.variables:
                raise ExpresionError(f"Falta un valor para la variable {nodo.valor!r}.")
            return self._real(float(self.variables[nodo.valor]))
        if nodo.tipo == "funcion":
            try:
                argumento = self._evaluate(nodo.izquierdo)
                if nodo.valor == "tan" and abs(math.cos(argumento)) <= 1e-12:
                    raise ExpresionError("La tangente no está definida cerca de pi/2 + k*pi.")
                return self._real(FUNCIONES[nodo.valor](argumento))
            except (ValueError, OverflowError) as error:
                raise ExpresionError(f"No se pudo evaluar {nodo.valor}: {error}") from error
        if nodo.valor == "u+":
            return self._evaluate(nodo.izquierdo)
        if nodo.valor == "u-":
            return -self._evaluate(nodo.izquierdo)
        izquierdo = self._evaluate(nodo.izquierdo)
        derecho = self._evaluate(nodo.derecho)
        try:
            if nodo.valor == "/":
                if abs(derecho) <= self.tolerancia:
                    raise ExpresionError(
                        f"División no permitida: el denominador {derecho:g} está dentro de la tolerancia {self.tolerancia:g}."
                    )
                return self._real(izquierdo / derecho)
            return self._real({"+": lambda: izquierdo + derecho, "-": lambda: izquierdo - derecho,
                    "*": lambda: izquierdo * derecho, "^": lambda: izquierdo ** derecho}[nodo.valor]())
        except (KeyError, ZeroDivisionError, OverflowError, ValueError) as error:
            raise ExpresionError(f"No se pudo evaluar la operación {nodo.valor!r}: {error}") from error


def evaluar(nodo, variables=None, tolerancia=1e-12):
    """Envoltorio compatible para evaluar con la clase reutilizable."""
    return ExpressionEvaluator(variables, tolerancia).evaluate(nodo)


class ExpressionInterpreter:
    """Fachada pequeña para integrar construcción, evaluación y recorridos."""

    def __init__(self, tolerancia=1e-12):
        self.tolerancia = tolerancia
        self.raiz = None

    def parse(self, texto):
        self.raiz = ExpressionParser(texto).parse()
        return self.raiz

    def evaluate(self, raiz=None, variables=None, tolerancia=None):
        arbol = self.raiz if raiz is None else raiz
        if arbol is None:
            raise ExpresionError("No hay un árbol construido para evaluar.")
        limite = self.tolerancia if tolerancia is None else tolerancia
        return ExpressionEvaluator(variables, limite).evaluate(arbol)

    def variables(self, raiz=None):
        arbol = self.raiz if raiz is None else raiz
        return variables_en_arbol(arbol)

    def traverse(self, orden, raiz=None):
        arbol = self.raiz if raiz is None else raiz
        return TreeTraverser(arbol).recorrer(orden)

    def traversal_steps(self, orden, raiz=None):
        arbol = self.raiz if raiz is None else raiz
        return TreeTraverser(arbol).pasos(orden)


def nodos_por_nivel(raiz):
    """Coordenadas simples para dibujar: x por orden inorden y y por profundidad."""
    posiciones = {}
    contador = 0

    def visitar(nodo, profundidad):
        nonlocal contador
        if nodo is None:
            return
        visitar(nodo.izquierdo, profundidad + 1)
        posiciones[nodo] = (contador, profundidad)
        contador += 1
        visitar(nodo.derecho, profundidad + 1)

    visitar(raiz, 0)
    return posiciones
