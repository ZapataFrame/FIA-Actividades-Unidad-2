"""Comparación reproducible antes/después, sin Qt ni paquetes adicionales.

La referencia inicial se obtiene del Git local; no usa la red. Registra todos
los resultados y tiempos, incluidos casos que se estancan o empeoran.
"""
import argparse
import csv
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from genetico import Parametros, RegresionSimbolica

CASOS = {
    'parabola': lambda x:x*x+x+1,
    'coeficientes': lambda x:2.7*x*x-1.3*x+.45,
    'trigonometrica': lambda x:1.8*math.sin(x)+.7,
    'cubica': lambda x:x**3-2*x+.5,
}


def principal():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--referencia',default='2076471')
    parser.add_argument('--poblacion',type=int,default=80)
    parser.add_argument('--generaciones',type=int,default=60)
    parser.add_argument('--semillas',type=int,nargs='+',default=[7,21,42])
    parser.add_argument('--salida',default='resultados/comparacion_busqueda.csv')
    args=parser.parse_args()
    raiz=Path(__file__).resolve().parent.parent
    original=subprocess.check_output(['git','show',f'{args.referencia}:arbol_expresiones/genetico.py'],cwd=raiz,text=True)
    filas=[]
    with tempfile.TemporaryDirectory() as temporal:
        archivo=Path(temporal)/'original.py'
        archivo.write_text(original)
        spec=importlib.util.spec_from_file_location('motor_original',archivo)
        base=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=base
        spec.loader.exec_module(base)
        for nombre,funcion in CASOS.items():
            puntos=[(i/4,funcion(i/4)) for i in range(-12,13)]
            for semilla in args.semillas:
                for variante in ('original','genetico_actual','hibrido_actual'):
                    comunes=dict(poblacion=args.poblacion,generaciones=args.generaciones,semilla=semilla)
                    if variante=='original':
                        motor=base.RegresionSimbolica(puntos,base.Parametros(**comunes))
                    else:
                        activo=variante=='hibrido_actual'
                        motor=RegresionSimbolica(puntos,Parametros(**comunes,ajuste_lineal=activo,refinar_constantes=activo))
                    inicio=time.monotonic()
                    ultimo=None
                    for ultimo in motor.evolucionar():
                        pass
                    mse=dict(ultimo.mejor_historico.metricas).get('mse',math.inf)
                    diversidad=len({i.expresion for i in ultimo.individuos})/len(ultimo.individuos)
                    filas.append(dict(caso=nombre,semilla=semilla,variante=variante,mse=mse,
                                      generaciones=ultimo.numero,segundos=time.monotonic()-inicio,
                                      diversidad=diversidad,expresion=ultimo.mejor_historico.expresion,
                                      poblacion=args.poblacion,limite_generaciones=args.generaciones))
                    print(nombre,semilla,variante,f'MSE={mse:.6g}',flush=True)
    salida=Path(args.salida)
    salida.parent.mkdir(parents=True,exist_ok=True)
    with salida.open('w',newline='',encoding='utf-8') as archivo:
        escritor=csv.DictWriter(archivo,fieldnames=filas[0])
        escritor.writeheader(); escritor.writerows(filas)
    print('Guardado:',salida)


if __name__=='__main__':
    principal()
