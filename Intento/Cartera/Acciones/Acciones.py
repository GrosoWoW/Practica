# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import sys
sys.path.append("..")
import numpy as np
import pandas as pd

from Bonos.Correlaciones import ewma
from Bonos.Curvas import seleccionar_bono_fecha, seleccionar_todos_bonos
from Bonos.Pivotes import *


# %%
def leer_archivo(nombreArchivo):

    """
    Extrae un archivo excel a un dataframe, calculando su valor de retorno
    con la funcion retorno_bonos
    
    """

    archivo = pd.read_excel('C:\\Users\\groso\\Desktop\\Practica\\Intento\\Cartera\\ArchivosExcel\\'+ nombreArchivo)
    columnas = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    archivo = archivo[columnas]

    return archivo



# %%
def retornos_acciones(nombreAccion):

    """
    Funcion encargada de calcular los retornos
    de una accion con la columna Adj Close
    :param nombreAccion: Nombre del archivo de la accion

    """

    tabla_accion = leer_archivo(nombreAccion)
    tabla_adj = tabla_accion["Adj Close"]
    fechas = tabla_accion["Date"]
    lenght = len(tabla_adj)
    arreglo = []

    for i in range(lenght):
        
        if i == 0:
            arreglo.append(0)

        else:
            valor = np.log(tabla_adj[i] / tabla_adj[i-1])
            arreglo.append(valor)

    df = pd.DataFrame({"Fecha": fechas, "Adj Close": tabla_adj, "Retornos": arreglo})
    return df



# %%
def volatilidades_acciones(retornos_acciones):

    """
    Funcion que calcula las volatilidades de una accion
    dado los retornos de esta
    :param retorno_acciones: DataFrame con los retornos de una accion
    :return DataFrame con las volatilidades

    """

    final = []
    lenght = len(retornos_acciones)

    calculo = ewma(retornos_acciones, 0.94)
    final.append(calculo["Vol c/ajuste"][0])

    df = pd.DataFrame({"Volatilidad": final})

    return df



# %%
def retorno_varias_acciones(nombreAcciones):

    """
    Funcion encargada del calculo de retornos
    para muchas acciones
    :param nombreAcciones: Vector con el nombre de el archivo de las acciones
    :return DataFrame con los retornos de cada accion

    """

    lenght = len(nombreAcciones)
    print(type(nombreAcciones))
    print(lenght)
    df = pd.DataFrame()
    for i in range(lenght):
        
        retornos = retornos_acciones(nombreAcciones[i])
        df[str(nombreAcciones[i]).split(".")[0]] = retornos["Retornos"]


    return df




# %%
def calculo_volatilidades_acciones(dfRetornos):

    """
    Funcion encargada de calcular las volatilidades
    para todas las acciones con el DataFrame de los retornos
    :param dfRetornos: DataFrame con todos los retornos de las acciones
    :return DataFrame con las volatilidad de cada accion

    """

    lenght = dfRetornos.shape[1]
    columnas = list(dfRetornos)
    df = pd.DataFrame()
    df["Empresa"] = columnas
    volatilidades = []

    for i in range(lenght):

        retornos = dfRetornos[columnas[i]]
        volatilidad = volatilidades_acciones(retornos)
        volatilidades.append(volatilidad.values[0][0]) 

    df["Volatilidades"] = volatilidades
    return df



# %%
def correlacion_acciones(dfRetornos, dfVolatilidades):

    """
    Funcion encargada de calcular la correlacion de las acciones
    :param dfRetornos: DataFrame con todos los retornos de las acciones
    :param dfVolatilidades: DataFrame con las volatilidades de las acciones
    :return DataFrame con la matriz de correlacion

    """

    num_acciones = len(dfVolatilidades)
    correlacion = ewma_new_new_pivotes(num_acciones, dfRetornos, dfVolatilidades)
    return correlacion




# %%
def covarianza_acciones(dfRetornos, dfVolatilidades):

    """
    Funcion encargada de calcular la covarianza de las acciones
    :param dfRetornos: DataFrame con los retornos de todas las acciones
    :param dfVolatilidades: DataFrame con la volatilidad de las acciones
    :return DataFrame con la matriz de covarianza de las acciones

    """

    num_acciones = len(dfVolatilidades)
    covarianza = covarianza_pivotes(num_acciones, dfRetornos, dfVolatilidades)
    return covarianza


