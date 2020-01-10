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
    return (1-lam)/(1-lam**(n-1))

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
        valor += (lam**i)*r[j][N-i-1]*r[k][N-i-1]

    return valor

def ewma_new_new(m_empresas, matriz_r):

    """
    Calculo de ewma para la matriz_r
    Recibe m_empresas que corresponde a la cantidad de empresas
    y la matriz_r con la cantidad de datos

    """

    matriz_r = matriz_r.drop(columns=("Date"))
    nombre = matriz_r.columns.tolist()
    matriz_r = matriz_r.values
        
    ro = np.zeros([m_empresas, m_empresas])
    for k in range(0,m_empresas):
        for j in range(0,m_empresas):

            tamanoRetorno = len(matriz_r[:][k])
            ro[k][j] = factor(0.94, tamanoRetorno) * formula(0.94, matriz_r, tamanoRetorno, j, k)
    
    df = pd.DataFrame(ro, columns=nombre, index=nombre)
    return df