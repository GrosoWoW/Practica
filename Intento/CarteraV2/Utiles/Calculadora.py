import pandas as pd
import numpy as np

vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30] #Vector para crear los pivotes

#------------------------Retornos------------------------------

"""
Funciones principales para el calculo de retornos de la moneda

"""

def calcular_retornos(dfHistorico):

    """
    Funcion encargada de calcular los retornos dado un historico para cada pivote
    :param dfHistorico: Pandas con los historicos a los que se les calculara el retorno
    :return DataFrame con todos los retornos ordenados

    """
    numero_filas = len(vector_dias)
    nombre_columnas = dfHistorico.columns

    numero_columnas = len(dfHistorico[nom_columnas[0]])
    valores = []
    df = pd.DataFrame()

    for i in range(numero_filas):

        columna = dfHistorico[nombre_columnas[i]]
        valores.append(0)
        for j in range(1, numero_columnas):

            valor = np.log(columna[j] / columna[j-1])
            valores.append(valor)

        df[nombre_columnas[i]] = np.array(valores)
        valores = []

    return df

#----------------------------Volatilidades---------------------------------

"""
Funciones encargadas de calcular las volatilidades de una
cartera

"""

def calculo_volatilidades(dfRetornos):

    """
    Funcion encargada de calcular las volatilidades de ciertos retornos
    Estas volatilidades estan calculadas con la funcion ewma, lambda 0.94
    :param dfRetornos: DataFrame con los retornos a los que se les calcularan las volatilidades
    :return DataFrame con las volatilidades

    """
    nom_columnas = dfRetornos.columns
    numero_filas = len(vector_dias)
    df = pd.DataFrame()
    valores = []

    for i in range(numero_filas):

        retornos = dfRetornos[nom_columnas[i]]
        valor = ewma(retornos, 0.94)
        valores.append(valor["Vol c/ajuste"].values[0])
    
    df["Volatilidades"] = valores
    return df


#---------------------------------Correlacion--------------------------------------

"""
Funciones principales para calcular la correlacion
de una matriz de datos

"""

def factor(lam, n):

    """
    Factor de multiplicacion de la formula principal
    Recibe lam que corresponde a lambda (factor 0.94)
    y n que corresponde al tamaño de cantidad de retornos

    """
    return (1-lam)

def formula(lam, r, N, j, k):
   
    """
    Calculo de la sumatoria correspondiente a la formula
    recibe lam que corresponda a 0.94
    r que corresponde a la matriz de datos 
    N es el tamaño de la cantidad de retornos
    j y k correspondientes a valores dados por ewma

    """
    valor = 0
    for i in range(0,N):
        valor += (lam**i)*r[N-i-1][j]*r[N-i-1][k]

    return valor / (1 - lam**(N-1))

def ewma_matriz(m_empresas, matriz_r, volatilidades):

    """
    Calculo de ewma para la matriz_r
    Recibe m_empresas que corresponde a la cantidad de empresas
    y la matriz_r con la cantidad de datos

    """
    nombre = matriz_r.columns.tolist()
    matriz_r = matriz_r.values
        
    ro = np.zeros([m_empresas, m_empresas])
    for k in range(0,m_empresas):
        for j in range(0,m_empresas):

            tamanoRetorno = len(matriz_r[:,k])
            ro[k][j] = factor(0.94, tamanoRetorno) * \
                (formula(0.94, matriz_r, tamanoRetorno, j, k))/(volatilidades.values[k][1]*volatilidades.values[j][1])
    
    df = pd.DataFrame(ro, columns=nombre, index=nombre)
    return df