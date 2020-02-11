import pandas as pd
import pyodbc
import numpy as np

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)


def seleccionar_accion(nemotecnico):

    accion = "SELECT * FROM [dbPortFolio].[dbo].[TdPlanvitalCartera] WHERE TipoLva = 'EXT' AND Nemotecnico = '"+ str(nemotecnico) +"'"
    accion = pd.read_sql(accion, cn)

    return accion

def historico(nemotecnico):

    accion_actual = seleccionar_accion(nemotecnico)

    nominales = accion_actual["Nominales"]
    monto = accion_actual["ValorizacionCLP"]
    largo = len(nominales)
    arreglo_valores = []

    for i in range(largo):

        calculo = monto[i]/nominales[i]
        arreglo_valores.append(calculo)

    df = pd.DataFrame(arreglo_valores, columns=["Historico"])
    return df



