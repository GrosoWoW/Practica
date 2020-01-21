import datetime
from math import exp, log
from time import time                                   

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

import pyodbc
from Correlaciones import ewma_new_new
from Curvas import (get_cnn, seleccionar_bono, seleccionar_bonos_moneda,
                    seleccionar_curva_derivados, seleccionar_curva_NS)
from FuncionesExcel import (graficar_retornos, tabla_bono_retorno,
                            tabla_excel_yahoo_retorno, unir_dataframes)
from LibreriasUtiles.Matematica import interpolacion_log_escalar
from LibreriasUtiles.UtilesValorizacion import (StrTabla2ArrTabla, add_days,
                                diferencia_dias_convencion, factor_descuento,
                                parsear_curva)


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

#-------------------Valorizacion con Pivotes----------------

def historico_factor_descuento(dia, convencion):

    curvans = seleccionar_curva_NS("IF#CLP")
    factor = []

    for i in range(len(curvans["ancla"][:])):


        dia_inicial = curvans["Fecha"][i]

        tir = TIR_n(dia, curvans["ancla"][i], curvans["y0"][i], curvans["y1"][i], curvans["y2"][i])
        difinal = add_days(dia_inicial, dia)
        factor.append(factor_descuento(tir, curvans["Fecha"][i], difinal, convencion, 0 ))
    
    return factor
       
"""
f, ax = plt.subplots()
ax.plot(historico_factor_descuento(30, "ACT360"), label="30 dias")
ax.plot(historico_factor_descuento(60, "ACT360"), label="60 dias")
ax.plot(historico_factor_descuento(90, "ACT360"), label="90 dias")
ax.plot(historico_factor_descuento(365, "ACT360"), label="365 dias")
ax.plot(historico_factor_descuento(365*2, "ACT360"), label = "365*2 dias")
ax.plot(historico_factor_descuento(365*3, "ACT360"), label = "365*3 dias")
ax.plot(historico_factor_descuento(365*4, "ACT360"), label = "365*4 dias")
ax.plot(historico_factor_descuento(365*5, "ACT360"), label = "365*5 dias")
ax.plot(historico_factor_descuento(365*10, "ACT360"), label = "365*10 dias")
ax.plot(historico_factor_descuento(365*15, "ACT360"), label = "365*15 dias")
ax.plot(historico_factor_descuento(365*20, "ACT360"), label = "365*20 dias")
ax.plot(historico_factor_descuento(365*40, "ACT360"), label = "365*40 dias")
ax.plot(historico_factor_descuento(365*80, "ACT360"), label = "365*80 dias")
ax.set_title("oowoo")
ax.set_xlabel("awa")
ax.set_ylabel("ewe")
ax.legend()

plt.show()
"""