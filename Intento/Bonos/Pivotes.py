import datetime
import math

import numpy as np
import pandas as pd
from openpyxl.workbook import Workbook

from Correlaciones import (covarianza_pivotes, ewma, ewma_new_new,
                           ewma_new_new_pivotes)
from Curvas import (get_cnn, seleccionar_bono_fecha, seleccionar_NS_fecha,
                    seleccionar_todos_bonos)
from Retornos import retorno_bonos, retorno_factor
from LibreriasUtiles.Util import add_days
from LibreriasUtiles.UtilesDerivados import siguiente_habil_pais, ultimo_habil_pais
from LibreriasUtiles.UtilesValorizacion import (StrTabla2ArrTabla, diferencia_dias_convencion,
                                plazo_anual_convencion)
from ValorizacionBonos import (TIR_n, historico_factor_descuento,
                               total_historico)

#----------------------Pivotes---------------------------------------

"""
A continuacion se presentan las funciones principales para realizar 
calculos de valorizaciones de bonos con el metodo Risk metrics, con
la utilizacion de pivotes. 

"""

vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

def intervalo_pivotes():

    """
    Calcula el intervalo de los bonos, es decir la fecha inicial
    del bono mas antiguo hasta la fecha final mas tardia
    :param bonos: Pandas de bonos que se calculara el intervalo

    """

    curvas = ("SELECT * FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = 'IF#CLP' ORDER BY 'Fecha' DESC")
    curvas = pd.read_sql(curvas, get_cnn())
    return curvas["Fecha"][0]

def primer_dia(bonos):

    """
    Calcula el primer dia de los bonos y lo transforma al formate
    datetime.datetime
    :param bonos: Pandas con bonos que se calculara el dia

    """

    fecha_actual = intervalo_pivotes()
    fecha_actual = ultimo_habil_pais(fecha_actual, "CL", get_cnn())
    fecha_actual = datetime.datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day)
    return fecha_actual

def fecha_vector(bonos):

    """
    Funcion que calcula el vector de fechas de los pivotes
    :param bonos: Bonos que se les calcularan las fechas de los pivotes

    """

    fecha_actual = primer_dia(bonos)  # Minimo
    nuevos_dias = []
    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

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
    fecha_tentativa = ultimo_habil_pais(primeraFecha.date(), "CL", get_cnn())
    fecha_tentativa = datetime.datetime(fecha_tentativa.year, fecha_tentativa.month, fecha_tentativa.day)
    curva_ns = seleccionar_NS_fecha(str("2018-12-28 00:00:00"))
    for i in range(len(vector_dias)):

        tir =  TIR_n(vector_dias[i], curva_ns["ancla"][0], curva_ns["y0"][0], curva_ns["y1"][0], curva_ns["y2"][0])
        tir_vector.append(tir)


    return tir_vector

def calculo_volatilidades(bonos):

    """
    Funcion que calcula las volatilidades para cada pivote, con el historico 
    de factores de descuento
    :param bonos: Bonos que los que se les sacara pivote y volatilidades correspondientes

    """

    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]
    volatilidades = []

    for i in range(len(vector_dias)):

        historico_factor = historico_factor_descuento(vector_dias[i], "ACT360")
        df = pd.DataFrame(historico_factor, columns=["Historico"])
        retorno = np.array(retorno_factor(df))
        volatilidad = ewma(retorno, 0.94)["Vol c/ajuste"][0]
        volatilidades.append(volatilidad)
    
    dataFrame = pd.DataFrame({"Volatilidad": volatilidades})
    return dataFrame

def seleccionar_volatilidades(volatilidades):

    """
    Funcion de seleccion de volatilidades
    Su uso se emplea para mayor comodidad

    """

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
    tir = tir_vector(add_days(fecha[0], -30))
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
        if i == 0 and fecha_probable >= fecha:
            return [pivotes.iloc[i], pivotes.iloc[i]]

        elif i == largo - 1 :

            return [pivotes.iloc[i], pivotes.iloc[i]]

        elif fecha <= fecha_probable:

            return [pivotes.iloc[i-1], pivotes.iloc[i]]

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

def valor_presente(flujo, Tir_flujo, D_flujo):

    """
    Funcion de calculo del valor presente utilizado en las proyecciones
    :param flujo: Correponde al flujo del cupon
    :param Tir_flujo: Corresponde al tir del cupon actual
    :param D_flujo: Corresponde al D del cupon actual

    """

    calculo = flujo/((1 + Tir_flujo)**D_flujo)
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

    """
    Funcion de calculo para la matriz de correlacion de 
    todos los pivotes
    :param pivotes: Pivoste que se les calculara la matriz de 
    correlacion

    """

    vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

    df = pd.DataFrame()
    for i in range(len(vector_dias)):

        historico_factor = historico_factor_descuento(vector_dias[i], "ACT360")
        df_s = pd.DataFrame(historico_factor, columns=["Historico"])
        retorno = np.array(retorno_factor(df_s))
        df[str(vector_dias[i])] = retorno

    correlacion = ewma_new_new_pivotes(len(vector_dias), df, pivotes["volatilidad"])
    covarianza = covarianza_pivotes(len(vector_dias), df, pivotes["volatilidad"])
    return [correlacion, covarianza]




def solucion_ecuacion(sigma_flujo, sigma_pivote1, sigma_pivote2, ro):

    """
    Funcion para calcular la solucion de la ecuacion propuesta
    para obtener el valor de alfa necesario para los calculos futuros
    :param sigma_flujo: Corresponde a la volatilidad del flujo
    :param sigma_pivote1: Corresponde a la volatilidad del pivote1
    :param sigma_pivote2: Correponde a la volatilidad del pivote2
    :param ro: Correspode a la correlacion del pivote1 y pivote2

    """

    A = (sigma_pivote1**2 + sigma_pivote2**2 - 2*ro*sigma_pivote1*sigma_pivote2)
    B = (2 * ro * sigma_pivote1* sigma_pivote2 - 2*sigma_pivote2**2)
    C = (sigma_pivote2**2 - sigma_flujo**2)

    x1 = (-B+math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte positiva
    x2 = (-B-math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte negativa

    return[x1, x2]

def calculo(bono):

    """
    Funcion de calculo de la distribucion para los pivotes
    de todos los bonos
    :param bono: Pandas con todos los bonos que se les calculara
    la distribucion

    """
    vector_valor = []
    piv = pivotes(bono)
    fecha_primero_pivote = add_days(piv["Fecha"][0], -30)
    correlacion = correlacion_pivotes(piv)[0]
    covarianza = correlacion_pivotes(piv)[1]
    print(covarianza)

    for i in range(len(np.array(bono["Fecha"]))):

        tabla = StrTabla2ArrTabla(bono["TablaDesarrollo"][i], str(bono["FechaEmision"][i]).split(" ")[0]) #Se crea la tabla de desarrollo del bono
        dfTabla_bono = pd.DataFrame(tabla, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
        fecha_emision = bono["FechaEmision"][i]
        resultado = calculo_por_bono(correlacion, fecha_primero_pivote, fecha_emision, piv, dfTabla_bono)
        vector_valor.append((resultado["Valor"].values))
    
    return vector_valor
   
def calculo_por_bono(correlacion, fecha_primero_pivote, fecha_emision, piv, tabla_bono):

    """
    Funcion que calcula la distribucion de valores para cada pivote
    en el calculo de un solo bono
    :param correlacion: Matriz de correlacion de los pivotes
    :param fecha_primero_pivote: Fecha correspondiente al dia 0
    :param fecha_emision: Fecha emision de el bono
    :param piv: Pivotes que se utilizaran en el calculo
    :param tabla_bono: Pandas con los datos de el bono

    """

    cupon = np.zeros(len(piv["Fecha"]))

    for j in range(len(np.array(tabla_bono["Numero"]))):

        fecha_inicial = tabla_bono["Fecha"][j]
        fecha = tabla_bono["Fecha"][j]

        pivote = entre_pivotes(fecha, piv)
        pivote1 = np.array(pivote)[0]
        pivote2 = np.array(pivote)[1]

        TIR_pivote1 = pivote1[1]
        TIR_pivote2 = pivote2[1]

        volatilidad_pivote1 = pivote1[2]
        volatilidad_pivote2 = pivote2[2]

        diferencia_dia_indices1 = (pivote1[0] - fecha_primero_pivote).days
        diferencia_dia_indices2 = (pivote2[0] - fecha_primero_pivote).days


        flujo_bono = tabla_bono["Cupon"][j]
        indice = vector_dias.index(diferencia_dia_indices1)
        D_cupon = plazo_anual_convencion("ACT360", fecha_emision, fecha)

        if pivote[0]["Fecha"] != pivote[1]["Fecha"]:

            alfa = alfa_0(fecha_inicial, pivote[0]["Fecha"], pivote[1]["Fecha"], fecha)
            TIR_fluj = TIR_flujo(alfa, TIR_pivote1, TIR_pivote2)
            volatilidad_fluj = volatilidad_flujo(alfa, volatilidad_pivote1, volatilidad_pivote2)
            
            solucion = min(solucion_ecuacion(volatilidad_fluj, volatilidad_pivote1, volatilidad_pivote2,\
                    correlacion[str(diferencia_dia_indices1)][str(diferencia_dia_indices2)]))

            valorPresente = valor_presente(flujo_bono, TIR_fluj, D_cupon)

            cupon[indice] += valorPresente * solucion
            cupon[indice + 1] += valorPresente * (1 - solucion)

        else:

            valorPresente = valor_presente(flujo_bono, TIR_pivote1, D_cupon)
            cupon[indice] += valorPresente  

    df = pd.DataFrame({"Fecha":piv["Fecha"], "Valor": cupon})
    return df
    #df.to_csv("hol.csv", mode= "a", header=False)


def vector_pivotes(pivotes_valores):

    """
    Calcula el vector B (super bono) con todos
    los pivotes calculados en la funcion calculo
    :param pivotes_valores: Corresponde a los valores de 
    los pivotes (Valor presente)

    """

    largo = len(pivotes_valores)
    valor = 0
    vector = []
    for  i in range(len(pivotes_valores[0])):

        for j in range(largo):
            
            pivote = pivotes_valores[j]
            valor += pivote[i]

        vector.append(valor)
        valor = 0

    return vector
    

def multiplicacion(covarianza, vector_grande):

    valor = np.dot(np.dot(vector_grande, covarianza), vector_grande)
    return valor


#-----------------------Calculo------------------------------

