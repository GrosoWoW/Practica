# 14-01
# from corr_proyeccion_1001 import *
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
from Bonos.LibreriasUtiles.UtilesValorizacion import *
from Bonos.LibreriasUtiles.UtilesDerivados import *
from Bonos.LibreriasUtiles.Util import *
from Derivados.valorizacionBD_0708_01 import valorizar_bono_NS, TIR_DB, parsear_convenciones
import pyodbc


pd.set_option('display.max_columns', None)
server = "192.168.30.200"
driver = '{SQL Server}'  # Driver you need to connect to the database
username = 'practicantes'
password = 'PBEOh0mEpt'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

# Plazos:
plazosPiv = [30, 90, 180, 360, 360 * 2, 360 * 3, 360 * 4, 360 * 5, 360 * 7, 360 * 9, 360 * 10, 360 * 15, 360 * 20,
             360 * 30]


def seleccionar_bonos(moneda, emisor, n):
    bonos = ("SELECT TOP (" + str(
        n) + ") * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda = '" + moneda + "' AND Emisor = "
                                                                                 "'" + emisor +
             "' ORDER BY FechaEmision DESC")
    bonos = pd.read_sql(bonos, cn)
    return bonos


def seleccionar_curvas(n):  # USAR PARA TENER LA MISMA CANTIDAD DE DATOS AL HACER CORRELACIONES.
    """
    Selecciona n curvas de la DB.
    :param n: Cantidad de curvas hacia el pasado.
    :return: DataFrame con la info de las curvas.
    """
    s = str(n)
    df_curvas = ("SELECT TOP (" + s + ") [Fecha],[ancla],[y0],[y1],[y2],[Tipo] FROM [dbAlgebra].[dbo].[TdCurvaNS] "
                                      "WHERE TIPO = 'IF#CLP' ")
    df_curvas = pd.read_sql(df_curvas, cn)
    return df_curvas


def cuadratica(a, b, c):
    """
    Resuelve cuadrática 0 = ax^2+ bx + c.
    :param a: Float.
    :param b: Float.
    :param c: Float.
    :return: Ambas soluciones en un vector.
    """
    assert b ** 2 - 4 * a * c >= 0, "Determinante negativo."
    sol1 = (-b + np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
    sol2 = (-b - np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
    return [sol1, sol2]


def tablas_desarrollo(df_bonos):
    """
    Calcula df con la tabla de desarrollo.
    :param df_bonos: df de los bonos.
    :return: Arreglo con las tablas de des como df.
    """
    aux = []
    for i in np.arange(len(df_bonos["Nemotecnico"])):
        aux.append(pd.DataFrame(
            StrTabla2ArrTabla(df_bonos.loc[i].TablaDesarrollo, str(df_bonos.loc[i].FechaEmision).split(" ")[0]),
            columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon']))
    return aux


def precios_bono(df_bono, cte_curvas, conv):
    """
    Calcula precios para los dias de las curvas. De pasado a futuro.
    :param conv: convencion del bono.
    :param cte_curvas: df con la informacion de las curvas para varios dias.
    :param conv: convencion del bono.
    :return: dataframe del precio del bono.
    """
    fechaEm = df_bono["FechaEmision"]
    dfTablaDes = pd.DataFrame(
        StrTabla2ArrTabla(df_bono["TablaDesarrollo"], str(fechaEm).split(" ")[0]),
        columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
    n = len(cte_curvas["ancla"])  # Cantidad de curvas.
    precios = []
    Fechas = []  # Desde la más antigua a la más presente.
    for i in np.arange(n)[::-1]:
        vp = valorizar_bono_NS(dfTablaDes, cte_curvas.loc[i], cte_curvas.loc[i].Fecha, fechaEm, conv)
        precios.append(vp)
        Fechas.append(cte_curvas.loc[i].Fecha)
    # PARA RETORNAR COMO DATAFRAME.
    df = pd.DataFrame()
    df["Fecha"] = Fechas  # Desde la fecha más antigua a la más reciente.
    df["Precio"] = precios
    return df


def retorno(df_precios):
    """
    Calcula los retorno de un vector de precios. Pondrá 0 donde no pueda calcular retorno.
    :param df_precios: df con columnas (de fecha y) valor (precio) . De pasado a futuro.
    :return: DataFrame con los retornos en cada fecha desde pasado a futuro.
    """
    aux = pd.DataFrame()
    str = df_precios.columns[1]
    fecha = [df_precios["Fecha"][0]]
    retorno = [0]
    for i in np.arange(1, len(df_precios["Fecha"])):
        if df_precios[str][i] != 0 and df_precios[str][i - 1] != 0:
            fecha.append(df_precios["Fecha"][i])
            retorno.append(np.log(df_precios[str][i] / df_precios[str][i - 1]))
        else:
            fecha.append(df_precios["Fecha"][i])
            retorno.append(0)
    # aux["Fecha"] = fecha     NO PONE COLUMNA DE FECHA
    aux[str] = retorno
    return aux


def mas_cercanas(arr, fecha):
    """
    Calcula pivotes de fecha. Asume que fecha está dentro del rango de arr.
    :param arr: Arreglo con fechas datetime en orden creciente.
    :param fecha: Fecha datetime.
    :return: Indice de los pivotes de fecha en arr.
    """
    aux = []
    for i in range(len(arr)):
        if arr[i] > fecha:
            aux.append(i - 1)
            aux.append(i)
            break
    return aux


def fecha_pivotes(fecha_ini, arr):
    """
    Calcula la feha de los pivotes contados desde fecha_ini.
    :param fecha_ini: datetime con fecha inicial.
    :param arr: Arreglo con los pivotes en días.
    :return: arreglo con los pivotes desde fecha_ini en formato datetime.
    """
    aux = []
    for i in range(len(arr)):
        aux.append(fecha_ini + datetime.timedelta(arr[i]))
    return aux


def corr_ewma(arr1, arr2):
    """
    Calcula Covarianza entre arr1 y arr2.
    :param arr1: df/Arreglo con valores (retornos) desde pasado a futuro. Tamaño n.
    :param arr2: df/Arreglo con valores (retornos) desde pasado a futuro. Tamaño n.
    :return: Sigma_{arr1, arr2}
    """
    r_1 = np.array(arr1)
    r_2 = np.array(arr2)
    n = len(arr1)
    lamb = 0.94
    pesos = 0.94 ** np.arange(len(r_1))[::-1]  # Dar más peso al futuro.
    return sum(r_2 * r_1 * pesos) * (1 - lamb)


def correlaciones(df_retornos):
    """
    Calcula correlaciones y volatilidades.
    :param df_retornos: DataFrame con los retornos en cada columna, SIN COLUMNA DE FECHA SOLO RETORNOS.
    :return: Matríz con correlaciones y arreglo con volatilidades.
    """
    # Nombre de las columnas de cada retorno.
    nombres = df_retornos.columns
    N = len(df_retornos.columns)
    M = np.ones([N, N])
    vol = []
    for i in np.arange(N):
        # Covarianza: tomar raíz.
        vol.append(np.sqrt(corr_ewma(df_retornos[nombres[i]], df_retornos[nombres[i]])))
    for i in np.arange(N):
        for j in np.arange(N):
            if i != j:
                M[i, j] = corr_ewma(df_retornos[nombres[i]], df_retornos[nombres[j]]) / (vol[i] * vol[j])
    return M, vol


def retorno_pivotes(df_curvas, conv="ACT360"):  # Es muy lento: 70s para todas las curvas.
    """
    Calcula retornos de factores de descuento en pivotes con ewma. Se demora 70s con 2340 curvas.
    :param df_curvas: df con la información de las curvas (futuro-->pasado).
    :return: df con retornos de cada pivote, coloca 0 para el retorno del primer día. (pasado-->futuro).
    """
    N = len(df_curvas["Fecha"])
    df = pd.DataFrame()  # Guardará los retornos.
    piv = plazosPiv
    orden = 0
    for plazo in piv:
        # Creación de arreglos facto y retorno para cada pivote.
        factores = np.zeros(N)
        retorno = [0]  # guarda en formato pasado-->futuro.
        for i in np.arange(N)[::-1]:  # (pasado-->futuro)
            # Fecha de la curva:
            fecha = df_curvas.loc[i].Fecha
            # Seleccionar curva.
            curvadf = df_curvas.loc[i]
            tir = TIR_DB(curvadf, plazo)
            fechafin = fecha + datetime.timedelta(plazo)
            factores[i] = factor_descuento(tir, fecha, fechafin, conv, orden)
            if i < N - 1:
                retorno.append(np.log(factores[i] / factores[i + 1]))

        df["Plazo " + str(plazo)] = retorno
    return df


def proyectar(df_tabla, fecha_ini, conv, cte_curva, M,
              vol):  # PEDIR SOLO CTE_CURVA Y QUE FECHA_INI SEA LA FECHA DE CTE_CURVA.
    """
    Proyecta los cupones del bono en los pivotes.
    :param df_tabla: DataFrame con la tabla de desarrollo de los pagos. Contiene columnas 'Fecha' y 'Cupon'.
    :param fecha_ini: Fecha de la valorización (fecha presente).
    :param conv: Conveción del bono (?)
    :param cte_curva: DataFrame con las ctes de la curva de fecha_ini.
    :param M: Matriz correlaciones.
    :param vol: Volatilidades.
    :return: DataFrame con la nueva tabla de desarrollo.
    """
    # Fechas de los pivotes contando deste fecha_ini.
    fechas_piv = fecha_pivotes(fecha_ini, plazosPiv)

    # Guarda las proyecciones sobre cada pivote.
    df = pd.DataFrame()
    df["Fecha"] = fechas_piv
    cupon = np.zeros(len(fechas_piv))

    # Calculo de las proyecciones.
    for i in np.arange(len(df_tabla["Fecha"])):  # Recorre pagos del bono.
        if df_tabla["Fecha"][i] >= fecha_ini:  # Solo los pagos después de fecha_ini.
            if df_tabla["Fecha"][i] <= fechas_piv[0]:
                plazo_flujo = plazo_anual_convencion(conv, fecha_ini, df_tabla["Fecha"][i])
                cupon[0] += df_tabla["Cupon"][i] / (
                        1 + TIR_DB(cte_curva, (df_tabla["Fecha"][i] - fecha_ini).days)) ** plazo_flujo
            elif df_tabla["Fecha"][i] >= fechas_piv[len(fechas_piv) - 1]:
                plazo_flujo = plazo_anual_convencion(conv, fecha_ini, df_tabla["Fecha"][i])
                cupon[len(fechas_piv) - 1] += df_tabla["Cupon"][i] / (
                        1 + TIR_DB(cte_curva, (df_tabla["Fecha"][i] - fecha_ini).days)) ** plazo_flujo
            else:
                # Info pivotes.
                ind_1 = mas_cercanas(fechas_piv, df_tabla["Fecha"][i])[0]
                ind_2 = mas_cercanas(fechas_piv, df_tabla["Fecha"][i])[1]
                piv_1 = fechas_piv[ind_1]
                piv_2 = fechas_piv[ind_2]
                plazo_p1 = (piv_1 - fecha_ini).days  # diferencia_dias_convencion(conv, fecha_ini, piv_1)
                plazo_p2 = (piv_2 - fecha_ini).days  # diferencia_dias_convencion(conv, fecha_ini, piv_2)
                plazo_flujo = plazo_anual_convencion(conv, fecha_ini, df_tabla["Fecha"][i])
                alpha_0 = plazo_anual_convencion(conv, piv_1, df_tabla["Fecha"][i]) / plazo_anual_convencion(conv,
                                                                                                             piv_1,
                                                                                                             piv_2)
                # Info tasas y parámetros.
                TIR_flujo = alpha_0 * TIR_DB(cte_curva, plazo_p1) + (1 - alpha_0) * TIR_DB(cte_curva, plazo_p2)
                VP_flujo = df_tabla["Cupon"][i] / ((1 + TIR_flujo) ** plazo_flujo)
                ro_12 = M[ind_1, ind_2]
                s_1 = vol[ind_1]
                s_2 = vol[ind_2]
                s_f = alpha_0 * s_1 + (1 - alpha_0) * s_2
                a = s_1 ** 2 + s_2 ** 2 - 2 * ro_12 * s_1 * s_2
                b = 2 * ro_12 * s_1 * s_2 - 2 * s_2 ** 2
                c = s_2 ** 2 - s_f ** 2

                # Solucion cuadrática.
                alpha = cuadratica(a, b, c)
                alpha = min(alpha)

                # Proyectar flujo en pivotes.
                cupon[ind_1] += alpha * VP_flujo
                cupon[ind_2] += (1 - alpha) * VP_flujo
    df["Cupon"] = cupon
    return df


df_bonos = ("SELECT TOP (10) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda ='CLP' ")
df_bonos = pd.read_sql(df_bonos, cn).sort_values(by="Fecha", ascending=False).groupby("Nemotecnico",
                                                                                       as_index=False).first()
convenciones = parsear_convenciones(df_bonos)
df_curvas = seleccionar_curvas(200)


# historico_factores(df_curvas, "ACT360", [30, 90, 180, 360, 360 * 2, 360 * 3, 360 * 4, 360 * 5, 360 * 7, 360 * 9, 360 * 10, 360 * 15, 360 * 20, 360*30])


def covarianzas(cor, vol):
    """
    Calcula matriz de varianza covarianza de los pivotes.
    :param cor: Matriz de correlaciones.
    :param vol: Volatilidades.
    :return: Arreglo 2-dim. Matriz de covarianza de los retornos (Como arreglo).
    """
    diag = np.diag(vol)
    return diag * cor * diag


def proyectar_varios(df_bonos, df_curvas, M, vol):
    """
    Proyecta varios bonos sobre los pivotes.
    :param df_bonos: DataFrame con la info de todos los bono a proyectar (SQL).
    :param df_curvas: DataFrame con la info de todas las curvas (SQL).
    :param M: Matriz de correlaciones de los pivotes.
    :param vol: Volatilidades de los pivotes.
    :return: Arreglo que guarda la proyección de los bonos como DataFrame.
    """
    # Arreglo que guarda las nuevas tablas de desarrollo y obtencion de curva más reciente (Fecha de la valorizacion).
    tabs_des = []
    conv = parsear_convenciones(df_bonos)
    curva = df_curvas.iloc[0]

    # Calculo de proyecciones.
    for i in np.arange(len(df_bonos["Fecha"])):
        # Obtener df del bono i-ésimo y su tabla de desarrollo.
        df_bono = df_bonos.iloc[i]
        df_tabla = pd.DataFrame(
            StrTabla2ArrTabla(df_bono["TablaDesarrollo"], str(df_bono["FechaEmision"]).split(" ")[0]),
            columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])

        # Agregar la proyección del i-ésimo bono.
        tabs_des.append(proyectar(df_tabla, curva["Fecha"], conv[i], curva, M, vol))
        # print(proyectar(df_bonos.iloc[i], curva["Fecha"], conv[i], curva, M, vol))
    return tabs_des


def volatilidad_cartera(df_bonos, acciones, df_curvas):
    """
    Calcula volatilidad de la cartera. Asume que las tablas de las acciones tienen el mismo n° de filas.
    :param df_bonos: DataFrame con info de los bonos.
    :param acciones: Arreglo con los nombres de acciones en string.
    :param df_curvas: DataFrame con la info de las curvas.
    :return: Volatilidad de la cartera.
    """
    # Df con retorno de los pivotes y cantidad de datos.
    df_pivotes = retorno_pivotes(df_curvas)
    M = len(df_pivotes[df_pivotes.columns[0]])
    df_pivotes.plot.hist(bins=20)
    plt.show()

    # Df con retorno de las acciones, valores presente de estas y cantidad de datos.
    vp = []
    df_acciones = pd.DataFrame()
    for accion in acciones:
        # Importar.
        df_accion = pd.read_excel('C:\\users\\javier\\desktop\\practica\\' + accion + '.xlsx')
        df_accion = df_accion.drop(columns=['Date', 'Open', 'High', 'Low', 'Volume'])
        df_accion["Adj Close shift"] = df_accion["Adj Close"].shift(1)

        # Calculo retorno y valor "presente" de la accion.
        df_accion["Retorno"] = np.log(df_accion["Adj Close"] / df_accion["Adj Close shift"])
        vp.append(df_accion.iloc[np.size(df_accion, 0) - 1]["Adj Close"])
        df_accion = df_accion.drop(columns=['Adj Close shift', 'Close'])
        df_accion["Retorno"][0] = 0  # Fijar retorno del primer día en 0.

        # Adjuntar retorno al df_acciones.
        df_acciones[accion] = df_accion["Retorno"]
        df_accion["Retorno"].plot.hist(bins=20)
        plt.title("Histograma retorno de " + accion)
        plt.show()
    N = len(df_acciones[acciones[0]])

    # Igualar cantidad de datos. Para mas instrumentos, tomar el mínimo.
    if M < N:
        df_acciones = df_acciones[:M]
    elif N < M:
        df_pivotes = df_pivotes[:N]

    # Dataframe con los retornos en conjunto. Orden: Acciones-Bonos.
    df_inst = pd.concat([df_acciones, df_pivotes], 1)
    cor, vol = correlaciones(df_inst)
    print("Retorno instrumentos: ")
    print(df_inst)
    print("Correlaciones: ")
    print(pd.DataFrame(cor))

    # Proyección de bonos y vector de valores presente.
    tabs_des = proyectar_varios(df_bonos, df_curvas, cor, vol)
    C = sum(tabs_des[i]["Cupon"] for i in range(len(tabs_des)))
    C = np.concatenate([vp, C])

    # Covarianza estimada y volatilidad en CLP.
    Cov = covarianzas(cor, vol)
    vol_cartera = np.sqrt(np.dot(np.dot(C, Cov), C))
    print("Volatilidad cartera en CLP: ")
    print(vol_cartera)
    print("Volatilidades acciones y bonos: ")
    print(pd.DataFrame(vol, columns=["Correlaciones"]))

    # Volatilidad en %.
    print("Volatilidad cartera en %: ")
    print((vol_cartera / sum(C)) * 100)

    return vol


# volatilidad_cartera(df_bonos, ['HABITAT.SN', 'IANSA.SN', 'ENTEL.SN'], df_curvas)


def ewma_estimacion(df_curvas, k):
    # Ratorno de pivotes y cantidad de días (n° curvas).
    df_pivotes = retorno_pivotes(df_curvas)
    df_retornos = retorno_pivotes(df_curvas, conv="ACT360")
    M = np.size(df_curvas, 0)

    # Arreglo que guarda las estimaciones y variables útiles.
    estimaciones_vol = []
    nombres = df_retornos.columns
    vol = 0

    # Calculo de las estimaciones en función de la cantidad de datos.
    for i in np.arange(M):
        est = np.sqrt(corr_ewma(df_retornos[nombres[k]][-i:], df_retornos[nombres[k]][-i:]))
        estimaciones_vol.append(est)
        if i == M - 1:
            vol = est
    plt.plot(estimaciones_vol, '*')
    plt.plot(np.ones(M) * vol, label="Estimación final")
    plt.legend()
    plt.title("Estimación con ewma en función de cantidad de datos")
    plt.show()


# ewma_estimacion(df_curvas, 3)