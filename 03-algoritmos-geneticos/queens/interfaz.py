"""Ventana sencilla para ver la población y el tablero de cualquier individuo."""

import tkinter as tk
from tkinter import messagebox, ttk

from algoritmo import Parametros, criterio_parada, evolucionar, obtener_colisiones


class Interfaz:
    def __init__(self, ventana):
        self.ventana = ventana
        self.historial = []
        self.ejecucion = None
        self.temporizador = None
        self.campos = {}
        ventana.title("Proyecto 3 · n reinas con algoritmo genético")
        ventana.geometry("1080x820")
        ventana.minsize(940, 720)

        controles = ttk.LabelFrame(ventana, text="Configura y pulsa Reiniciar para aplicar los cambios", padding=8)
        controles.pack(fill="x", padx=12, pady=8)
        p = Parametros()
        especificaciones = [
            ("N reinas", "n", p.n),
            ("Población", "tamano_poblacion", p.tamano_poblacion),
            ("Límite de generaciones", "generaciones", p.generaciones),
            ("Cruce por pareja (0–1)", "prob_cruce", p.prob_cruce),
            ("Mutación por individuo (0–1)", "prob_mutacion", p.prob_mutacion),
            ("Élites (0 = sin)", "elites", p.elites),
            ("Semilla", "semilla", p.semilla),
            ("Pausa entre pasos (ms)", "pausa", 150),
        ]
        for indice, (nombre, clave, valor) in enumerate(especificaciones):
            fila, columna = indice // 3, 2 * (indice % 3)
            ttk.Label(controles, text=nombre).grid(row=fila, column=columna, padx=(0, 6), pady=3, sticky="w")
            campo = ttk.Entry(controles, width=9)
            campo.insert(0, str(valor))
            campo.grid(row=fila, column=columna + 1, padx=(0, 15), sticky="w")
            self.campos[clave] = campo

        botones = ttk.Frame(ventana)
        botones.pack(fill="x", padx=12)
        for titulo, accion in [("Reiniciar", self.reiniciar), ("Siguiente generación", self.avanzar),
                               ("Reproducir", self.reproducir), ("Pausar", self.pausar)]:
            ttk.Button(botones, text=titulo, command=accion).pack(side="left", padx=(0, 8))
        self.resumen = tk.StringVar()
        etiqueta = ttk.Label(ventana, textvariable=self.resumen, padding=(12, 8))
        etiqueta.pack(fill="x")
        etiqueta.bind("<Configure>", lambda evento: etiqueta.configure(wraplength=max(100, evento.width - 24)))

        vistas = ttk.Frame(ventana)
        vistas.pack(fill="both", expand=True, padx=12)
        self.tablero = tk.Canvas(vistas, background="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.grafica = tk.Canvas(vistas, background="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.tablero.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.grafica.pack(side="left", fill="both", expand=True)
        self.tablero.bind("<Configure>", lambda evento: self.dibujar_tablero())
        self.grafica.bind("<Configure>", lambda evento: self.dibujar_evolucion())
        ttk.Label(ventana, text="Tablero: rojo = reina en conflicto; azul = sin conflicto. Selecciona una fila para ver otro individuo.").pack(pady=5)

        marco = ttk.LabelFrame(ventana, text="Población actual · el mejor aparece resaltado", padding=5)
        marco.pack(fill="x", padx=12, pady=(0, 10))
        self.tabla = ttk.Treeview(marco, columns=("numero", "genes", "colisiones"), show="headings", height=7, selectmode="browse")
        for clave, titulo, ancho in [("numero", "#", 45), ("genes", "Filas por columna (1…n)", 650),
                                     ("colisiones", "Pares en conflicto", 160)]:
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=ancho, minwidth=45)
        vertical = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(marco, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="ew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        marco.columnconfigure(0, weight=1)
        self.tabla.tag_configure("mejor", background="#fff0d6")
        self.tabla.bind("<<TreeviewSelect>>", lambda evento: self.dibujar_tablero())
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.reiniciar()

    def leer_parametros(self):
        valores = {}
        for clave, campo in self.campos.items():
            convertir = float if clave in ("prob_cruce", "prob_mutacion") else int
            valores[clave] = convertir(campo.get())
        pausa = valores.pop("pausa")
        if pausa < 1:
            raise ValueError("La pausa debe ser ≥ 1 ms.")
        # Límites de la ventana para mantener legible el tablero y la tabla.
        if not 1 <= valores["n"] <= 10000:
            raise ValueError("En la interfaz usa de 1 a 32 reinas.")
        if not 2 <= valores["tamano_poblacion"] <= 1000 or not 0 <= valores["generaciones"] <= 5000:
            raise ValueError("Usa población 2–1000 y límite de generaciones 0–5000.")
        return Parametros(**valores), pausa

    def reiniciar(self):
        self.pausar()
        try:
            parametros, pausa = self.leer_parametros()
            ejecucion = evolucionar(parametros)
            inicial = next(ejecucion)
        except ValueError as error:
            messagebox.showerror("Revisa los parámetros", str(error))
            return
        self.parametros, self.pausa, self.ejecucion = parametros, pausa, ejecucion
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
        return not criterio_parada(estado, self.parametros)

    def reproducir(self):
        # Un paso por callback: la ventana puede procesar el botón Pausar.
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
        if estado.mejor.colisiones == 0:
            situacion = "Solución encontrada: 0 pares en conflicto"
        elif estado.numero >= self.parametros.generaciones:
            situacion = "Límite alcanzado sin solución"
        else:
            situacion = "Búsqueda en curso"
        if self.parametros.n in (2, 3):
            situacion += " · n=2 y n=3 no tienen solución"
        distintos = len({ind.genes for ind in estado.poblacion})
        self.resumen.set(
            f"{situacion}\nGeneración {estado.numero}/{self.parametros.generaciones} · "
            f"Mejor (pares): {estado.mejor.colisiones} · Promedio: {estado.promedio:.2f} · "
            f"Mejor histórico: {estado.mejor_historico.colisiones} · Individuos distintos: {distintos}/{len(estado.poblacion)}"
        )
        self.tabla.delete(*self.tabla.get_children())
        ancho = max(650, self.parametros.n * 35)
        self.tabla.column("genes", width=ancho, minwidth=ancho)
        for indice, individuo in enumerate(estado.poblacion):
            self.tabla.insert("", "end", iid=str(indice), values=(indice + 1, str(individuo.genes), individuo.colisiones),
                              tags=("mejor",) if individuo == estado.mejor else ())
        mejor_indice = estado.poblacion.index(estado.mejor)
        self.tabla.selection_set(str(mejor_indice))
        self.tabla.see(str(mejor_indice))
        self.dibujar_tablero()
        self.dibujar_evolucion()

    def dibujar_tablero(self):
        if not self.historial:
            return
        self.tablero.delete("all")
        seleccion = self.tabla.selection()
        indice = int(seleccion[0]) if seleccion else self.historial[-1].poblacion.index(self.historial[-1].mejor)
        individuo = self.historial[-1].poblacion[indice]
        n = self.parametros.n
        ancho, alto = self.tablero.winfo_width(), self.tablero.winfo_height()
        lado = max(1, min(ancho - 70, alto - 75))
        celda = lado / n
        izquierda, arriba = (ancho - lado) / 2, 40
        self.tablero.create_text(ancho / 2, 17, text=f"Individuo {indice + 1} · Pares en conflicto: {individuo.colisiones}",
                                font=("TkDefaultFont", 10, "bold"))

        def centro(columna):
            return (izquierda + (columna + 0.5) * celda, arriba + (individuo.genes[columna] - 0.5) * celda)

        for fila in range(n):
            for columna in range(n):
                x, y = izquierda + columna * celda, arriba + fila * celda
                color = "#e2e8f0" if (fila + columna) % 2 else "#f8fafc"
                self.tablero.create_rectangle(x, y, x + celda, y + celda, fill=color, outline="#cbd5e1")
        for i in range(n):
            self.tablero.create_text(izquierda + (i + 0.5) * celda, arriba + lado + 12, text=str(i + 1), font=("TkDefaultFont", 8))
            self.tablero.create_text(izquierda - 14, arriba + (i + 0.5) * celda, text=str(i + 1), font=("TkDefaultFont", 8))
        pares = obtener_colisiones(individuo.genes)
        atacadas = {columna for par in pares for columna in par}
        for i, j in pares:
            self.tablero.create_line(*centro(i), *centro(j), fill="#ef4444", width=1)
        radio = celda * 0.3
        for columna in range(n):
            x, y = centro(columna)
            color = "#dc2626" if columna in atacadas else "#2563eb"
            self.tablero.create_oval(x - radio, y - radio, x + radio, y + radio, fill=color, outline="")
            if celda >= 22:
                self.tablero.create_text(x, y, text="R", fill="white", font=("TkDefaultFont", max(8, int(celda * 0.23)), "bold"))
        self.tablero.create_text(ancho / 2, alto - 12, text="Columna → · Filas numeradas desde arriba")

    def dibujar_evolucion(self):
        if not self.historial:
            return
        self.grafica.delete("all")
        ancho, alto = self.grafica.winfo_width(), self.grafica.winfo_height()
        izquierda, derecha, arriba, abajo = 52, max(53, ancho - 20), 45, max(46, alto - 45)
        ultimo = max(1, self.historial[-1].numero)
        maximo = max(1, max(g.promedio for g in self.historial)) * 1.1

        def punto(generacion, valor):
            return izquierda + generacion / ultimo * (derecha - izquierda), abajo - valor / maximo * (abajo - arriba)

        self.grafica.create_text(ancho / 2, 17, text="Pares en conflicto · menor es mejor", font=("TkDefaultFont", 10, "bold"))
        for i in range(5):
            valor = maximo * i / 4
            _, y = punto(0, valor)
            self.grafica.create_line(izquierda, y, derecha, y, fill="#e2e8f0")
            self.grafica.create_text(izquierda - 6, y, text=f"{valor:.1f}", anchor="e")
        self.grafica.create_line(izquierda, arriba, izquierda, abajo, derecha, abajo, fill="#64748b")
        self.grafica.create_text(izquierda, abajo + 12, text="0")
        self.grafica.create_text(derecha, abajo + 12, text=str(ultimo))
        self.grafica.create_text(ancho / 2, alto - 10, text="Generación · azul: promedio, naranja: mejor, verde: histórico")
        for atributo, color in [("promedio", "#2563eb"), ("mejor", "#ea580c"), ("mejor_historico", "#16a34a")]:
            puntos = []
            for g in self.historial:
                valor = getattr(g, atributo)
                puntos.extend(punto(g.numero, valor if atributo == "promedio" else valor.colisiones))
            if len(puntos) >= 4:
                self.grafica.create_line(*puntos, fill=color, width=2, dash=(4, 3) if atributo == "mejor_historico" else ())
            else:
                x, y = puntos
                self.grafica.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")


if __name__ == "__main__":
    ventana = tk.Tk()
    Interfaz(ventana)
    ventana.mainloop()
