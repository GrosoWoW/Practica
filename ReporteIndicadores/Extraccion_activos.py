import datetime

import numpy as np
import pandas as pd

import pyodbc
from DerivadosTipos.DerivadosFWD import *
from DerivadosTipos.DerivadosSCC import *

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

# ---------------------------------------------Extraccion de bonos------------------------------------------------
def cambiar_fecha(fecha):

    fechas = fecha.split("-")
    fechas = fechas[2].split(" ")[0] + "/" + fechas[1] + "/" + fechas[0]
    return fechas

def conversionSYP(riesgo):
    return {-1: "AAA", 1: 'AAA',2: 'AA',3: 'AA',4: 'AA',5: 'A',6: 'A',7: 'A',8: 'BBB',9: 'BBB',10: 'BBB',\
            11: 'BB',12: 'BB',13: 'BB',14: 'B',15: 'B',16: 'B',17: 'CCC',18: 'CC',19: 'CC',20: 'C',\
            21: 'C',22: 'C',23: 'D',24: 'E'}.get(riesgo)

def ajustes(bonos):
    bonos['FechaEmision'] = bonos['FechaEmision'].apply(lambda x: x.strftime('%Y-%m-%d'))
    bonos['Base1'] = bonos['Base1'].apply(lambda x: x if x != -1 else 'ACT')
    bonos['Base2'] = bonos['Base2'].apply(lambda x: x if x != -1 else 'ACT')
    bonos['Convencion'] = bonos['Base1'].apply(lambda x: str(x)) + '/' + bonos['Base2'].apply(lambda x: str(x))
    bonos['Riesgo'] = bonos['RiesgoInt'].apply(lambda x: conversionSYP(x))
    return bonos


def extraer_bonos(n,cn):

    pandas = pd.DataFrame()

    bonos = "SELECT Moneda, Base1  , Base2, TablaDesarrollo , FechaEmision, NemotecnicoBono AS Nemotecnico, RiesgoInt \
    FROM (SELECT * FROM (SELECT Moneda, Base1  , Base2, TablaDesarrollo , FechaEmision, Nemotecnico AS NemotecnicoBono \
    FROM [dbAlgebra].[dbo].[TdNemoRF]) AS bono JOIN (SELECT * FROM [dbPortFolio].[dbo].[TdPlanvitalCartera]) AS planvital \
    ON bono.FechaEmision > '20190101' AND bono.NemotecnicoBono = planvital.Nemotecnico) AS A \
    JOIN (SELECT DISTINCT Nemotecnico, RiesgoLVA AS RiesgoInt FROM [dbAlgebra].[dbo].[TdRiesgoLva]) AS B ON A.NemotecnicoBono = B.Nemotecnico"

    bonos = pd.read_sql(bonos, cn)

    moneda = []
    base1 = []
    base2 = []
    tabla = []
    fecha_emision = []
    nemotecnico = []
    riesgo = []

    for i in range(np.size(bonos, 0)):

        if bonos["Nemotecnico"][i] in nemotecnico: continue
        if bonos["RiesgoInt"][i] in riesgo : continue

        moneda.append(bonos["Moneda"][i])
        base1.append(bonos["Base1"][i])
        base2.append(bonos["Base2"][i])
        tabla.append(bonos["TablaDesarrollo"][i])
        fecha_emision.append(bonos["FechaEmision"][i])
        nemotecnico.append(bonos["Nemotecnico"][i])
        riesgo.append(bonos["RiesgoInt"][i])

    pandas["Moneda"] = moneda
    pandas["Base1"] = base1
    pandas["Base2"] = base2
    pandas["TablaDesarrollo"] = tabla
    pandas["FechaEmision"] = fecha_emision
    pandas["Nemotecnico"] = nemotecnico
    pandas["RiesgoInt"] = riesgo

    bonos_final = ajustes(pandas).head(n)


    return bonos_final

#-------------------------------------- Extraccion de derivados ------------------------------------------------------

def extraer_derivados(cantidad, cn):

    derivados = "SELECT TOP ("+ str(cantidad) +") * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] WHERE Tipo = 'FWD' OR Tipo = 'SCC'"
    derivados = pd.read_sql(derivados, cn)
    derivado = pd.DataFrame()
    dev = []

    for i in range(cantidad):

        info_derivado = dict()
        info_derivado["Tipo"] = derivados["Tipo"][i]
        info_derivado["ID_Key"] = derivados["ID_Key"][i]
        info_derivado["Administradora"] = derivados["Administradora"][i]
        info_derivado["Fondo"] = derivados["Fondo"][i]
        info_derivado["Contraparte"] = derivados["Contraparte"][i]
        info_derivado["ID"] = int(derivados["ID"][i])
        info_derivado["Nemotecnico"] = derivados["Nemotecnico"][i]
        info_derivado["Mercado"] = derivados["Mercado"][i]     
        fecha = datetime.date(2019, 10, 14)
        hora = '1700'
        info_derivado["FechaEfectiva"] = cambiar_fecha(str(derivados["FechaEfectiva"][i]))
        info_derivado["FechaVenc"] = cambiar_fecha(str(derivados["FechaVenc"][i]))
        info_derivado["AjusteFeriados"] = derivados["AjusteFeriados"][i]
        info_derivado["NocionalActivo"] = derivados["NocionalActivo"][i]
        info_derivado["NocionalPasivo"] = derivados["NocionalActivo"][i]

        info_derivado["MonedaActivo"] = derivados["MonedaActivo"][i]
        info_derivado["MonedaPasivo"] = derivados["MonedaPasivo"][i]

        info_derivado["MonedaBase"] = derivados["MonedaBase"][i]
        info_derivado["TipoTasaActivo"] = derivados["TipoTasaActivo"][i]
        info_derivado["TipoTasaPasivo"] = derivados["TipoTasaPasivo"][i]
        info_derivado["TasaActivo"] = derivados["TasaActivo"][i]
        info_derivado["TasaPasivo"] = derivados["TasaPasivo"][i]
        info_derivado["FrecuenciaActivo"] = derivados["FrecuenciaActivo"][i]
        info_derivado["FrecuenciaPasivo"] = info_derivado["FrecuenciaActivo"]

        info1 = pd.DataFrame([info_derivado])
        tipo_derivado = derivados["Tipo"][i]
        
        if tipo_derivado == 'SCC':

            derivado_info = DerivadosSCC(fecha, hora, info1, cn)
        
        elif tipo_derivado == 'FWD':

            derivado_info = DerivadosFWD(fecha, hora, info1, cn)

        dev.append(derivado_info)

    derivado["Derivado"] = dev
    derivado["Nemotecnico"] = 'BCINO UF 200709_A'
    return derivado


# --------------------------------------------- Extraccion de accion -------------------------------------------------------

def seleccionar_accion(nemotecnico, fondo):

    accion = "SELECT * FROM [dbPortFolio].[dbo].[TdPlanvitalCartera] WHERE Fondo = '" + fondo + "' AND Nemotecnico = '"+ str(nemotecnico) +"' ORDER BY Fecha DESC"
    accion = pd.read_sql(accion, cn)

    return accion

def historico_IPSA(n, fecha):

    ipsa = "SELECT TOP (" + n + ") [IPSA] FROM [dbAlgebra].[dbo].[TdIndicadores] WHERE Fecha <= '" + fecha + "'"
    ipsa = pd.read_sql(ipsa, cn)[::-1]

    return ipsa

def extraer_acciones(arreglo_nemotecnicos, arreglo_fondo, n = 60):

    """
    Calcula el historico para un arreglo de nemotecnicos
    :param arreglo_nemotecnicos: Lista con los nemotecnicos de las acciones en string
    :param arreglo_fondo: Lista con los fondos de las acciones anterior mencionadas
    :return: DataFrame con las monedas, nemotecnicos, inversiones y historicos de las 
    acciones

    """

    cantidad_acciones = len(arreglo_nemotecnicos)

    monedas = []
    nombres = []
    nemotecnicos = []
    inversiones = []
    historicos = []

    for i in range(cantidad_acciones):

        nemotecnico = arreglo_nemotecnicos[i]
        fondo = arreglo_fondo[i]

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

        monedas.append("CLP")
        nombres.append(nemotecnico)
        nemotecnicos.append(nemotecnico)
        inversiones.append(accion_actual["ValorizacionCLP"][0])
        historicos.append([arreglo_valores])


    df1 = pd.DataFrame()
    df1["Moneda"] = monedas
    df1["Nombre"] = nombres
    df1["Nemotecnico"] = nemotecnicos
    df1["Inversion"] = inversiones
    df1["Historico"] = historicos


    return df1

