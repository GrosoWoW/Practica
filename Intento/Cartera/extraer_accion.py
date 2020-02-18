import pandas as pd
import pyodbc
import numpy as np

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)


def seleccionar_accion(nemotecnico, fondo):

    accion = "SELECT * FROM [dbPortFolio].[dbo].[TdPlanvitalCartera] WHERE Fondo = '" + fondo + "' AND Nemotecnico = '"+ str(nemotecnico) +"' ORDER BY Fecha DESC"
    accion = pd.read_sql(accion, cn)

    return accion

def historico_IPSA(n, fecha):
    ipsa = "SELECT TOP (" + n + ") [IPSA] FROM [dbAlgebra].[dbo].[TdIndicadores] WHERE Fecha <= '" + fecha + "'"
    ipsa = pd.read_sql(ipsa, cn)[::-1]

    return ipsa

def historico(nemotecnico, fondo,n = 60):

    accion_actual = seleccionar_accion(nemotecnico, fondo)

    accion_modificada = accion_actual.groupby(["Fecha", "Fondo", "Nemotecnico"], as_index=False).sum()

    valorizacion = accion_modificada["ValorizacionCLP"]
    nominales = accion_modificada["Nominales"]
    largo = len(nominales)

    
    arreglo_valores = []
    arreglo_valores.append(0)

    if (largo >= n):

        for i in range(1, n):

            calculo = np.log(abs(valorizacion[i]*nominales[i - 1]/(valorizacion[i - 1]*nominales[i])))
            arreglo_valores.append(calculo)
    
    else:

        arreglo_valores = historico_IPSA(str(n), '20200214')['IPSA'].apply(lambda x: 0 if x == -1000 else x)
        arreglo_valores = arreglo_valores.values.tolist()

    df1 = pd.DataFrame()
    df1["Moneda"] = ["CLP"]
    df1["Nombre"] = [nemotecnico]
    df1["Nemotecnico"] = [nemotecnico]
    df1["Inversion"] = [accion_actual["ValorizacionCLP"][0]]
    df1["Historico"] = [[arreglo_valores]]

    return df1

