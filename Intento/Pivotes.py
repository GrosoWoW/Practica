import datetime

import math

import pandas as pd

import numpy as np

from Correlaciones import ewma, ewma_new_new
from Curvas import (get_cnn, seleccionar_bono_fecha, seleccionar_NS_fecha,
                    seleccionar_todos_bonos)
from Retornos import retorno_bonos, retorno_factor
from Util import add_days
from UtilesDerivados import siguiente_habil_pais, ultimo_habil_pais
from UtilesValorizacion import StrTabla2ArrTabla, diferencia_dias_convencion
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

def calculo_volatilidades(bonos):

    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]
    volatilidades = []

    for i in range(len(vector_dias)):

        historico_factor = evaluacion_curva(vector_dias[i], "ACT360")
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

    vol = calculo_volatilidades(bonos)
    vol = np.array(seleccionar_volatilidades(vol))
    fecha = fecha_vector(bonos)
    tir = tir_vector(fecha[0])
    volatilidades = []

    for i in range(len(vector_dias)):

        volatilidades.append(vol[i])

    df = pd.DataFrame({"Fecha": fecha, "TIR": tir, "volatilidad": volatilidades})
    return df


def entre_pivotes(fecha, pivotes):

    """
    Funcion que se encarga de encontrar los dos pivotes
    que limitan a la fecha entregada, es decir los pivotes necesarios
    para el calculo
    :param fecha: Fecha del pago al que se buscaran sus limites
    :param pivotes: Todos los pivotes calculados

    """
    largo = len(pivotes["Fecha"])
    for i in range(largo):

        fecha_probable = pivotes["Fecha"][i]
        if i == 0 and fecha_probable > fecha:

            return [pivotes.iloc[i], pivotes.iloc[i]]

        elif i == largo - 1 :

            return [pivotes.iloc[i], pivotes.iloc[i]]

        elif fecha < fecha_probable:

            return [pivotes.iloc[i], pivotes.iloc[i+1]]

def alfa_0(fecha_inicial, pivote1, pivote2, flujo):

    """
    Funcion para el calculo de alfa_0, para utilizar en la funcion
    :param fecha_inicial: Fecha de el dia 0 del calculo
    :param pivote1: Primer pivote del intervalo de fechas
    :param pivote2: Segundo pivote del intervalo de fechas
    :param flujo: Fecha en donde se realizo el pago
    (en dias)

    """
    D_flujo = diferencia_dias_convencion("ACT360", fecha_inicial, flujo)/360
    D_pivote1 = diferencia_dias_convencion("ACT360", fecha_inicial, pivote1)/360
    D_pivote2 = diferencia_dias_convencion("ACT360", fecha_inicial, pivote2)/360
    calculo = (D_flujo - D_pivote1)/(D_pivote2 - D_pivote1)
    return calculo

def TIR_flujo(alfa, TIR_pivote1, TIR_pivote2):

    """
    Funcion para el calculo de Tir del flujo
    :param alfa: Valor del alfa_0 calculado en la funcion alfa_0
    :param TIR_pivote1: Valor del tir en el pivote 1
    :param TIR_pivote2: Valor del tir en el pivote 2

    """

    calculo = alfa * TIR_pivote1 + (1 - alfa)*TIR_pivote2
    return calculo

def volatilidad_flujo(alfa, volatilidad_pivote1, volatilidad_pivote2):

    """
    Funcion del calculo de Volatilidad del flujo
    :param alfa: Valor de alfa calculado en la funcion alfa_0
    :param volatilidad_pivote1: Volatilidad del pivote1
    :param volatilidad_pivote2: Volatilidad del pivote2

    """   

    calculo = alfa * volatilidad_pivote1 + (1 - alfa) * volatilidad_pivote2
    return calculo

def correlacion_pivotes(pivotes):

    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

    df = pd.DataFrame()
    for i in range(len(vector_dias)):

        historico_factor = evaluacion_curva(vector_dias[i], "ACT360")
        df_s = pd.DataFrame(historico_factor, columns=["Historico"])
        retorno = np.array(retorno_factor(df_s))
        df[str(vector_dias[i])] = retorno

    correlacion = ewma_new_new(len(vector_dias), df, pivotes["volatilidad"])
    return correlacion


def solucion_ecuacion(sigma_flujo, sigma_pivote1, sigma_pivote2, ro):

    A = (sigma_pivote1**2 + sigma_pivote2**2 - 2*ro*sigma_pivote1*sigma_pivote2)
    B = (2 * ro * sigma_pivote1* sigma_pivote2 - 2*sigma_pivote2**2)
    C = (sigma_pivote2**2 - sigma_flujo**2)

    x1 = (-B+math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte positiva
    x2 = (-B-math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte negativa

    return[x1, x2]

def calculo(bono):

    piv = pivotes(bono)
    primera_fecha = piv["Fecha"][0]
    fecha_emision = piv["Fecha"][0]
    correlacion = correlacion_pivotes(piv)
    print(correlacion)


    for i in range(len(np.array(bono["Fecha"]))):

        tabla = StrTabla2ArrTabla(bono["TablaDesarrollo"][i], str(bono["FechaEmision"][i]).split(" ")[0]) #Se crea la tabla de desarrollo del bono
        dfTabla_bono = pd.DataFrame(tabla, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])

        for j in range(len(np.array(dfTabla_bono["Numero"]))):

            fecha_inicial = dfTabla_bono["Fecha"][j]

            fecha = dfTabla_bono["Fecha"][j]
            pivote = entre_pivotes(fecha, piv)
            alfa = alfa_0(fecha_inicial, pivote[0]["Fecha"], pivote[1]["Fecha"], fecha)
            pivote1 = np.array(pivote)[0]
            pivote2 = np.array(pivote)[1]
            TIR_pivote1 = pivote1[1]
            TIR_pivote2 = pivote2[1]
            TIR_fluj = TIR_flujo(alfa, TIR_pivote1, TIR_pivote2)
            volatilidad_pivote1 = pivote1[2]
            volatilidad_pivote2 = pivote2[2]
            volatilidad_fluj = volatilidad_flujo(alfa, volatilidad_pivote1, volatilidad_pivote2)
            diferencia_dia1 = (pivote1[0] - primera_fecha).days
            diferencia_dia2 = (pivote2[0] - primera_fecha).days


            print(solucion_ecuacion(volatilidad_fluj, volatilidad_pivote1, volatilidad_pivote2, correlacion[str(diferencia_dia1)][str(diferencia_dia2)] ))

         

bonos = seleccionar_todos_bonos("CLP")
bono = seleccionar_bono_fecha(str(primer_dia(bonos)))
piv = pivotes(bonos)
correlacion_pivotes(piv)

fecha_new = datetime.datetime(2014, 6, 2)
calculo(bonos)
