import numpy as np
import pandas as pd

#-----------------Calculo de retorno-------------------------

def retorno_bonos(tablaHistorico, fecha):

    """
    Calcula el retorno de los bonos para una tabla de bonos,
    recibe la tabla de bonos y la matriz de fechas

    """ 

    retornos = []

    for i in range(len(tablaHistorico)):

        if i != 0:

            diferencia_valor = np.log(tablaHistorico[i] / tablaHistorico[i-1])
            retornos.append(diferencia_valor)
        else:

            retornos.append(0)

    tabla = pd.DataFrame({"Date": fecha, "Valor": tablaHistorico, "Retorno": retornos})
    return tabla