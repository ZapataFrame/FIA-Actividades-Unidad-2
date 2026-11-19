"""Interfaz Tkinter: ejecutar con `python interfaz.py`. Solo biblioteca estándar."""

import tkinter as tk
from tkinter import messagebox, ttk

from algoritmo import PROBLEMAS, Parametros, calcular_bits, evolucionar


class Interfaz:
    def __init__(self, ventana):
        self.ventana = ventana
        ventana.title("Algoritmo genético · población y generaciones")
        ventana.geometry("1150x820")
        ventana.minsize(950, 720)
        self.temporizador = None
        self.historial = []
        self.ejecucion = None
        self.campos = {}

        controles = ttk.LabelFrame(ventana, text="1. Configura y pulsa Reiniciar para aplicar cambios", padding=10)
        controles.pack(fill="x", padx=12, pady=10)
        self.ejemplo = ttk.Combobox(controles, values=[p.nombre for p in PROBLEMAS], state="readonly", width=62)
        self.ejemplo.current(0)
        self.ejemplo.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        self.ejemplo.bind("<<ComboboxSelected>>", self.cambiar_ejemplo)

        defaults = Parametros()
        especificaciones = [
            ("Población", "tamano_poblacion", defaults.tamano_poblacion),
            ("Generaciones", "generaciones", defaults.generaciones),
            ("Precisión en x", "precision", defaults.precision),
            ("Cruce (0–1)", "prob_cruce", defaults.prob_cruce),
            ("Mutación por bit (0–1)", "prob_mutacion", defaults.prob_mutacion),
            ("Élites (0 = sin)", "elites", defaults.elites),
            ("Semilla", "semilla", defaults.semilla),
            ("Variables", "dimensiones", defaults.dimensiones),
            ("Pausa entre pasos (ms)", "pausa", 150),
        ]
        for indice, (etiqueta, clave, valor) in enumerate(especificaciones):
            fila, columna = 1 + indice // 3, (indice % 3) * 2
            ttk.Label(controles, text=etiqueta).grid(row=fila, column=columna, padx=(0, 8), pady=3, sticky="w")
            entrada = ttk.Entry(controles, width=12)
            entrada.insert(0, str(valor))
            entrada.grid(row=fila, column=columna + 1, padx=(0, 22), sticky="w")
            self.campos[clave] = entrada
        self.campos["dimensiones"].configure(state="disabled")

        botones = ttk.Frame(ventana)
        botones.pack(fill="x", padx=12)
        for texto, accion in [("Reiniciar", self.reiniciar), ("Siguiente generación", self.avanzar),
                              ("Reproducir", self.reproducir), ("Pausar", self.pausar)]:
            ttk.Button(botones, text=texto, command=accion).pack(side="left", padx=(0, 8))
        self.resumen = tk.StringVar()
        ttk.Label(ventana, textvariable=self.resumen, padding=(12, 8), wraplength=1100).pack(fill="x")

        graficas = ttk.Frame(ventana)
        graficas.pack(fill="both", expand=True, padx=12)
        self.poblacion_canvas = tk.Canvas(graficas, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.historia_canvas = tk.Canvas(graficas, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.poblacion_canvas.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.historia_canvas.pack(side="left", fill="both", expand=True)
        for canvas in (self.poblacion_canvas, self.historia_canvas):
            canvas.bind("<Configure>", lambda evento: self.dibujar())

        ttk.Label(ventana, text="Azul: población / promedio · Naranja: mejor de esta generación · Verde: mejor histórico").pack(pady=5)
        tabla_marco = ttk.LabelFrame(ventana, text="2. Individuos de la generación actual (desplázate para ver todos)", padding=5)
        tabla_marco.pack(fill="x", padx=12, pady=(0, 10))
        self.tabla = ttk.Treeview(tabla_marco, columns=("numero", "bits", "valores", "objetivo"), show="headings", height=7)
        for clave, titulo, ancho in [("numero", "#", 45), ("bits", "Genotipo: bits por variable", 380),
                                     ("valores", "Fenotipo: valores por variable", 360), ("objetivo", "f(x)", 140)]:
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=ancho, minwidth=40, stretch=clave != "numero")
        barra = ttk.Scrollbar(tabla_marco, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(tabla_marco, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=barra.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="ew")
        barra.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        tabla_marco.columnconfigure(0, weight=1)
        self.tabla.tag_configure("mejor", background="#fff0d6")
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.reiniciar()

    def cambiar_ejemplo(self, evento=None):
        self.pausar()
        entrada = self.campos["dimensiones"]
        entrada.configure(state="normal")
        entrada.delete(0, "end")
        entrada.insert(0, "2" if PROBLEMAS[self.ejemplo.current()].varias_variables else "1")
        if not PROBLEMAS[self.ejemplo.current()].varias_variables:
            entrada.configure(state="disabled")
        # Cada gráfico mantiene el problema de su ejecución hasta Reiniciar.

    def leer_parametros(self):
        enteros = {"tamano_poblacion", "generaciones", "elites", "semilla", "dimensiones"}
        valores = {}
        for clave, campo in self.campos.items():
            if clave == "pausa":
                continue
            convertir = int if clave in enteros else float
            valores[clave] = convertir(campo.get())
        pausa = int(self.campos["pausa"].get())
        if pausa < 1:
            raise ValueError("La pausa debe ser ≥ 1 ms.")
        # Límites prácticos de la interfaz; el algoritmo no depende de ellos.
        if not 2 <= valores["tamano_poblacion"] <= 2000 or not 1 <= valores["dimensiones"] <= 10:
            raise ValueError("En la interfaz usa población de 2 a 2000 y de 1 a 10 variables.")
        if not 0 <= valores["generaciones"] <= 5000:
            raise ValueError("En la interfaz usa de 0 a 5000 generaciones.")
        if valores["precision"] < 1e-12:
            raise ValueError("En la interfaz usa precisión ≥ 1e-12.")
        return Parametros(**valores), pausa

    def reiniciar(self):
        self.pausar()
        try:
            parametros, pausa = self.leer_parametros()
            problema = PROBLEMAS[self.ejemplo.current()]
            ejecucion = evolucionar(problema, parametros)
            inicial = next(ejecucion)  # Aquí se validan todos los parámetros.
        except (ValueError, OverflowError) as error:
            messagebox.showerror("Revisa los parámetros", str(error))
            return
        self.parametros, self.pausa, self.problema = parametros, pausa, problema
        self.ejecucion = ejecucion
        self.historial = [inicial]
        self.actualizar()

    def avanzar(self):
        self.pausar()
        self.siguiente()

    def siguiente(self):
        if self.ejecucion is None:
            return False
        try:
            estado = next(self.ejecucion)
        except StopIteration:
            return False
        self.historial.append(estado)
        self.actualizar()
        return estado.numero < self.parametros.generaciones

    def reproducir(self):
        # after() devuelve el control a Tk entre generaciones: se puede pausar.
        self.pausar()
        if self.siguiente():
            self.temporizador = self.ventana.after(self.pausa, self.reproducir)

    def pausar(self):
        if self.temporizador is not None:
            self.ventana.after_cancel(self.temporizador)
            self.temporizador = None

    def cerrar(self):
        self.pausar()
        self.ventana.destroy()

    def actualizar(self):
        estado = self.historial[-1]
        bits = calcular_bits(self.problema, self.parametros.precision)
        paso = (self.problema.limite_superior - self.problema.limite_inferior) / (2**bits - 1)
        valores = ", ".join(f"{x:.6f}" for x in estado.mejor.valores)
        final = " · Finalizado" if estado.numero == self.parametros.generaciones else ""
        self.resumen.set(
            f"Generación {estado.numero}/{self.parametros.generaciones}{final} · "
            f"{'Máximo' if self.problema.maximizar else 'Mínimo'} en [{self.problema.limite_inferior}, {self.problema.limite_superior}]\n"
            f"Mejor actual: f = {estado.mejor.objetivo:.6f}, x = ({valores}) · "
            f"Promedio: {estado.promedio:.6f} · Mejor histórico: {estado.mejor_historico.objetivo:.6f}\n"
            f"{bits} bits por variable · Separación de la rejilla: {paso:.6g} · "
            f"Individuos distintos: {len({ind.cromosomas for ind in estado.poblacion})}/{len(estado.poblacion)}"
        )
        self.tabla.delete(*self.tabla.get_children())
        for numero, individuo in enumerate(estado.poblacion, 1):
            self.tabla.insert("", "end", values=(numero, " | ".join(individuo.cromosomas),
                              ", ".join(f"{x:.6f}" for x in individuo.valores), f"{individuo.objetivo:.6f}"),
                              tags=("mejor",) if individuo == estado.mejor else ())
        self.dibujar()

    def preparar_grafica(self, canvas, titulo, xmin, xmax, ymin, ymax, etiqueta_x):
        canvas.delete("all")
        ancho, alto = max(canvas.winfo_width(), 100), max(canvas.winfo_height(), 100)
        izquierda, derecha, arriba, abajo = 72, ancho - 22, 45, alto - 42
        margen = max((ymax - ymin) * 0.08, 0.001)
        ymin, ymax = ymin - margen, ymax + margen
        xmax = max(xmax, xmin + 1e-9)

        def punto(x, y):
            return (izquierda + (x - xmin) / (xmax - xmin) * (derecha - izquierda),
                    abajo - (y - ymin) / (ymax - ymin) * (abajo - arriba))

        canvas.create_text(ancho / 2, 18, text=titulo, font=("TkDefaultFont", 10, "bold"))
        for i in range(5):
            y = ymin + (ymax - ymin) * i / 4
            _, py = punto(xmin, y)
            canvas.create_line(izquierda, py, derecha, py, fill="#e2e8f0")
            canvas.create_text(izquierda - 6, py, text=f"{y:.4g}", anchor="e")
        canvas.create_line(izquierda, arriba, izquierda, abajo, derecha, abajo, fill="#64748b")
        canvas.create_text(izquierda, abajo + 14, text=f"{xmin:g}")
        canvas.create_text(derecha, abajo + 14, text=f"{xmax:g}")
        canvas.create_text(ancho / 2, alto - 10, text=etiqueta_x)
        canvas.create_text(25, 30, text="f(x)")
        return punto

    def trazar(self, canvas, coordenadas, color):
        if len(coordenadas) > 1:
            canvas.create_line(*[valor for par in coordenadas for valor in par], fill=color, width=2)
        elif coordenadas:
            x, y = coordenadas[0]
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color)

    def dibujar(self):
        if not self.historial:
            return
        estado = self.historial[-1]
        a, b = self.problema.limite_inferior, self.problema.limite_superior
        poblacion = [(ind.valores[0], ind.objetivo) for ind in estado.poblacion]
        curva = []
        if self.parametros.dimensiones == 1:
            curva = [(a + (b - a) * i / 600, self.problema.funcion((a + (b - a) * i / 600,))) for i in range(601)]
        valores = [y for _, y in curva + poblacion]
        titulo = "Función y población actual" if curva else "Población: proyección x₁ frente a f(x₁, …, xn)"
        punto = self.preparar_grafica(self.poblacion_canvas, titulo, a, b, min(valores), max(valores), "x" if curva else "x₁ (las demás variables están en la tabla)")
        self.trazar(self.poblacion_canvas, [punto(x, y) for x, y in curva], "#94a3b8")
        for x, y in poblacion:
            px, py = punto(x, y)
            self.poblacion_canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#2563eb", outline="")
        px, py = punto(estado.mejor.valores[0], estado.mejor.objetivo)
        self.poblacion_canvas.create_oval(px - 6, py - 6, px + 6, py + 6, outline="#ea580c", width=3)

        valores = [valor for g in self.historial for valor in (g.mejor.objetivo, g.promedio, g.mejor_historico.objetivo)]
        punto = self.preparar_grafica(self.historia_canvas, "Evolución del objetivo (no pesos de ruleta)", 0,
                                     max(1, estado.numero), min(valores), max(valores), "Generación")
        for color, atributo in [("#2563eb", "promedio"), ("#ea580c", "mejor"), ("#16a34a", "mejor_historico")]:
            serie = []
            for g in self.historial:
                valor = getattr(g, atributo)
                serie.append(punto(g.numero, valor if atributo == "promedio" else valor.objetivo))
            self.trazar(self.historia_canvas, serie, color)


if __name__ == "__main__":
    ventana = tk.Tk()
    Interfaz(ventana)
    ventana.mainloop()
