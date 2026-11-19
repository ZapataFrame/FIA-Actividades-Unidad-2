"""Panel Qt de regresión simbólica. El motor en genetico.py no importa Qt."""

import math
import threading
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPointF, QRectF
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QTabWidget, QFileDialog,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QScrollArea, QSplitter,
)
from PyQt6.QtGui import QPainter, QColor, QPen

from algoritmo import OPERACIONES
from datos import leer_csv, muestrear
from genetico import Parametros, RegresionSimbolica, OPERACIONES_BASE
from seleccion import METODOS
from entradas import EntradaEntera, EntradaReal
from diagnostico import diagnosticar


def numero(valor):
    return f'{valor:.6g}' if math.isfinite(valor) else 'No definida / inválida'


class TrabajadorGenetico(QThread):
    generacion = pyqtSignal(object)
    fallo = pyqtSignal(str)

    def __init__(self, motor, parent=None):
        super().__init__(parent)
        self.motor = motor
        self.cancelado = threading.Event()

    def run(self):
        try:
            for estado in self.motor.evolucionar(self.cancelado.is_set):
                self.generacion.emit(estado)
        except InterruptedError:
            pass
        except Exception as error:
            self.fallo.emit(str(error))


class CurvaError(QWidget):
    """Error por generación; escala logarítmica para apreciar mejoras pequeñas."""
    def __init__(self):
        super().__init__()
        self.estados = []
        self.setMinimumHeight(260)

    def paintEvent(self, evento):
        p = QPainter(self)
        try:
            p.fillRect(self.rect(), QColor('white'))
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(84, 24, max(1,self.width()-112), max(1,self.height()-84))
            series = [
                [(e.numero, e.mejor_historico.perdida) for e in self.estados],
                [(e.numero, e.media) for e in self.estados],
            ]
            finitos = [math.log10(max(v,1e-15)) for s in series for _,v in s if math.isfinite(v)]
            if not finitos:
                p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Ejecuta la evolución para ver la pérdida por generación.')
                return
            ymin, ymax = min(finitos)-.5, max(finitos)+.5
            xmax = max(1, self.estados[-1].numero)
            def punto(x,y):
                return QPointF(rect.left()+rect.width()*x/xmax,
                               rect.bottom()-rect.height()*(y-ymin)/(ymax-ymin))
            p.setPen(QPen(QColor('#e5eaf0'),1))
            for i in range(6):
                y = ymin+(ymax-ymin)*i/5
                py = punto(0,y).y()
                p.drawLine(QPointF(rect.left(),py),QPointF(rect.right(),py))
                p.setPen(QColor('black'))
                p.drawText(QRectF(0,py-10,76,20),Qt.AlignmentFlag.AlignRight,f'1e{y:.1f}')
                p.setPen(QPen(QColor('#e5eaf0'),1))
            for serie,color in zip(series,('#2563b5','#d18224')):
                p.setPen(QPen(QColor(color),2))
                anterior=None
                for x,y in serie:
                    actual=punto(x,math.log10(max(y,1e-15))) if math.isfinite(y) else None
                    if anterior is not None and actual is not None:
                        p.drawLine(anterior,actual)
                    anterior=actual
            p.setPen(QColor('black'))
            p.drawRect(rect)
            p.drawText(84,self.height()-18,'Generación 0')
            p.drawText(self.width()-150,self.height()-18,f'Generación {xmax}')
        finally:
            p.end()


class PanelGenetico(QWidget):
    aplicar = pyqtSignal(object, object)

    def __init__(self, crear_arbol, crear_grafica):
        super().__init__()
        self.puntos = []
        self.diagnostico = None
        self.estados = []
        self.trabajador = None
        self.parametros = None
        self.seleccionado = None
        self._error = ''
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Regresión simbólica · modo híbrido por defecto; puedes desactivar los refinamientos en Configuración avanzada.'))
        carga = QHBoxLayout()
        self.importar = QPushButton('Importar CSV para evolución')
        self.importar.clicked.connect(self.importar_csv)
        carga.addWidget(self.importar)
        self.archivo = QLabel('Sin datos. Formato: columnas x,y; mínimo dos X distintos.')
        carga.addWidget(self.archivo,1)
        layout.addLayout(carga)
        self.referencia_texto=QLabel('La referencia de la media aparecerá al cargar los datos.')
        self.referencia_texto.setWordWrap(True)
        layout.addWidget(self.referencia_texto)
        grid = QGridLayout()
        self.poblacion = self.entero(80)
        self.generaciones = self.entero(100)
        self.altura = self.entero(6)
        self.cruce = self.real(.85)
        self.mutacion = self.real(.35)
        self.elitismo = self.entero(2)
        self.torneo = self.entero(3)
        self.semilla = self.entero(42)
        self.metrica = QComboBox()
        for texto,clave in [('MSE','mse'),('RMSE','rmse'),('NMSE','nmse'),('R²','r2')]:
            self.metrica.addItem(texto,clave)
        self.seleccion = QComboBox()
        for clave,nombre in METODOS.items():
            self.seleccion.addItem(nombre,clave)
        self.seleccion.setToolTip('Torneo, ruleta de pérdidas, rango o uniforme. El tamaño de torneo sólo se usa en Torneo.')
        self.seleccion.currentIndexChanged.connect(self.actualizar_seleccion)
        self.objetivo = self.real(.000001)
        self.objetivo.setToolTip('Parada cuando la pérdida ≤ tolerancia. Para R² la pérdida es 1 − R².')
        self.mutacion.setToolTip('Probabilidad por hijo. Si muta, se sortea uno de los cuatro tipos según sus pesos.')
        self.cruce.setToolTip('Probabilidad por pareja. Intercambia un subárbol de cada padre.')
        self.elitismo.setToolTip('Individuos conservados sin cambios; debe ser menor que la población.')
        controles = [('Población',self.poblacion),('Generaciones',self.generaciones),
                     ('Altura máxima',self.altura),('Prob. cruce',self.cruce),
                     ('Prob. mutación',self.mutacion),('Élite',self.elitismo),
                     ('Torneo',self.torneo),('Semilla',self.semilla),
                     ('Métrica objetivo',self.metrica),('Tolerancia de pérdida',self.objetivo),
                     ('Selección de padres',self.seleccion)]
        self.controles_parametros = [control for _,control in controles]
        for i,(texto,control) in enumerate(controles):
            fila,col=divmod(i,6)
            grid.addWidget(QLabel(texto),fila*2,col)
            grid.addWidget(control,fila*2+1,col)
        layout.addLayout(grid)
        self.avanzado = QCheckBox('Configuración avanzada: mutaciones, inmigración, operaciones y refinamientos')
        layout.addWidget(self.avanzado)
        self.config_extra = QWidget()
        extra = QGridLayout(self.config_extra)
        self.pesos=[]
        for col,nombre in enumerate(('Terminal','Operación','Intercambio de hijos','Subárbol nuevo')):
            control = self.entero((30,30,10,30)[col])
            self.pesos.append(control)
            extra.addWidget(QLabel(nombre+' · peso'),0,col)
            extra.addWidget(control,1,col)
        self.cientificas = QCheckBox('Catálogo científico completo (más restricciones de dominio)')
        extra.addWidget(self.cientificas,2,0,1,4)
        self.potencias = QCheckBox('Añadir potencias ^ al catálogo base (sin activar todo el científico)')
        self.potencias.setChecked(True)
        extra.addWidget(self.potencias,7,0,1,4)
        extra.addWidget(QLabel('Los pesos se normalizan entre sí. La probabilidad de mutación se aplica por individuo.'),3,0,1,4)
        self.inmigracion = self.real(.1)
        extra.addWidget(QLabel('Fracción de inmigrantes'),4,0)
        extra.addWidget(self.inmigracion,4,1)
        self.ajuste_lineal = QCheckBox('Ajuste lineal de salida (híbrido)')
        self.ajuste_lineal.setChecked(True)
        self.refinar_constantes = QCheckBox('Refinamiento local de constantes (híbrido)')
        self.refinar_constantes.setChecked(True)
        extra.addWidget(self.ajuste_lineal,5,0,1,2)
        extra.addWidget(self.refinar_constantes,5,2,1,2)
        extra.addWidget(QLabel('Cierra Configuración avanzada para volver a las gráficas. Iniciar evolución también la cierra.'),6,0,1,4)
        self.config_extra.hide()
        self.avanzado.toggled.connect(self.alternar_configuracion)
        layout.addWidget(self.config_extra)
        acciones = QHBoxLayout()
        self.iniciar = QPushButton('Iniciar evolución')
        self.iniciar.setObjectName('primary')
        self.iniciar.clicked.connect(self.ejecutar)
        self.detener = QPushButton('Detener')
        self.detener.clicked.connect(self.cancelar)
        self.detener.setEnabled(False)
        acciones.addWidget(self.iniciar)
        acciones.addWidget(self.detener)
        self.estado = QLabel('Sin ejecución. MSE, RMSE y NMSE se minimizan; para R² se minimiza 1 − R².')
        self.estado.setWordWrap(True)
        acciones.addWidget(self.estado,1)
        layout.addLayout(acciones)
        self.vistas = QTabWidget()
        layout.addWidget(self.vistas,1)
        ajuste = QWidget()
        ajuste_layout = QVBoxLayout(ajuste)
        self.mejor_texto = QLabel('La mejor función y sus métricas aparecerán aquí.')
        self.mejor_texto.setWordWrap(True)
        self.mejor_texto.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ajuste_layout.addWidget(self.mejor_texto)
        ajuste_layout.addWidget(QLabel('Azul: mejor función · rojo: CSV · gris discontinuo: predecir la media'))
        self.ajuste = crear_grafica()
        self.ajuste.setMinimumSize(420, 180)
        ajuste_layout.addWidget(self.ajuste,1)
        self.usar_mejor = QPushButton('Abrir mejor función en el editor')
        self.usar_mejor.setEnabled(False)
        self.usar_mejor.clicked.connect(self.aplicar_mejor)
        ajuste_layout.addWidget(self.usar_mejor)
        self.vistas.addTab(ajuste,'Ajuste de la función')
        progreso = QWidget()
        pl = QVBoxLayout(progreso)
        pl.addWidget(QLabel('Pérdida (escala log) · azul: mejor histórica · naranja: media de individuos válidos. Cero se dibuja en 1e−15.'))
        self.curva = CurvaError()
        pl.addWidget(self.curva,1)
        self.vistas.addTab(progreso,'Evolución del error')
        individuos = QWidget()
        il = QVBoxLayout(individuos)
        navegacion = QHBoxLayout()
        navegacion.addWidget(QLabel('Generación'))
        self.generacion = QComboBox()
        self.generacion.currentIndexChanged.connect(self.mostrar_generacion)
        navegacion.addWidget(self.generacion)
        self.seguir = QCheckBox('Seguir última generación')
        self.seguir.setChecked(True)
        navegacion.addWidget(self.seguir)
        self.usar = QPushButton('Abrir individuo en el editor')
        self.usar.clicked.connect(self.aplicar_individuo)
        self.usar.setEnabled(False)
        navegacion.addWidget(self.usar)
        navegacion.addStretch()
        il.addLayout(navegacion)
        division = QSplitter(Qt.Orientation.Horizontal)
        self.tabla = QTableWidget(0,7)
        self.tabla.setHorizontalHeaderLabels(['Posición','Pérdida','MSE','RMSE','R²','Nodos','Expresión'])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.mostrar_individuo)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        division.addWidget(self.tabla)
        self.arbol_individuo = crear_arbol()
        self.arbol_individuo.setMinimumSize(420, 200)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(self.arbol_individuo)
        division.addWidget(area)
        division.setSizes([650,450])
        il.addWidget(division,1)
        self.detalle = QLabel('Selecciona un individuo para inspeccionar su árbol y sus métricas.')
        self.detalle.setWordWrap(True)
        self.detalle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        il.addWidget(self.detalle)
        self.vistas.addTab(individuos,'Individuos')
        self.espacio_configuracion = QWidget()
        layout.addWidget(self.espacio_configuracion,1)
        self.espacio_configuracion.hide()

    @staticmethod
    def entero(valor):
        return EntradaEntera(valor)

    @staticmethod
    def real(valor):
        return EntradaReal(valor)

    @property
    def en_ejecucion(self):
        return self.trabajador is not None and self.trabajador.isRunning()

    def actualizar_seleccion(self):
        self.torneo.setEnabled(not self.en_ejecucion and self.seleccion.currentData()=='torneo')

    def alternar_configuracion(self, visible):
        self.config_extra.setVisible(visible)
        self.vistas.setVisible(not visible)
        self.espacio_configuracion.setVisible(visible)

    def importar_csv(self):
        ruta,_=QFileDialog.getOpenFileName(self,'Observaciones para regresión simbólica','','CSV (*.csv)')
        if ruta:
            self.cargar_csv(ruta)

    def cargar_csv(self,ruta):
        if self.en_ejecucion:
            return
        try:
            puntos=leer_csv(ruta)
            if len(puntos)<2 or len({x for x,_ in puntos})<2:
                raise ValueError('Se requieren al menos dos puntos con X diferentes.')
            d=diagnosticar(puntos)
            self.puntos=puntos
            self.diagnostico=d
            aviso=' Oscilaciones frecuentes: revisa altura, potencias y frecuencia.' if d.cruces_media>=6 and d.cruces_media>len(puntos)/5 else ''
            self.referencia_texto.setText(f'Referencia constante: y={d.media_y:.6g} · MSE={d.mse_media:.6g} · R²=0 si Y no es constante.'+aviso)
            self.archivo.setText(f'{Path(ruta).name} · {len(puntos)} puntos · X ∈ [{min(x for x,_ in puntos):g}, {max(x for x,_ in puntos):g}]')
            self.limpiar_resultados()
            self.ajuste.configurar([],puntos,self.rango(puntos),d.media_y)
            self.estado.setText('Datos cargados. Ajusta parámetros y pulsa Iniciar evolución.')
        except (OSError,ValueError,OverflowError) as error:
            self.estado.setText(f'No se cargó el CSV: {error}')

    def limpiar_resultados(self):
        self.estados=[]
        self.generacion.clear()
        self.tabla.setRowCount(0)
        self.curva.estados=[]
        self.curva.update()
        self.seleccionado=None
        self.usar.setEnabled(False)
        self.usar_mejor.setEnabled(False)
        self.arbol_individuo.configurar(None,None)
        self.mejor_texto.setText('Sin resultado para esta ejecución.')
        self.detalle.setText('Selecciona un individuo.')

    def ejecutar(self):
        if self.en_ejecucion:
            return
        try:
            if not self.puntos:
                raise ValueError('Primero importa un CSV con observaciones X,Y.')
            self.parametros=Parametros(
                poblacion=self.poblacion.value(), generaciones=self.generaciones.value(),
                altura_maxima=self.altura.value(), prob_cruce=self.cruce.value(),
                prob_mutacion=self.mutacion.value(), elitismo=self.elitismo.value(),
                torneo=self.torneo.value(), semilla=self.semilla.value(),
                metrica=self.metrica.currentData(), objetivo=self.objetivo.value(),
                seleccion=self.seleccion.currentData(), inmigracion=self.inmigracion.value(),
                ajuste_lineal=self.ajuste_lineal.isChecked(),
                refinar_constantes=self.refinar_constantes.isChecked(),
                pesos_mutacion=tuple(c.value() for c in self.pesos),
                operaciones=OPERACIONES if self.cientificas.isChecked() else tuple(
                    o for o in OPERACIONES if o in OPERACIONES_BASE or (self.potencias.isChecked() and o.simbolo=='^')),
            )
            motor=RegresionSimbolica(self.puntos,self.parametros)
        except ValueError as error:
            self.estado.setText(str(error)); return
        self.limpiar_resultados()
        self.avanzado.setChecked(False)
        self._error=''
        self.trabajador=TrabajadorGenetico(motor,self)
        self.trabajador.generacion.connect(self.recibir)
        self.trabajador.fallo.connect(self.fallar)
        self.trabajador.finished.connect(self.finalizar)
        self.importar.setEnabled(False)
        self.iniciar.setEnabled(False)
        self.detener.setEnabled(True)
        for control in self.controles_parametros:
            control.setEnabled(False)
        self.config_extra.setEnabled(False)
        self.estado.setText('Inicializando población…')
        self.trabajador.start()

    def cancelar(self):
        if self.trabajador is not None:
            self.trabajador.cancelado.set()
            self.estado.setText('Deteniendo… Se conservarán las generaciones completadas.')

    def fallar(self,mensaje):
        self._error=mensaje
        self.estado.setText('Error: '+mensaje)

    def finalizar(self):
        self.iniciar.setEnabled(True)
        self.importar.setEnabled(True)
        self.detener.setEnabled(False)
        for control in self.controles_parametros:
            control.setEnabled(True)
        self.config_extra.setEnabled(True)
        self.actualizar_seleccion()
        if self._error:
            return
        if self.trabajador.cancelado.is_set():
            texto='Detenida por el usuario.'
        elif self.estados and self.estados[-1].mejor_historico.perdida<=self.parametros.objetivo:
            texto='Tolerancia objetivo alcanzada.'
        else:
            texto='Límite de generaciones alcanzado.'
        modo='Híbrido' if self.parametros.ajuste_lineal or self.parametros.refinar_constantes else 'Genético puro'
        self.estado.setText(modo+' · '+texto+' El resultado aproxima los datos; no garantiza la fórmula original.')

    def recibir(self,estado):
        self.estados.append(estado)
        self.generacion.addItem(str(estado.numero))
        if self.seguir.isChecked():
            self.generacion.setCurrentIndex(len(self.estados)-1)
        self.curva.estados=self.estados
        self.curva.update()
        mejor=estado.mejor_historico
        self.usar_mejor.setEnabled(mejor.valido)
        self.estado.setText(f'Generación {estado.numero}/{self.parametros.generaciones} · válidos {estado.validos}/{len(estado.individuos)} · diversidad {estado.diversidad:.0%} · pérdida {numero(mejor.perdida)}')
        metricas=dict(mejor.metricas)
        resumen=' · '.join(f'{k.upper() if k!="r2" else "R²"}: {numero(v)}' for k,v in metricas.items())
        explicacion=self.diagnostico.explicar_ajuste(metricas.get('mse',math.inf))
        self.mejor_texto.setText(f'f(x) = {mejor.expresion}\n{resumen or mejor.error}\n{explicacion}')
        if mejor.valido:
            xmin,xmax,ymin,ymax=self.rango(self.puntos)
            muestras=muestrear(mejor.raiz,xmin,xmax,(xmax-xmin)/300)
            self.ajuste.configurar(muestras,self.puntos,(xmin,xmax,ymin,ymax),self.diagnostico.media_y)

    @staticmethod
    def rango(puntos):
        xs,ys=zip(*puntos)
        mx=max((max(xs)-min(xs))*.08,.1)
        my=max((max(ys)-min(ys))*.1,.1)
        return min(xs)-mx,max(xs)+mx,min(ys)-my,max(ys)+my

    def mostrar_generacion(self,indice):
        if not 0<=indice<len(self.estados):
            return
        poblacion=self.estados[indice].individuos
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(poblacion))
        for fila,ind in enumerate(poblacion):
            m=dict(ind.metricas)
            valores=[str(fila+1),numero(ind.perdida),numero(m.get('mse',math.nan)),
                     numero(m.get('rmse',math.nan)),numero(m.get('r2',math.nan)),str(ind.nodos),ind.expresion]
            for columna,texto in enumerate(valores):
                item=QTableWidgetItem(texto)
                if ind.error:
                    item.setToolTip(ind.error)
                self.tabla.setItem(fila,columna,item)
        self.tabla.blockSignals(False)
        self.tabla.selectRow(0)
        self.mostrar_individuo()

    def mostrar_individuo(self):
        g=self.generacion.currentIndex()
        fila=self.tabla.currentRow()
        if not 0<=g<len(self.estados) or fila<0:
            return
        self.seleccionado=self.estados[g].individuos[fila]
        ind=self.seleccionado
        self.arbol_individuo.setMinimumWidth(max(580,ind.nodos*46))
        self.arbol_individuo.configurar(ind.raiz,None)
        m=dict(ind.metricas)
        resumen=' · '.join(f'{k.upper()}: {numero(v)}' for k,v in m.items())
        self.detalle.setText(f'f(x) = {ind.expresion}\n{resumen or ind.error}')
        self.usar.setEnabled(True)

    def aplicar_individuo(self):
        if self.seleccionado is not None:
            self.aplicar.emit(self.seleccionado.raiz,tuple(self.puntos))

    def aplicar_mejor(self):
        if self.estados and self.estados[-1].mejor_historico.valido:
            self.aplicar.emit(self.estados[-1].mejor_historico.raiz,tuple(self.puntos))
