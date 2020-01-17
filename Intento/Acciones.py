import pandas as pd
import numpy as np
from Curvas import seleccionar_todos_bonos, seleccionar_bono_fecha
from Pivotes import *
from Correlaciones import ewma


def retornos_acciones(tabla_datos):

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

    print(final)
    df = pd.DataFrame({"Volatilidad": final})
    print(df)

    return df

def unir_dataframes(data1, data2):

    return pd.concat([data1, data2], axis=0)


def calculo_para_acciones(acciones):

    largo = len(acciones)
    retornos = []
    for i in range(largo):

        calculo_retorno = retornos_acciones(acciones[i])
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

#--------------------------------Calculo-----------------------

bonos = seleccionar_todos_bonos("CLP")
bono = seleccionar_bono_fecha(str(primer_dia(bonos)))
piv = pivotes(bonos)
corr_piv = correlacion_pivotes(piv)
vol_bonos = calculo_volatilidades(bonos)


retorno = tabla_excel_yahoo_retorno("BSANTANDER.SN.xlsx")
calculo_acciones = calculo_para_acciones([retorno])
union = unir_dataframes(vol_bonos, calculo_acciones[1])

print(union)

a = calculo(bonos)
b = vector_pivotes(a)
c = correlacion_pivotes(piv)[1]
a = correlacion_pivotes_Acciones(b, calculo_acciones[0][0], union)
print(multiplicacion(c, b))
print(a[1])
print(multiplicacion_acciones(a[1], union["Volatilidad"]))

