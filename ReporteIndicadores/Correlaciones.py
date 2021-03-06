
import math
import numpy as np
import pandas as pd

#------------------Correlacion--------------------------

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
                (formula(0.94, matriz_r, tamanoRetorno, j, k))/(volatilidades.values[k][0]*volatilidades.values[j][0])
    
    df = pd.DataFrame(ro, columns=nombre, index=nombre)
    return df

# retornos: vector de retornos a los que se les busca calcular volatilidad, ordenados del más reciente al más antiguo
# l: valor de lambda entre 0 y 1
def ewma(retornos, l):
    """
    Retorna DataFrame con la volatilidad del vector de retornos.
    :param: retornos: DataFrame de una columna con histórico de retornos. Orden: pasado-->futuro 
    :param: l: lambda.
    :return: 
    """
    # Cantidad retornos.
    n=len(retornos)
    # Pesos para el ewma.
    factor = l**np.array(range(n))
    volSinAjuste = sum((1-l)*retornos*retornos*factor[::-1])
    volConAjuste = volSinAjuste/(1-l**(n-1))
    volSinAjuste = np.sqrt(volSinAjuste)
    volConAjuste = np.sqrt(volConAjuste)
    
    data = [[volConAjuste, volSinAjuste, 1/(1-l**(n-1)), n ]]
    df = pd.DataFrame(data, columns = ['Vol c/ajuste', "Vol s/ajuste","Ajuste", " cantidad de retornos"])
    return df

#-----------------------Covarianza---------------------------------------------

def covarianza_pivotes(m_empresas, matriz_r, volatilidades):

    """
    Calculo de la matriz de covarianza de la matriz_r
    Recibe m_empresas que corresponde a la cantidad de empresas
    y la matriz_r con la cantidad de datos

    """
    nombre = matriz_r.columns.tolist()
    matriz_r = matriz_r.values
        
    ro = np.zeros([m_empresas, m_empresas])
    for k in range(0,m_empresas):
        for j in range(0,m_empresas):

            if k == j:
                ro[k][j] = (volatilidades.values[k])**2
            else:
                tamanoRetorno = len(matriz_r[:,k])
 
                ro[k][j] = (factor(0.94, tamanoRetorno) * \
                    formula(0.94, matriz_r, tamanoRetorno, j, k))
    
    df = pd.DataFrame(ro, columns=nombre, index=nombre)
    return df