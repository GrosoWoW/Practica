import pandas as pd
import pyodbc
import numpy as np

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)


def seleccionar_accion(nemotecnico, fondo):

    accion = "SELECT * FROM [dbPortFolio].[dbo].[TdPlanvitalCartera] WHERE Fondo = '" + fondo + "' AND TipoLva = 'EXT' AND Nemotecnico = '"+ str(nemotecnico) +"' ORDER BY Fecha DESC"
    accion = pd.read_sql(accion, cn)

    return accion

def historico(nemotecnico, fondo,n = 60):

    accion_actual = seleccionar_accion(nemotecnico, fondo)

    a = accion_actual.groupby(["Fecha", "Fondo", "Nemotecnico"], as_index=False).sum()

    valorizacion = a["ValorizacionCLP"]
    nominales = a["Nominales"]
    largo = len(nominales)

    print(a)

    largo_final = max(n, largo)
    print(largo_final)
    arreglo_valores = []
    arreglo_valores.append(0)


    for i in range(1, largo_final):

        calculo = np.log(abs(valorizacion[i]*nominales[i - 1]/(valorizacion[i - 1]*nominales[i])))
        arreglo_valores.append(calculo)

    df1 = pd.DataFrame()
    df1["Moneda"] = ["CLP"]
    df1["Nombre"] = [nemotecnico]
    df1["Inversion"] = [accion_actual["ValorizacionCLP"][0]]
    df1["Historico"] = [[arreglo_valores]]
    print(df1)

    return df1

