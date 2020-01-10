import pyodbc
import pandas as pd
from UtilesValorizacion import StrTabla2ArrTabla, diferencia_dias_convencion, factor_descuento, parsear_curva
from Matematica import interpolacion_log_escalar
import datetime
import numpy as np
from math import exp, log
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from time import time
from FuncionesExcel import tabla_excel_yahoo_retorno, tabla_bono_retorno, unir_dataframes, graficar_retornos
from Curvas import seleccionar_bonos_moneda, seleccionar_curva_NS, seleccionar_bono, get_cnn, seleccionar_curva_derivados
from Correlaciones import ewma_new_new

"""
Funciones principales para calcular datos de un bono
Como su valor, historico, graficas, etc

"""

# Calcula la suma total del tir
def TIR(s, ancla, y0, y1, y2):

    """
    Calculo de los valores del TIR con todos los periodos
    de pago (entregados por el parametro s)

    """

    coef = np.zeros(4)
    coef[0] = ancla
    coef[1] = y0
    coef[2] = y1
    coef[3] = y2
    vector = np.zeros(len(s))

    for i in range(1, len(s)):
        vector[i] = coef[1] + (coef[0] - coef[1]) * (1 - np.exp(-s[i] / coef[2])) * (coef[2] / s[i]) + coef[3] * (
            (1 - np.exp(-s[i] / coef[2])) * (coef[2] / s[i]) - np.exp(-s[i] / coef[2]))

    return vector

#Calcula un factor del tir dependiendo la curva y n
def TIR_n(n, ancla, y0, y1, y2):

    """
    Caluclo del TIR para un pago en especifico, el cual
    corresponde al valor de n

    """

    coef = np.zeros(4)
    coef[0] = ancla
    coef[1] = y0
    coef[2] = y1
    coef[3] = y2
    valor = 0
    valor = coef[1] + (coef[0] - coef[1]) * (1 - np.exp(-n / coef[2])) * (coef[2] / n) + coef[3] * (
        (1 - np.exp(-n / coef[2])) * (coef[2] / n) - np.exp(-n / coef[2]))

    return valor

# Calculo de valor del bono

def valor_bono_derivados(bono, curva_derivados):

    """
    Calculo de un valor del bono con el tipo de curva
    de derivados, con la utilizacion de la interpolacion
    logaritmica

    """

    tabla_desarrollo = StrTabla2ArrTabla(bono.values[0][1], str(bono.values[0][0]).split(" ")[0])
    dfTabla = pd.DataFrame(tabla_desarrollo, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
    fecha_inicial = datetime.datetime.now()
    largo = dfTabla[["Numero"]].shape[0]
    convencion = "ACT360"

    suma = 0
    historico = []

    for i in range(largo):

        diferencia = diferencia_dias_convencion(convencion, fecha_inicial, dfTabla["Fecha"][i])
        if (diferencia > 0):

            tir = interpolacion_log_escalar(diferencia, curva_derivados)
            valor = (dfTabla["Cupon"][i])*(factor_descuento(tir, fecha_inicial, dfTabla["Fecha"][i], convencion, 0))
            historico.append(valor)
            suma += valor

    return suma
            
#--------------------Historico de precio---------------------

def parsear_convenciones(df_tabla):
    convenciones = []
    for i in range(df_tabla.shape[0]):
        if df_tabla.loc[0].Base1 == -1:
            s = "ACT"
        else:
            s = str(df_tabla.loc[0].Base1) + '/'
        convenciones.append(s+str(df_tabla.loc[0].Base2))
    return convenciones

curva_ns_1 = seleccionar_curva_NS("IF#CLP")

def valor_bono(bono, curva):

    """
    Calcula el valor del bono con todos sus cupones
    Recibe el bono a calcular el valor, y la curva 
    que se utilizara para el calculo
    
    """

    tabla = StrTabla2ArrTabla(bono["TablaDesarrollo"][0], str(bono["FechaEmision"][0]).split(" ")[0]) #Se crea la tabla de desarrollo del bono
    dfTabla_bono = pd.DataFrame(tabla, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
    cantidad_pagos = dfTabla_bono["Cupon"].shape[0]
    convencion = parsear_convenciones(bono)
    suma = 0

    for i in range(cantidad_pagos):

        #Diferencia entre la curva y el pago del bono
        diferencia_dias = diferencia_dias_convencion(convencion[0], curva.Fecha, dfTabla_bono["Fecha"][i]) 

        if (diferencia_dias > 0):

            tir = TIR_n(diferencia_dias, curva.ancla, curva.y0, curva.y1, curva.y2)
            factor = factor_descuento(tir, curva.Fecha, dfTabla_bono["Fecha"][i], convencion[0], 0)
            suma += factor * dfTabla_bono["Cupon"][i]

    return suma

def total_historico(bonos):

    """
    Calcula el valor de un bono con todas las curvas que se encuentran
    en la base de datos, entrega una matriz con el eje x e y correspondiente

    """

    curvas = seleccionar_curva_NS("IF#CLP")
    largo = curvas.shape[0]
    valorBono = []
    indices = []
    
    for i in range(largo):

        fecha_curvas = curvas.loc[i].Fecha
        diferencia = bonos["FechaEmision"][0] - fecha_curvas
        
        if(diferencia.days < 0):
            curva = curvas.loc[i]
            calculo_bono = valor_bono(bonos, curva)
            valorBono.append(calculo_bono)
            indices.append(fecha_curvas)
    
    return [valorBono[::-1], indices[::-1]]

def auto_bono(Nemotecnico):

    """
    Selecciona un bono respecto a su nemotecnico
    y calcula el total historico de este

    """

    bono = seleccionar_bono(Nemotecnico)
    bono = total_historico(bono)
    return bono

def plot_bonos(arregloBonos):

    """
    Grafica el total historico de un arreglo de bonos

    """

    largo = len(arregloBonos)
    for i in range(largo):

        bonos = auto_bono(arregloBonos[i])
        plt.plot(bonos[1], bonos[0])
        
    plt.show()