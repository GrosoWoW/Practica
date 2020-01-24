import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
from Bonos.LibreriasUtiles.UtilesValorizacion import *
from Bonos.LibreriasUtiles.UtilesDerivados import *
from Bonos.LibreriasUtiles.Util import *
import pyodbc

server = "192.168.30.200"
driver = '{SQL Server}'  # Driver you need to connect to the database
username = 'practicantes'
password = 'PBEOh0mEpt'
cnn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

# Datos bono:
data = (
    "SELECT TOP (1000) [FechaEmision], [TablaDesarrollo] FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = 'BSTDU10618' ")
data = pd.read_sql(data, cnn)
fechasEm = data["FechaEmision"]
tablasDes = data["TablaDesarrollo"]
fecha = str(fechasEm.values[0]).split("T")[0]

# Datos curva:
curvas = ("SELECT TOP (1000) [Curva] FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_CLP' AND "
          "Fecha = '2018-06-11' AND Hora = '1700' ")
curvas = pd.read_sql(curvas, cnn)

# DATOS USADOS:
arr_curva = parsear_curva(curvas["Curva"][0], datetime.datetime.now())  # Curva
arr_tabla = StrTabla2ArrTabla(tablasDes.values[0], str(fechasEm.values[0]).split("T")[0])  # BSTDU10618

# Data frame con tabla de desarrollo del bono BSTDU10618
df = pd.DataFrame(arr_tabla, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])


def plot_curva(arr):
    """
    Plotea curva guardada en arr.
    :param arr: Arreglo de la forma arr[i] = [x_i, y_i]
    :return: Plot
    """
    x = []
    y = []
    for v in arr:
        x.append(float(v[0]) / 365.0)
        y.append(float(v[1]) / 100.0)
    plt.plot(x, y, '*')
    plt.title('Tasa por cantidad de años')
    plt.ylabel("Tasa")
    plt.xlabel("Tiempo (años)")
    plt.show()


def valorizar_bono(tabla, curva):
    """
    Entrega valor presente del bono.
    :param tabla: np array 2-dim que representa tabla de desarrollo.
    :param curva: np array 2-dim que representa curva.
    :param fecha:
    :return:
    """
    conv = "LACT360"
    parsear_curva(curvas.values[0][0], datetime.datetime.now())
    # fecha = datetime.datetime(2019, 11, 28)  # Fecha curva.
    fecha = datetime.datetime(2018, 6, 11)  # Fecha emision bono.
    # fecha = datetime.datetime.now()  # Fecha de hoy.
    dfTabla = pd.DataFrame(tabla,
                           columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
    n = len(dfTabla["Cupon"])
    vp = 0
    for i in np.arange(n):
        # print(diferencia_dias_convencion(conv, fecha, dfTabla["Fecha"][i]))
        if diferencia_dias_convencion(conv, fecha, dfTabla["Fecha"][i]) >= 0:
            tir = interpolacion_log_escalar(diferencia_dias_convencion(conv, fecha, dfTabla["Fecha"][i]), curva)
            vp += dfTabla["Cupon"][i] * factor_descuento(tir, fecha, dfTabla["Fecha"][i], conv, 0)
            # print(dfTabla["Cupon"][i] * factor_descuento(tir, fecha, dfTabla["Fecha"][i], conv, 0))
            # print(factor_descuento(tir, fecha, dfTabla["Fecha"][i], conv, 0))
    return vp


# print(valorizar_bono(arr_tabla, arr_curva))
# StrTabla2ArrTabla(strTabla, fechaEmision)

# plot_curva(arr_curva)

# print(df)

"""----------------------------VALORACION EN EL TIEMPO, SE HIZO EL 08-01----------------------------"""

# Parametros curvas.
cte_curvas = ("SELECT TOP (1200) [Fecha],[ancla],[y0],[y1],[y2],[Tipo]FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = "
              "'IF#CLP' ")
cte_curvas = pd.read_sql(cte_curvas, cnn)

# Info Bonos.
data_bonos = (
    "SELECT TOP (7) [Nemotecnico], [FechaEmision], [TablaDesarrollo], [Base1], [Base2] FROM [dbAlgebra].[dbo].["
    "TdNemoRF] WHERE Moneda = 'CLP' ")
data_bonos = pd.read_sql(data_bonos, cnn)


def plot_curvas_NS(dfCurva):
    parsear_curva(dfCurva["Curva"][0], dfCurva["Fecha"][0])


def TIR(coef, s):
    """
    TIR en s.
    :param coef: Arreglo de la forma coef = [a, y_0, y_1, y_2]
    :param s: Tiempo en dias.
    :return: r(s)
    """
    return coef[1] + (coef[0] - coef[1]) * (1 - np.exp(-s / coef[2])) * (coef[2] / s) + coef[3] * (
            (1 - np.exp(-s / coef[2])) * (coef[2] / s) - np.exp(-s / coef[2]))


def TIR_DB(df, s):
    """
    Retorna curva NS, para parametros en df, evaluada en s.
    :param df: data frame con formato [fecha, ancla, y_0, y_1, y_2].Basta que tenga los parametros pedidos.
    :param s: Tiempo en dias.
    :return: Tasa al dia s.
    """
    ancla = df["ancla"]
    y_0 = df["y0"]
    y_1 = df["y1"]
    y_2 = df["y2"]
    return y_0 + (ancla - y_0) * (1 - np.exp(-s / y_1)) * (y_1 / s) + y_2 * (
            (1 - np.exp(-s / y_1)) * (y_1 / s) - np.exp(-s / y_1))


def parsear_convenciones(df_tabla):
    """
    Retorna convencion de los bonos en un arreglo.
    :param df_tabla: dataframe con la info de los bonos.
    :return:
    """
    convenciones = []
    for i in range(df_tabla.shape[0]):
        if df_tabla.loc[0].Base1 == -1:
            s = "ACT"
        else:
            s = str(df_tabla.loc[0].Base1) + '/'
        convenciones.append(s + str(df_tabla.loc[0].Base2))
    return convenciones


infoCurva = cte_curvas.loc[cte_curvas['Fecha'] == '2018-12-20 00:00:00']


def valorizar_bono_NS(tablaDes, curvaCtes, fecha, fechaEm, conv):
    """
    Retorna precio en fecha entregada de un bono. Según curva NS.
    :param tablaDes: dataframe tabla desarrollo.
    :param curvaCtes: dataframe ctes de la curva del dia de fecha.
    :param fechaEm: datetime con fecha emision del bono.
    :param fecha: datetime con la fecha de la valorizacion.
    :param conv: Convencion del bono.
    :return: float valor presente
    """
    n = len(tablaDes["Cupon"])
    vp = 0  # Si fecha es mayor que fechaEm, coloca un 0.
    if fecha < fechaEm:
        return vp  # NO HAY PRECIO ANTES DE LA FECHA DE EMISION.
    else:
        for i in np.arange(n)[::-1]:
            if diferencia_dias_convencion(conv, fecha, tablaDes["Fecha"][i]) > 0:  # CON MAYOR ESTRICTO NO DA WARNING.
                tir = TIR_DB(curvaCtes, diferencia_dias_convencion(conv, fecha, tablaDes["Fecha"][i]))
                vp += tablaDes["Cupon"][i] * factor_descuento(tir, fecha, tablaDes["Fecha"][i], conv, 0)

        return vp


# print(data_bonos["TablaDesarrollo"].values[0])

tabla_df = pd.DataFrame(arr_tabla,
                        columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])


# print(valorizar_bono_NS(tabla_df, infoCurva, datetime.datetime.today()))

def historico_bono(dfTablaDes, fechaEm, cte_curvas, conv):
    """
    Plot/arreglo/dataframe del precio del bono en las fechas que hay curva.
    :param dfTablaDes: data frame con la tabla de desarrollo del bono.
    :param fechaEm: datetime con la fecha de emision.
    :param cte_curvas: df con la informacion de las curvas para varios dias.
    :param conv: convencion del bono.
    :return: Plot/dataframe del precio del bono vs tiempo.
    """
    n = len(cte_curvas["ancla"]) # Cantidad de curvas.
    precios = []
    Fechas = [] # Desde la más antigua a la más presente.
    for i in np.arange(n)[::-1]:
        vp = valorizar_bono_NS(dfTablaDes, cte_curvas.loc[i], cte_curvas.loc[i].Fecha, fechaEm, conv)
        precios.append(vp)
        Fechas.append(cte_curvas.loc[i].Fecha)
    # return precios_tpoInv[::-1]
    # QUITAR PARA PLOTEAR HISTORICO POR SEPARADO.
    """precios = precios_tpoInv[::-1]
    plt.ylabel('Precio')
    plt.xlabel('Tiempo (días)')
    plt.title('Precio del bono en días que hay curva.')
    plt.plot(precios, label='Precio bono')
    plt.show()"""
    # PARA RETORNAR COMO DATAFRAME.
    df = pd.DataFrame()
    df["Precio"] = precios
    df["Fecha"] = Fechas # Desde la fecha más antigua a la más reciente.
    return df


# historico_bono(df, cte_curvas, "ACT360")  # BSTDU10618

def historico_varios_bonos(dfBonos, dfCurvas):
    """
    Plot del precio de varios bonos con respecto al tiempo.
    :param dfBonos: dataframe con la info de los bonos (SQL).
    :param dfCurvas: dataframe con la info de las curvas (SQL)
    :return: Plot precio de los bonos.
    """
    fecha_ini_curva = str(cte_curvas["Fecha"][len(cte_curvas["Fecha"]) - 1]).split(" ")[0]
    n = len(dfBonos["FechaEmision"])
    convenciones = parsear_convenciones(dfBonos)
    for i in np.arange(n):
        conv = convenciones[i]
        arr_tabla = StrTabla2ArrTabla(dfBonos.loc[i].TablaDesarrollo, str(dfBonos.loc[i].FechaEmision).split(" ")[0])
        # Data frame con tabla de desarrollo del bono
        desarrollo = pd.DataFrame(arr_tabla,
                                  columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente',
                                           'Cupon'])

        precios = historico_bono(desarrollo, dfBonos["FechaEmision"][i], dfCurvas, conv)
        lab = dfBonos["Nemotecnico"][i]
        plt.plot(precios, label=lab)
        plt.legend()

    plt.ylabel('Precio')
    plt.xlabel('Tiempo (días) desde ' + fecha_ini_curva)
    plt.title('Precio del bono como función del tiempo')
    plt.show()


# historico_varios_bonos(data_bonos, cte_curvas)


"""for n in np.arange(7):
    print(pd.DataFrame(
        StrTabla2ArrTabla(data_bonos.loc[n].TablaDesarrollo, str(data_bonos.loc[n].FechaEmision).split(" ")[0]),
        columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon']))"""
