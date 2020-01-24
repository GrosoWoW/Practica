import numpy as np
import pandas as pd
from Bonos.LibreriasUtiles.Util import add_days

#-----------------Calculo de retorno-------------------------

"""
Aqui se presentan las funciones para calcular los retornos de ciertos
tipos de datos (Retornos de valores de bonos, factores de descuento, etc)

"""

def retorno_bonos(tablaHistorico, fecha):

    """
    Calcula el retorno de los bonos para una tabla de bonos,
    recibe la tabla de bonos y la matriz de fechas

    """ 
    retornos = []
    fechas = []
    valor = []
    largo = len(tablaHistorico)

    for i in range(largo-1):

        if i != 0 and tablaHistorico[i] != 0:

            diferencia_valor = np.log(tablaHistorico[i+1] / tablaHistorico[i])
            retornos.append(diferencia_valor)
            fechas.append(fecha[i])
            valor.append(tablaHistorico[i])

        """
        elif i == 0:

            retornos.append(0)
            fechas.append(fecha[i])
            valor.append(tablaHistorico[i])

        else:
            retornos.append(0)
            fechas.append(fecha[i])
            valor.append(tablaHistorico[i])
        """

    tabla = pd.DataFrame({"Date": fechas, "Valor": valor, "Retorno": retornos})
    return tabla

def retorno_factor(factorDescuento):

    """
    Calcula los retornos para una tabla de historicos
    de factores de descuento
    :param factorDescuento: Pandas de historicos de factor de descuento

    """

    historico = factorDescuento["Historico"]
    retornos = []

    for i in range(len(historico)):

        if(i==0):
            retornos.append(0)

        else:
            diferencia_valor = np.log(historico[i] / historico[i-1])
            retornos.append(diferencia_valor)

    return(retornos)




