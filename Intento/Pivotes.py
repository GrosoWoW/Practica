import datetime

import pandas as pd

import numpy as np

from Correlaciones import ewma
from Curvas import (get_cnn, seleccionar_bono_fecha, seleccionar_NS_fecha,
                    seleccionar_todos_bonos)
from Retornos import retorno_bonos, retorno_factor
from Util import add_days
from UtilesDerivados import siguiente_habil_pais, ultimo_habil_pais
from UtilesValorizacion import StrTabla2ArrTabla
from ValorizacionBonos import TIR_n, total_historico, evaluacion_curva

#----------------------Pivotes---------------------------------------

"""
A continuacion se presentan las funciones principales para realizar 
calculos de valorizaciones de bonos con el metodo Risk metrics, con
la utilizacion de pivotes

"""

vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]


def intervalo_pivotes(bonos):

    """
    Calcula el intervalo de los bonos, es decir la fecha inicial
    del bono mas antiguo hasta la fecha final mas tardia
    :param bonos: Pandas de bonos que se calculara el intervalo

    """

    maximo = min(bonos["FechaEmision"])
    minimo = max(bonos["FechaVenc"])
    return [minimo, maximo]

def primer_dia(bonos):

    """
    Calcula el primer dia de los bonos y lo transforma al formate
    datetime.datetime
    :param bonos: Pandas con bonos que se calculara el dia

    """

    fecha_actual = intervalo_pivotes(bonos)[1]
    fecha_actual = ultimo_habil_pais(fecha_actual, "CL", get_cnn())
    fecha_actual = datetime.datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day)
    return fecha_actual

def fecha_vector(bonos):

    fecha_actual = primer_dia(bonos)  # Minimo
    nuevos_dias = []
    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

    vector_dias[0] = (intervalo_pivotes(bonos)[1] - fecha_actual).days

    for i in range(len(vector_dias)):

        fecha_nueva = fecha_actual + datetime.timedelta(vector_dias[i]) 
        nuevos_dias.append(fecha_nueva)
    return nuevos_dias
    

def tir_vector(primeraFecha):

    """
    Calcula el vector de TIR para cierta fecha inicial, los tirs se calculan
    para los intervales de dias que se encuentran en vector_dias
    :param primeraFecha: Primer dia donde se calculara el vector de tir

    """

    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]
    tir_vector = []
    curva_ns = seleccionar_NS_fecha(str(primeraFecha))
    for i in range(len(vector_dias)):

        tir =  TIR_n(vector_dias[i], curva_ns["ancla"][0], curva_ns["y0"][0], curva_ns["y1"][0], curva_ns["y2"][0])
        tir_vector.append(tir)


    return tir_vector


def volatilidad_vector(cantidadDia, retorno):

    """
    Calcula el ewma (para volatilidad) de un vector de retornos,
    hasta una cierta cantidad de dias
    :param cantidadDia: El numero de dias que se quiere calcular el ewma
    :param retorno: Pandas con los retornos que se utilizaran en el calculo

    """

    euma = ewma(retorno["Retorno"][:cantidadDia], 0.94)
    return euma

def unir_vectores(bonos):



    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]
    fechas = fecha_vector(bonos)
    dif = (max(fechas) - min(fechas)).days
    volatilidades = []

    for i in range(len(vector_dias)):

        historico_factor = evaluacion_curva(vector_dias[i], "LACT360")
        df = pd.DataFrame(historico_factor, columns=["Historico"])
        retorno = np.array(retorno_factor(df))
        volatilidad = ewma(retorno, 0.94)["Vol c/ajuste"][0]
        volatilidades.append(volatilidad)
    
    dataFrame = pd.DataFrame({"Volatilidad": volatilidades})
    return dataFrame

def seleccionar_volatilidades(volatilidades):

    volatilidad = volatilidades["Volatilidad"]
    return volatilidad

def pivotes(bonos):

    """
    Calculo de los pivoste con sus respectivos valores de TIR y
    de volatilidad, tambien presentan las fechas que se utilizaran
    en estos
    :param bonos: Pandas con los bonos a los que se crearan los pivotes

    """

    vol = unir_vectores(bonos)
    vol = np.array(seleccionar_volatilidades(vol))
    fecha = fecha_vector(bonos)
    tir = tir_vector(fecha[0])
    volatilidades = []
    print(vol)

    for i in range(len(vector_dias)):

        volatilidades.append(vol[i])

    print(vol)
    print(tir)
    print(volatilidades)

    df = pd.DataFrame({"Fecha": fecha, "TIR": tir, "volatilidad": volatilidades})
    print(df)

bonos = seleccionar_todos_bonos("CLP")
bono = seleccionar_bono_fecha(str(primer_dia(bonos)))

print(pivotes(bonos))
