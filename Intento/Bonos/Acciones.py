import numpy as np
import pandas as pd

from Correlaciones import ewma
from Curvas import seleccionar_bono_fecha, seleccionar_todos_bonos
from Pivotes import *


def retornos_acciones(nombreAccion):

    print(nombreAccion)
    archivo = pd.read_excel('C:\\Users\\groso\\Desktop\\Practica\\Intento\\ArchivosExcel\\'+ nombreAccion)
    columnas = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    tabla_datos = archivo[columnas]
    arreglo = []
    arreglo.append(0)
    tabla_adj = tabla_datos["Adj Close"]
    fechas = tabla_datos["Date"]
    largo = len(tabla_adj)


    for i in range(1, largo):

        valor = np.log(tabla_adj[i] / tabla_adj[i-1])
        arreglo.append(valor)

    df = pd.DataFrame({"Date": fechas, "Adj Close": tabla_adj, "Retornos": arreglo})
    return df


def volatilidades_acciones(retornos_acciones):

    final = []
    for i in range(len(retornos_acciones)):

        calculo = ewma(retornos_acciones[i]["Retornos"], 0.94)
        final.append(calculo["Vol c/ajuste"][0])

    df = pd.DataFrame({"Volatilidad": final})

    return df

def unir_dataframes(data1, data2):

    return pd.concat([data1, data2], axis=0)


def calculo_para_acciones(acciones):

    retornos = []
    calculo_retorno = retornos_acciones(acciones)
    retornos.append(calculo_retorno)
    volatilidad = volatilidades_acciones(retornos)

    return [retornos, volatilidad]


def tabla_excel_yahoo_retorno(nombreArchivo):

    """
    Extrae un archivo excel a un dataframe, calculando su valor de retorno
    con la funcion retorno_bonos
    
    """

    archivo = pd.read_excel('C:\\Users\\groso\\Desktop\\Practica\\Intento\\ArchivosExcel\\'+ nombreArchivo)
    columnas = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    archivo = archivo[columnas]
    nombre = nombreArchivo.split(".")[0]

    return archivo

def correlacion_pivotes_Acciones(pivotes, acciones, volatilidad):

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

    nuevo_df = pd.concat([df[:len(acciones["Retornos"])], acciones["Retornos"]], axis=1)
    correlacion = ewma_new_new_pivotes(len(volatilidad["Volatilidad"]), nuevo_df, volatilidad["Volatilidad"])
    covarianza = covarianza_pivotes(len(volatilidad["Volatilidad"]), nuevo_df, volatilidad["Volatilidad"])
    return [correlacion, covarianza]

def multiplicacion_acciones(covarianza, vector_grande):

    valor = np.dot(np.dot(vector_grande, covarianza), vector_grande)
    return valor

def varias_acciones(lista_acciones):

    largo = len(lista_acciones)
    df = pd.DataFrame()
    for i in range(largo):

        retorno = tabla_excel_yahoo_retorno(lista_acciones[i])
        calculo_acciones = calculo_para_acciones(lista_acciones[i])
        df = pd.concat([df, calculo_acciones[1]], axis=1)

    return df

        
def retorno_varias_acciones(lista_acciones):

    large = len(lista_acciones)
    df = pd.DataFrame()

    for i in range(large):

        retorno = retornos_acciones(lista_acciones[i])
        df["Retornos"] = retorno["Retornos"]
    
    return df




#--------------------------------Calculo-----------------------

bonos = seleccionar_todos_bonos("CLP")
bono = seleccionar_bono_fecha(str(primer_dia(bonos)))
piv = pivotes(bonos)
corr_piv = correlacion_pivotes(piv)
vol_bonos = calculo_volatilidades(bonos)


acciones = ["BSANTANDER.SN.xlsx"]
volatilidad_accion = varias_acciones(acciones)
volatilidad_total = unir_dataframes(vol_bonos, volatilidad_accion)

retorno_acciones = retorno_varias_acciones(acciones)
print(retorno_acciones)


a = calculo(bonos)
b = vector_pivotes(a)
c = correlacion_pivotes(piv)[1]
a = correlacion_pivotes_Acciones(b, retorno_acciones, volatilidad_total)
print(a)

