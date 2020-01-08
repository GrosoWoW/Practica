import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import datetime

#Extraccion del archivo excel
excel_file = pd.ExcelFile("Tabla.xlsx")

#Hoja1 con contenido de primera tabla
data = excel_file.parse("Hoja1")

Intereses = data["Interés"][:]/100

#Hoja2 con contenido de la segunda tabla
data2 = excel_file.parse("Hoja2")

Intereses2 = data2["Interés"][:]/100


t = data["N°"][:]

fecha = data["Fecha cupón"][:]

#Pasa las fechas del excel a version datatime, en un arreglo
def pasar_dias(dias):

    arreglo_dias = []
    for  i in range (len(dias) - 1):
        
        fecha[i] = str(fecha[i])
        fecha_cambiado = fecha[i].split("-")
        print(fecha_cambiado)
        nuevo_dia = datetime.date(int(fecha_cambiado[2]), int(fecha_cambiado[1]), int(fecha_cambiado[0])) 
        arreglo_dias.append(nuevo_dia)


    return arreglo_dias

def TIR(s):

    coef = np.zeros(4)
    coef[0] = 0.147075
    coef[1] = 0.206466
    coef[2] = 55.189922
    coef[3] = -0.055953
    vector = np.zeros(len(s))

    for i in range(len(s)):
        vector[i] = coef[1] + (coef[0] - coef[1]) * (1 - np.exp(-s[i] / coef[2])) * (coef[2] / s[i]) + coef[3] * (
            (1 - np.exp(-s[i] / coef[2])) * (coef[2] / s[i]) - np.exp(-s[i] / coef[2]))

    plt.plot(vector)
    plt.show()
    return vector



def valorizacion(data, tir):

    periodos = len(data["N°"][:])
    suma = 0


    for i in range(periodos):
        suma += data["Cupón"][i]/((1 + tir[i]/100)**(t[i]))

    
    return suma

dias = t*182.5
a = valorizacion(data, TIR(dias))
print(a)

