import datetime
from math import exp, log
from time import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

import pyodbc
from Correlaciones import ewma_new_new
from Curvas import (get_cnn, seleccionar_bono, seleccionar_bonos_moneda,
                    seleccionar_curva_derivados, seleccionar_curva_NS)
from FuncionesExcel import (graficar_retornos, tabla_bono_retorno,
                            tabla_excel_yahoo_retorno, unir_dataframes)
from Matematica import interpolacion_log_escalar
from UtilesValorizacion import (StrTabla2ArrTabla, diferencia_dias_convencion,
                                factor_descuento, parsear_curva)
from ValorizacionBonos import auto_bono, plot_bonos, valor_bono_derivados

#-------------------------Calculos-Historico-------------------------
tiempo_inicial = time()
arreglo_bonos = ["BSTDU10618", "BSTDU21118", "BSTDU30618", "BSTDU40117", "BSTDU70518" , "BENTE-L"]
plot_bonos(arreglo_bonos)

def tiempos(bonos):

    """
    Calcula el tiempo que demora una matriz de bonos en calcular
    el retorno del bono, recibe bonos que corresponde a una matriz
    con todos los bonos que se desea medir el tiempo de ejecucion

    """
    tiempos = []
    tiempo_i = time()
    for i in range(len(bonos)):
        print(bonos[i])
        auto_bono(bonos[i])
        tiempo = time() - tiempo_i
        tiempos.append(tiempo)
    plt.plot(tiempos, "*")
    plt.show()

bonobon = ["BSTDU10618", "BSTDU21118", "BSTDU30618", "BSTDU40117", "BSTDU70518" , "BENTE-L", "BCORCB0914"\
    ,"BCORCC0914","BCORCD0914","BCORCE0914","BCORCF0914","BCORCG0914","BCORCH0914","BCORCI0914","BCORCJ0914","BCORCK0914", \
        "BCORCL0914","BCORCM0914","BCORCN0914","BCORCO0914","BCCA-C0912","BCCA-D1113","BCCA-E0115","BCCAR-A",\
        "BCCAR-B","BSECX10118","BPLZA-L","BBBVP20714","BFALA-Q","BCOPV-B","BEMCA-Q","BQUIN-T","BRPLC-E","BFORU-BA","BECOP-H",\
        "BESVA-R","BBCI-E1117","BESTW10417","BESTW20717","BESTW30218","BESTW40218","BESTW61117"]

#tiempos(bonobon)

bono_6 = auto_bono("BENTE-L")
print(bono_6)

#Bono que se utilizara para el calculo
bono_derivados =("SELECT TOP (10) [FechaEmision], [TablaDesarrollo] FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = 'BSTDU10618'")
bono_derivados = pd.read_sql(bono_derivados, get_cnn())

curva_derivados = seleccionar_curva_derivados(str(bono_derivados["FechaEmision"][0]))
curva_derivados = parsear_curva(curva_derivados["Curva"][0], datetime.datetime.today)

#Calculo del valor de un bono con curva derivados
valor_bono_derivados(bono_derivados, curva_derivados)

#------------------Calculos-Retorno---------------------

#Bonos
tiempo_inicial = time()
BonoEntel = tabla_bono_retorno(bono_6, "BonoEntel", False, 20)

#Acciones
Entel = tabla_excel_yahoo_retorno("ENTEL.SN.csv")
Facebook = tabla_excel_yahoo_retorno("FB.csv")  
Santander = tabla_excel_yahoo_retorno("BSANTANDER.SN.csv")
Iansa = tabla_excel_yahoo_retorno("IANSA.SN.csv")

#Correlaciones
matriz_correlacion = unir_dataframes([Entel, Facebook, Santander, Iansa, BonoEntel])
matriz_correlacion = ewma_new_new(5, matriz_correlacion)
print(matriz_correlacion)

#Tiempo
tiempo_final = time()-tiempo_inicial
print("Correlacion: {:.5f}".format(tiempo_final))
graficar_retornos([Entel, Facebook, Santander],["ENTEL", "FB", "BSANTANDER", "IANSA", "BonoEntel"])
