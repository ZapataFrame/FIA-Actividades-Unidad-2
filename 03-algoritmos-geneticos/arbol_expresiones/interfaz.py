"""Interfaz didáctica: árbol, recorridos y plano cartesiano en dos pestañas."""

import sys
import math
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPalette
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QTabWidget, QToolButton, QListWidget, QSlider, QFileDialog, QScrollArea,
)
from algoritmo import (Nodo, ExpresionError, ExpressionParser, ExpressionEvaluator,
                       ExpressionInterpreter, nodos_por_nivel, texto_inorder)
from biblioteca import GeneradorExpresiones, altura_arbol
from datos import muestrear, validar_funcion, leer_csv, guardar_csv
from metricas import calcular_metricas
from interfaz_genetica import PanelGenetico
from entradas import EntradaEntera


class ArbolCanvas(QWidget):
    """Dibujo vectorial del árbol; los colores explican el estado del recorrido."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.raiz = None
        self.paso = None
        self.setMinimumSize(580, 380)
        self.setAutoFillBackground(True)

    def configurar(self, raiz, paso):
        self.raiz, self.paso = raiz, paso
        self.update()

    def paintEvent(self, evento):
        """Pinta con un ciclo de vida explícito para que Qt nunca conserve un painter activo.

        Si una operación de dibujo recibe un dato inesperado, el ``finally``
        sigue llamando ``end()``; esto evita que un error de paint termine en
        el mensaje ``QBackingStore::endPaint`` y en un cierre nativo de Qt.
        """
        if getattr(self, "_pintando", False):
            return
        self._pintando = True
        painter = QPainter()
        if not painter.begin(self):
            self._pintando = False
            return
        try:
            self._pintar_contenido(painter)
        except Exception as error:  # La ventana debe seguir viva ante un fallo visual.
            print(f"No se pudo dibujar el árbol: {error}", file=sys.stderr)
        finally:
            painter.end()
            self._pintando = False

    def _pintar_contenido(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#fffdf8"))
        if self.raiz is None:
            painter.setPen(QColor("#77716a"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Escribe una expresión y pulsa Construir árbol")
            return

        posiciones = nodos_por_nivel(self.raiz)
        max_x = max(x for x, _ in posiciones.values())
        max_depth = max(depth for _, depth in posiciones.values())
        margen_x, margen_y = 50, 55
        paso_x = (self.width() - 2 * margen_x) / max(max_x, 1)
        paso_y = min(100, (self.height() - 2 * margen_y) / max(max_depth, 1))
        puntos = {}
        for nodo, (indice, profundidad) in posiciones.items():
            puntos[nodo] = QPointF(margen_x + indice * paso_x, margen_y + profundidad * paso_y)

        def dibujar_aristas(nodo):
            if nodo is None:
                return
            origen = puntos[nodo]
            for hijo in (nodo.izquierdo, nodo.derecho):
                if hijo is not None:
                    destino = puntos[hijo]
                    painter.setPen(QPen(QColor("#bcb5aa"), 2))
                    painter.drawLine(origen, destino)
                    dibujar_aristas(hijo)
        dibujar_aristas(self.raiz)

        visitados = set(self.paso.visitados) if self.paso else set()
        actual = self.paso.nodo if self.paso else None
        radio = 25
        for nodo, punto in puntos.items():
            if nodo is actual:
                fondo, borde = "#f4b183", "#c35b16"
            elif nodo in visitados:
                fondo, borde = "#b9d9ee", "#3979a8"
            elif nodo.es_hoja:
                fondo, borde = "#e8f1dd", "#729653"
            else:
                fondo, borde = "#f2ede5", "#766f65"
            painter.setPen(QPen(QColor(borde), 2))
            painter.setBrush(QBrush(QColor(fondo)))
            painter.drawEllipse(punto, radio, radio)
            painter.setPen(QColor("#302e2b"))
            painter.setFont(QFont("Sans", 11, QFont.Weight.Normal))
            painter.drawText(QRectF(punto.x() - radio, punto.y() - radio, 2 * radio, 2 * radio),
                             Qt.AlignmentFlag.AlignCenter,
                             f'{float(nodo.valor):.4g}' if nodo.tipo == 'numero' else nodo.valor)


class GraficaCanvas(QWidget):
    """Dibuja muestras precalculadas; pintar nunca evalúa expresiones.

    El rectángulo de dibujo recorta la curva. Los huecos y saltos muy grandes
    no se unen para evitar líneas verticales falsas junto a asíntotas.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(580, 380)
        self.muestras = []
        self.puntos = []
        self.rango = (-10, 10, -10, 10)
        self.referencia = None

    def configurar(self, muestras, puntos, rango, referencia=None):
        self.muestras, self.puntos, self.rango = muestras, puntos, rango
        self.referencia = referencia
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.fillRect(self.rect(), QColor('white'))
            area = QRectF(72, 24, max(1, self.width()-100), max(1, self.height()-80))
            xmin, xmax, ymin, ymax = self.rango
            def punto(x, y):
                return QPointF(area.left()+(x-xmin)/(xmax-xmin)*area.width(),
                               area.bottom()-(y-ymin)/(ymax-ymin)*area.height())
            p.setFont(QFont('Sans Serif', 10))
            for i in range(11):
                x = xmin + i*(xmax-xmin)/10
                y = ymin + i*(ymax-ymin)/10
                px, py = punto(x, ymin).x(), punto(xmin, y).y()
                p.setPen(QPen(QColor('#e5eaf0'), 1))
                p.drawLine(QPointF(px, area.top()), QPointF(px, area.bottom()))
                p.drawLine(QPointF(area.left(), py), QPointF(area.right(), py))
                p.setPen(QColor('black'))
                p.drawText(QRectF(px-36, area.bottom()+8, 72, 20), Qt.AlignmentFlag.AlignCenter, f'{x:.3g}')
                p.drawText(QRectF(0, py-10, 64, 20), Qt.AlignmentFlag.AlignRight, f'{y:.3g}')
            p.setPen(QPen(QColor('#68758a'), 1.5))
            if xmin <= 0 <= xmax:
                p.drawLine(punto(0, ymin), punto(0, ymax))
            if ymin <= 0 <= ymax:
                p.drawLine(punto(xmin, 0), punto(xmax, 0))
            p.drawRect(area)
            p.drawText(QPointF(area.right(), area.bottom()+44), 'x')
            p.drawText(QPointF(18, 18), 'f(x)')
            p.save()
            p.setClipRect(area)
            if self.referencia is not None:
                p.setPen(QPen(QColor('#64748b'),1.5,Qt.PenStyle.DashLine))
                p.drawLine(punto(xmin,self.referencia),punto(xmax,self.referencia))
            p.setPen(QPen(QColor('#2563b5'), 2))
            anterior = None
            for x, y in self.muestras:
                actual = None if y is None else punto(x, y)
                if actual is not None and anterior is not None:
                    if abs(actual.y()-anterior.y()) < area.height():
                        p.drawLine(anterior, actual)
                anterior = actual
            p.setPen(QPen(QColor('#9e352c'), 1))
            p.setBrush(QColor('#d64a3d'))
            for x, y in self.puntos:
                p.drawEllipse(punto(x, y), 4, 4)
            p.restore()
        finally:
            p.end()


def configurar_tema(app):
    """Fusion y paleta completa para independizar controles del tema oscuro."""
    app.setStyle('Fusion')
    app.setFont(QFont('Sans Serif', 10))
    paleta = QPalette()
    colores = {'Window': '#f6f7f9', 'WindowText': '#000000', 'Base': '#ffffff',
               'AlternateBase': '#f4f6f8', 'Text': '#000000', 'Button': '#ffffff',
               'ButtonText': '#000000', 'Highlight': '#dbeafe',
               'HighlightedText': '#000000', 'ToolTipBase': '#ffffff',
               'ToolTipText': '#000000', 'PlaceholderText': '#64748b'}
    for grupo in QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled:
        for rol, color in colores.items():
            paleta.setColor(grupo, getattr(QPalette.ColorRole, rol), QColor(color))
    app.setPalette(paleta)
    app.setStyleSheet('''
        QWidget { color: #000000; font-weight: normal; }
        QMainWindow, QTabWidget::pane { background: #f6f7f9; }
        QLineEdit, QComboBox, QAbstractSpinBox, QListWidget, QAbstractItemView {
            color: #000000; background-color: #ffffff;
            selection-color: #000000; selection-background-color: #dbeafe;
            border: 1px solid #b9c4d1; border-radius: 4px; padding: 5px;
        }
        QPushButton, QToolButton { background: #ffffff; color: #000000;
            border: 1px solid #b9c4d1; border-radius: 4px; padding: 6px 10px; }
        QPushButton:hover, QToolButton:hover { background: #e8eef6; }
        QPushButton:disabled { color: #627083; background: #eef0f3; }
        QPushButton#primary { background: #dbeafe; border-color: #709bd0; }
        QLabel#title { font-size: 20px; font-weight: 600; }
        QLabel#result, QLabel#stats { background: #ffffff; border: 1px solid #d1d9e3;
            border-radius: 5px; padding: 8px; }
        QTabBar::tab { background: #edf0f4; color: #000000; padding: 9px 16px; }
        QTabBar::tab:selected { background: #ffffff; border-bottom: 2px solid #2563b5; }
        QHeaderView::section { background: #edf0f4; color: #000000; padding: 5px; border: 1px solid #d1d9e3; }
        QToolTip { background: #ffffff; color: #000000; border: 1px solid #b9c4d1; }
    ''')


class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        configurar_tema(QApplication.instance())
        self.setWindowTitle('Árbol de expresiones')
        self.resize(1180, 800)
        self.interprete = ExpressionInterpreter()
        self.raiz = None
        self.texto_construido = None
        self.pasos, self.indice, self.puntos_csv = [], 0, []
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.navegar(self.indice+1))
        root = QWidget()
        self.setCentralWidget(root)
        principal = QVBoxLayout(root)
        principal.setContentsMargins(18, 16, 18, 16)
        self.titulo = QLabel('Árbol de expresiones')
        self.titulo.setObjectName('title')
        principal.addWidget(self.titulo)
        self.ayuda = QLabel('1. Escribe o genera una expresión.  2. Explora el árbol o abre Gráfica y datos.')
        principal.addWidget(self.ayuda)
        entrada = QHBoxLayout()
        entrada.addWidget(QLabel('f(x) ='))
        self.entrada = QLineEdit('(x + 2) * sin(x)')
        self.entrada.setPlaceholderText('Ejemplo: sin(x) + x^2')
        self.entrada.returnPressed.connect(self.construir)
        self.entrada.textEdited.connect(self.marcar_pendiente)
        entrada.addWidget(self.entrada, 1)
        self.construir_boton = self.boton('Construir', self.construir)
        self.construir_boton.setObjectName('primary')
        entrada.addWidget(self.construir_boton)
        self.generar_boton = self.boton('Generar expresión', self.generar_ecuacion)
        entrada.addWidget(self.generar_boton)
        entrada.addWidget(QLabel('Altura máx.'))
        self.altura_maxima = EntradaEntera(4)
        self.altura_maxima.setToolTip('Límite para generación; una hoja tiene altura 1.')
        entrada.addWidget(self.altura_maxima)
        self.barra_editor = QWidget()
        self.barra_editor.setLayout(entrada)
        entrada.setContentsMargins(0,0,0,0)
        principal.addWidget(self.barra_editor)
        self.descripcion = QLabel()
        self.descripcion.setWordWrap(True)
        principal.addWidget(self.descripcion)
        self.pestanas = QTabWidget()
        principal.addWidget(self.pestanas, 1)
        self.crear_arbol()
        self.crear_grafica()
        self.genetico = PanelGenetico(ArbolCanvas, GraficaCanvas)
        self.genetico.aplicar.connect(self.usar_individuo)
        self.pestanas.addTab(self.genetico, 'Evolución genética')
        self.pestanas.currentChanged.connect(self.cambiar_vista)
        self.construir()

    @staticmethod
    def boton(texto, accion):
        boton = QPushButton(texto)
        boton.clicked.connect(accion)
        return boton

    def crear_arbol(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        self.resultado = QLabel()
        self.resultado.setObjectName('result')
        self.resultado.setWordWrap(True)
        self.resultado.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.resultado)
        barra = QHBoxLayout()
        barra.addWidget(QLabel('Recorrido'))
        self.orden = QComboBox()
        self.orden.addItems(['preorder', 'inorder', 'postorder'])
        self.orden.currentTextChanged.connect(self.preparar_recorrido)
        barra.addWidget(self.orden)
        self.estructura = QLabel()
        barra.addWidget(self.estructura)
        barra.addStretch()
        self.detalles = QToolButton()
        self.detalles.setText('Ver pasos')
        self.detalles.setCheckable(True)
        self.detalles.toggled.connect(self.mostrar_detalles)
        barra.addWidget(self.detalles)
        layout.addLayout(barra)
        centro = QHBoxLayout()
        self.canvas = ArbolCanvas()
        self.area_arbol = QScrollArea()
        self.area_arbol.setWidgetResizable(True)
        self.area_arbol.setWidget(self.canvas)
        centro.addWidget(self.area_arbol, 1)
        self.historial = QListWidget()
        self.historial.setMaximumWidth(320)
        self.historial.currentRowChanged.connect(self.navegar)
        self.historial.hide()
        centro.addWidget(self.historial)
        layout.addLayout(centro, 1)
        self.estado = QLabel()
        self.estado.setWordWrap(True)
        layout.addWidget(self.estado)
        controles = QHBoxLayout()
        self.anterior = self.boton('Anterior', lambda: self.navegar(self.indice-1))
        self.play = self.boton('Reproducir', self.alternar)
        self.siguiente = self.boton('Siguiente', lambda: self.navegar(self.indice+1))
        for b in self.anterior, self.play, self.siguiente:
            controles.addWidget(b)
        self.linea_tiempo = QSlider(Qt.Orientation.Horizontal)
        self.linea_tiempo.valueChanged.connect(self.navegar)
        controles.addWidget(self.linea_tiempo, 1)
        self.contador = QLabel()
        controles.addWidget(self.contador)
        self.velocidad = QComboBox()
        for texto, ms in [('0.5×',1600), ('1×',800), ('2×',400)]:
            self.velocidad.addItem(texto, ms)
        self.velocidad.setCurrentIndex(1)
        self.velocidad.currentIndexChanged.connect(lambda: self.timer.setInterval(self.velocidad.currentData()))
        controles.addWidget(self.velocidad)
        layout.addLayout(controles)
        self.pestanas.addTab(pagina, 'Árbol y recorridos')

    def crear_grafica(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.addWidget(QLabel('Plano cartesiano · azul: función · rojo: observaciones CSV'))
        grid = QGridLayout()
        self.csv_desde = self.numero(-10)
        self.csv_hasta = self.numero(10)
        self.grafica_y_min = self.numero(-10)
        self.grafica_y_max = self.numero(10)
        self.csv_paso = self.numero(0.1, 0.000001, 1e6)
        for col, (texto, control) in enumerate([
            ('X mínimo', self.csv_desde), ('X máximo', self.csv_hasta),
            ('Y mínimo', self.grafica_y_min), ('Y máximo', self.grafica_y_max),
            ('Paso CSV', self.csv_paso),
        ]):
            grid.addWidget(QLabel(texto), 0, col)
            grid.addWidget(control, 1, col)
        self.graficar_boton = self.boton('Actualizar gráfica', self.graficar_funcion)
        grid.addWidget(self.graficar_boton, 1, 5)
        layout.addLayout(grid)
        self.grafica = GraficaCanvas()
        layout.addWidget(self.grafica, 1)
        fila = QHBoxLayout()
        self.csv_boton = self.boton('Cargar CSV', self.abrir_csv)
        self.generar_csv_boton = self.boton('Exportar puntos CSV', self.generar_csv)
        self.quitar_csv = self.boton('Quitar datos', self.limpiar_datos)
        fila.addWidget(self.csv_boton)
        fila.addWidget(self.generar_csv_boton)
        fila.addWidget(self.quitar_csv)
        fila.addStretch()
        layout.addLayout(fila)
        self.metricas_texto = QLabel('Carga un CSV X,Y para comparar la función con datos observados.')
        self.metricas_texto.setObjectName('stats')
        self.metricas_texto.setWordWrap(True)
        layout.addWidget(self.metricas_texto)
        self.pestanas.addTab(pagina, 'Gráfica y datos')

    @staticmethod
    def numero(valor, minimo=-1e6, maximo=1e6):
        control = QDoubleSpinBox()
        control.setDecimals(6)
        control.setRange(minimo, maximo)
        control.setValue(valor)
        return control

    def marcar_pendiente(self):
        self.pausar()
        self.descripcion.setText('Expresión modificada. Pulsa Construir o Actualizar gráfica para aplicarla.')

    def cambiar_vista(self, indice):
        self.pausar()
        genetica = indice == 2
        self.barra_editor.setVisible(not genetica)
        self.descripcion.setVisible(not genetica)
        self.titulo.setText('Regresión simbólica' if genetica else 'Árbol de expresiones')
        self.ayuda.setText('Importa un CSV, elige la selección y configura la búsqueda.' if genetica else
                           '1. Escribe o genera una expresión.  2. Explora el árbol o abre Gráfica y datos.')

    def usar_individuo(self, raiz, puntos):
        """El individuo elegido reutiliza el editor, recorridos y métricas."""
        self.entrada.setText(texto_inorder(raiz))
        self.puntos_csv = list(puntos)
        self.construir(raiz)
        self.pestanas.setCurrentIndex(0)

    def mostrar_detalles(self, visible):
        self.historial.setVisible(visible)
        self.detalles.setText('Ocultar pasos' if visible else 'Ver pasos')

    def asegurar_arbol(self):
        if self.texto_construido != self.entrada.text():
            self.construir()
        if self.raiz is None:
            raise ExpresionError('Primero escribe una expresión válida.')
        return self.raiz

    def construir(self, raiz=None):
        self.pausar()
        try:
            if isinstance(raiz, Nodo):
                self.interprete.raiz = raiz
            else:
                raiz = self.interprete.parse(self.entrada.text())
        except ExpresionError as error:
            self.raiz = self.interprete.raiz = None
            self.texto_construido = None
            self.pasos = []
            self.historial.clear()
            self.canvas.configurar(None, None)
            self.grafica.configurar([], [], self.rango_seguro())
            self.resultado.setText(f'Expresión inválida: {error}')
            self.descripcion.setText('Corrige la expresión para continuar.')
            self.estructura.clear()
            self.estado.clear()
            self.metricas_texto.setText('Sin función válida para comparar.')
            self.actualizar_botones()
            return
        self.raiz = raiz
        self.texto_construido = self.entrada.text()
        variables = self.interprete.variables(raiz)
        self.resultado.setText('f(x) = ' + texto_inorder(raiz))
        if not variables:
            try:
                self.resultado.setText(f'Resultado = {self.interprete.evaluate():.12g}')
            except ExpresionError as error:
                self.resultado.setText(f'Error de evaluación: {error}')
        elif variables - {'x'}:
            self.resultado.setText(texto_inorder(raiz) + '\nÁrbol simbólico. Para el plano 2D usa sólo la variable x.')
        self.estructura.setText(f'{len(nodos_por_nivel(raiz))} nodos · altura {altura_arbol(raiz)}')
        cantidad = len(nodos_por_nivel(raiz))
        self.canvas.setMinimumWidth(max(580, cantidad*46))
        self.descripcion.setText('Árbol construido. Explora el recorrido o ve a Gráfica y datos.')
        self.grafica.configurar([], self.puntos_csv, self.rango_seguro())
        self.metricas_texto.setText('Actualiza la gráfica para comparar la función actual.')
        self.preparar_recorrido()

    def rango_seguro(self):
        valores = (self.csv_desde.value(), self.csv_hasta.value(),
                   self.grafica_y_min.value(), self.grafica_y_max.value())
        if valores[0] >= valores[1] or valores[2] >= valores[3]:
            return (-10, 10, -10, 10)
        return valores

    def validar_rango(self):
        xmin, xmax = self.csv_desde.value(), self.csv_hasta.value()
        ymin, ymax = self.grafica_y_min.value(), self.grafica_y_max.value()
        if xmin >= xmax or ymin >= ymax:
            raise ValueError('Los máximos X e Y deben ser mayores que sus mínimos.')
        return xmin, xmax, ymin, ymax

    def generar_ecuacion(self):
        try:
            generador = GeneradorExpresiones(self.altura_maxima.value(), variables=('x',))
            def valida(texto):
                raiz = ExpressionParser(texto).parse()
                puntos = muestrear(raiz, -2, 2, 0.5)
                return sum(y is not None for _, y in puntos) >= 5
            self.entrada.setText(generador.generar_hasta(valida))
            self.construir()
        except (ValueError, ExpresionError) as error:
            self.descripcion.setText(str(error))

    def graficar_funcion(self):
        try:
            raiz = self.asegurar_arbol()
            xmin, xmax, ymin, ymax = self.validar_rango()
            muestras = muestrear(raiz, xmin, xmax, (xmax-xmin)/600)
            self.grafica.configurar(muestras, self.puntos_csv, (xmin,xmax,ymin,ymax))
            self.comparar_datos()
            validos = sum(y is not None for _, y in muestras)
            self.descripcion.setText(f'Gráfica actualizada: {validos}/{len(muestras)} muestras reales válidas. Los huecos indican dominio inválido.')
            self.pestanas.setCurrentIndex(1)
        except (ValueError, ExpresionError) as error:
            self.descripcion.setText(str(error))

    def comparar_datos(self):
        if not self.puntos_csv:
            self.metricas_texto.setText('Carga un CSV X,Y para comparar con f(x).')
            return
        reales, predichos = [], []
        evaluador = ExpressionEvaluator()
        for x, y in self.puntos_csv:
            evaluador.variables['x'] = x
            try:
                predicho = evaluador.evaluate(self.raiz)
            except ExpresionError:
                continue
            reales.append(y)
            predichos.append(predicho)
        if not reales:
            self.metricas_texto.setText('Ninguna observación pertenece al dominio de la función.')
            return
        valores = calcular_metricas(reales, predichos)
        texto = ' · '.join(f'{clave.upper() if clave != "r2" else "R²"}: {valor:.6g}'
                           if math.isfinite(valor) else f'{clave.upper()}: no definida'
                           for clave, valor in valores.items())
        self.metricas_texto.setText(texto + f'\nComparados: {len(reales)}/{len(self.puntos_csv)}. NMSE = MSE / varianza observada.')

    def abrir_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(self, 'Cargar puntos X,Y', '', 'CSV (*.csv)')
        if ruta:
            self.comparar_csv(ruta)

    leer_csv = staticmethod(leer_csv)

    def comparar_csv(self, ruta):
        try:
            self.asegurar_arbol()
            validar_funcion(self.raiz)
            self.puntos_csv = leer_csv(ruta)
            xs, ys = zip(*self.puntos_csv)
            for minimo, maximo, control_min, control_max in [
                (min(xs),max(xs),self.csv_desde,self.csv_hasta),
                (min(ys),max(ys),self.grafica_y_min,self.grafica_y_max),
            ]:
                margen = max((maximo-minimo)*0.1, 1)
                control_min.setValue(minimo-margen)
                control_max.setValue(maximo+margen)
            self.graficar_funcion()
        except (OSError, ValueError, ExpresionError) as error:
            self.descripcion.setText(f'CSV: {error}')

    def limpiar_datos(self):
        self.puntos_csv = []
        self.graficar_funcion()

    def generar_csv(self):
        try:
            raiz = self.asegurar_arbol()
            muestras = muestrear(raiz, self.csv_desde.value(), self.csv_hasta.value(), self.csv_paso.value())
            validos = sum(y is not None for _, y in muestras)
            if not validos:
                raise ValueError('No hay puntos válidos en este intervalo.')
            ruta, _ = QFileDialog.getSaveFileName(self, 'Guardar puntos', 'funcion.csv', 'CSV (*.csv)')
            if not ruta:
                return
            if not ruta.lower().endswith('.csv'):
                ruta += '.csv'
            guardar_csv(ruta, muestras)
            self.descripcion.setText(f'CSV guardado: {validos} puntos; {len(muestras)-validos} omitidos por dominio inválido.')
        except (OSError, ValueError, ExpresionError) as error:
            self.descripcion.setText(f'Exportación: {error}')

    def preparar_recorrido(self):
        if self.raiz is None:
            return
        self.pausar()
        self.pasos = list(self.interprete.traversal_steps(self.orden.currentText(), self.raiz))
        self.historial.blockSignals(True)
        self.historial.clear()
        self.historial.addItems([p.mensaje for p in self.pasos])
        self.historial.blockSignals(False)
        self.linea_tiempo.blockSignals(True)
        self.linea_tiempo.setRange(0, max(0,len(self.pasos)-1))
        self.linea_tiempo.blockSignals(False)
        self.navegar(0)

    def navegar(self, indice):
        if not self.pasos:
            return
        self.indice = max(0,min(indice,len(self.pasos)-1))
        paso = self.pasos[self.indice]
        for control in self.historial, self.linea_tiempo:
            control.blockSignals(True)
        self.historial.setCurrentRow(self.indice)
        self.linea_tiempo.setValue(self.indice)
        for control in self.historial, self.linea_tiempo:
            control.blockSignals(False)
        self.canvas.configurar(self.raiz,paso)
        self.estado.setText(paso.mensaje + ' · Naranja: actual · Azul: visitados')
        self.contador.setText(f'{self.indice+1}/{len(self.pasos)}')
        self.actualizar_botones()
        if self.indice == len(self.pasos)-1:
            self.pausar()

    def actualizar_botones(self):
        self.play.setEnabled(bool(self.pasos))
        self.anterior.setEnabled(bool(self.pasos) and self.indice>0)
        self.siguiente.setEnabled(bool(self.pasos) and self.indice<len(self.pasos)-1)
        if not self.pasos:
            self.contador.setText('0/0')

    def alternar(self):
        if self.timer.isActive():
            self.pausar()
        elif self.pasos:
            if self.indice == len(self.pasos)-1:
                self.navegar(0)
            if len(self.pasos)>1:
                self.timer.start(self.velocidad.currentData())
                self.play.setText('Pausar')

    def pausar(self):
        self.timer.stop()
        self.play.setText('Reproducir')

    def closeEvent(self, evento):
        self.pausar()
        if self.genetico.en_ejecucion:
            self.genetico.cancelar()
            # Espera de forma asíncrona; nunca destruye un QThread activo.
            self.genetico.trabajador.finished.connect(self.close)
            evento.ignore()
            return
        evento.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = Ventana()
    ventana.show()
    sys.exit(app.exec())
