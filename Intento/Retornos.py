import numpy as np
import pandas as pd
from Util import add_days

#-----------------Calculo de retorno-------------------------

def retorno_bonos(tablaHistorico, fecha, pivotes, num):

    """
    Calcula el retorno de los bonos para una tabla de bonos,
    recibe la tabla de bonos y la matriz de fechas

    """ 
    retornos = []
    fechas = []
    valor = []
    if(pivotes):
        largo = len(tablaHistorico)
    else:
        largo =num 

    fechauwu = fecha[0]
    for i in range(largo):
        #print(i)

        if i >= len(tablaHistorico):

            fechauwu = add_days(fechauwu, 1)
            retornos.append(0)
            fechas.append(fechauwu)
            valor.append(0)

        elif i != 0 and tablaHistorico[i] != 0:

            fechauwu = fecha[i]
            diferencia_valor = np.log(tablaHistorico[i] / tablaHistorico[i-1])
            retornos.append(diferencia_valor)
            fechas.append(fecha[i])
            valor.append(tablaHistorico[i])

        elif i == 0:

            fechauwu = fecha[i]
            retornos.append(0)
            fechas.append(fecha[i])
            valor.append(tablaHistorico[i])

        else:

            fechauwu = fecha[i]
            retornos.append(0)
            fechas.append(fecha[i])
            valor.append(tablaHistorico[i])

    tabla = pd.DataFrame({"Date": fechas, "Valor": valor, "Retorno": retornos})
    return tabla

def retorno_factor(factorDescuento):

    historico = factorDescuento["Historico"]
    retornos = []

    for i in range(len(historico)):

        if(i==0):
            retornos.append(0)

        else:
            diferencia_valor = np.log(historico[i] / historico[i-1])
            retornos.append(diferencia_valor)

    return(retornos)




