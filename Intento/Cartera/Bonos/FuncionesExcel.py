import datetime
from math import exp, log
from time import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

import pyodbc
import Bonos.LibreriasUtiles.Util
import Bonos.LibreriasUtiles.UtilesValorizacion
from Bonos.Retornos import retorno_bonos

#----------------Funciones para trabajar en excel---------------------

def dataframe_datetime(tabla):

    """
    Cambia la columna fecha de la tabla de excel a un
    datetime, originalmente se encuentra en string

    """

    Fecha = tabla["Date"]
    nueva_fecha = []
    for i in range(len(Fecha)):

        fecha_drop = Fecha[i].split("-")
        fecha_string = datetime.datetime(int(fecha_drop[0]), int(fecha_drop[1]), int(fecha_drop[2]))
        nueva_fecha.append(fecha_string)
    
    tabla.drop(columns = ["Date"])
    tabla["Date"] = nueva_fecha
    return tabla

def tabla_excel_yahoo_retorno(nombreArchivo):

    """
    Extrae un archivo excel a un dataframe, calculando su valor de retorno
    con la funcion retorno_bonos
    
    """

    archivo = pd.read_csv('C:\\Users\\groso\\Desktop\\Practica\\Intento\\ArchivosExcel\\'+ nombreArchivo)
    Tabla = retorno_bonos(archivo["Adj Close"], archivo["Date"])
    Tabla = Tabla.drop(columns="Valor")
    nombre = nombreArchivo.split(".")[0]
    Tabla = Tabla.rename(columns={'Retorno':nombre })
    return Tabla

def tabla_bono_retorno(bono, nombre):

    """
    Calcula la tabla de retorno de un bono, renombrando
    la columna retorno con el nombre del bono para
    mejor entendimiento

    """

    Tabla = retorno_bonos(bono[0], bono[1])
    Tabla = Tabla.drop(columns="Valor")
    Tabla = Tabla.rename(columns={"Retorno":nombre})
    return Tabla

def unir_dataframes(datas):

    """
    Recibe una lista de tablas y las une con un join
    siendo la llave la fecha donde se calculo el retorno

    """

    tabla = []

    for i in range(len(datas)):

        tabla_actual = datas[i]
        if isinstance(tabla_actual["Date"][0], str):

            tabla_actual = dataframe_datetime(tabla_actual)

        if len(tabla) == 0:

            tabla = tabla_actual
        else:

            tabla = pd.merge(tabla, tabla_actual, on="Date")
    return tabla

def graficar_retornos(tablas, nombres):

    """
    Grafica los retornos para una cierta cantidad de tablas,
    recibe un vector de tablas que se quieren graficar
    y los nombre de cada valor

    """

    largo = len(tablas)
    for i in range(largo):

        plt.plot(tablas[i]["Date"][:], tablas[i][nombres[i]][:])
    plt.show()
