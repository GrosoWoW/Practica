import pandas as pd
import pyodbc

"""
Funciones principales para extraer datos de una base de datos
Tanto para extraer bonos como para extraer curvas

"""

server= "192.168.30.200"
driver = '{SQL Server}'  # Driver you need to connect to the database
username = 'practicantes'
password = 'PBEOh0mEpt'
cnn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

def get_cnn():

    return cnn

def seleccionar_curva_derivados(fecha):

    """
    Selecciona una curva de la base de datos dbDerivados.dbo.TdCurvasDerivados
    Con la fecha correspondiente

    """

    curvas = ("SELECT * FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_CLP' AND Fecha = " + "'" + fecha + "'")
    curvas = pd.read_sql(curvas, cnn)
    return curvas

def seleccionar_curva_NS(tipo):

    """
    Selecciona una curva NS de la base de datos dbAlgebra.dbor.TdCurvaNS
    Donde la moneda corresponde a tipo

    """

    curvas = ("SELECT * FROM dbAlgebra.dbo.TdCurvaNS WHERE Tipo = '"+ tipo + "' ORDER BY Fecha  DESC")
    curvas = pd.read_sql(curvas, cnn)
    return curvas

def seleccionar_bono(nemotecnico):

    """
    Selecciona un bono de la base de datos dbAlgebra.dbo.TdNemoRF 
    con respecto a su nemotecnico

    """

    bono = ("SELECT TOP (10) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = " + "'"+nemotecnico+"'")
    bono = pd.read_sql(bono, cnn)
    return bono

def seleccionar_bonos_moneda(moneda, nemotecnico):

    """
    Selecciona un bono de la base de datos dbAlgebra.dbo.TdNemoRF
    con respecto a su nemotecnico y moneda

    """

    bonos = ("SELECT TOP (10) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda = " + "'" + moneda +"'" " AND Nemotecnico = " + "'"+nemotecnico+"'")
    bonos = pd.read_sql(bonos, cnn)
    return bonos
    
def curva_desarrollo(curvita):

    """
    Entrega la curva de desarrollo de 
    una cierta curva
    
    """

    tasa = []
    fecha = []
    for i in range(len(curvita)):

        tasa.append(float(curvita[i][1]))
        fecha.append(int(curvita[i][0]))

    return [fecha, tasa]


def curva_bonita(curva):

    finalX = []
    finalY = []
    for i in range(182, 10000):

        finalX.append(i)
        finalY.append(interpolacion_log_escalar(i, curva))
    
    return [finalX, finalY]

