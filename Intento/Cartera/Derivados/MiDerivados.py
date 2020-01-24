# 20-01

import timeit
from Derivados.DerivadosTipos.DerivadosSCC import *
from Derivados.DerivadosTipos.DerivadosFWD import *
from Derivados.DerivadosTipos.DerivadosSUC import *
import pyodbc
from Derivados.proyeccion import *
import matplotlib.pyplot as plt
from Bonos.LibreriasUtiles.UtilesValorizacion import plazo_anual_convencion

pd.set_option('display.max_columns', None)

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cnn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

P = dict()
P["CLP"] = plazosPiv
P["USD"] = plazosPiv
P["UF"] = plazosPiv


def reformat_fecha(fecha):
    """

    :param fecha:
    :return:
    """
    fecha = "/".join(str(fecha).split(" ")[0].split("-")[::-1])
    return fecha


def tabla_paridad():
    """
    Busca tabla paridad.
    :return: Tabla paridad como DataFrame.
    """
    tabla = ("SELECT TOP(1000) [Tipo], [Mercados], [Moneda] FROM[dbDerivados].[dbo].[TdParidadMonedasCurvasDescuento]")
    tabla = pd.read_sql(tabla, cnn)
    return tabla


tablaParidad = tabla_paridad()


def seleccionar_derivado(ID_key, fecha_ini, hora='1700'):
    """
    Selecciona derivado de la base de datos.
    :param hora: Hora de la valo
    :param ID_key: Identificación del derivado.
    :param fecha_ini: datetime.date. Fecha valorización.
    :return: DerivadosAbstracto. El derivado.
    """
    derivado = ("SELECT TOP (1) * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] WHERE ID_Key = '"
                + str(ID_key) + "'")
    derivado = pd.read_sql(derivado, cnn)

    # Fechas como string formato dd/mm/aa
    FechaVenc = reformat_fecha(derivado["FechaVenc"][0])  # "12/03/2020"
    FechaEfectiva = reformat_fecha(derivado["FechaEfectiva"][0])  # "12/03/2018"
    derivado["FechaVenc"] = [FechaVenc]
    derivado["FechaEfectiva"] = [FechaEfectiva]
    derivado["ID"] = [int(derivado["ID"][0])]

    return DerivadosSCC(fecha_ini, hora, derivado, cnn)


# miDerivado.procesar_todo()

# MonActivo = miDerivado.info_cartera.MonedaActivo[0]


def buscar_curvas(mon, n=1000):
    """
    Busca las curvas asociadas a la moneda mon de la basde de datos.
    :param mon: Str con el tipo de moneda (MonedaActivo).
    :param n: Int. Cantidad de curvas.
    :return: DataFrame con n curvas asociadas al derivado. Formato: futuro --> pasado.
    """

    # Str con nombre de la curva (busca en tabla de paridad, uno-a-uno).
    strCurva = tablaParidad["Tipo"][tablaParidad["Moneda"] == mon].values[0]

    # Seleccionar curvas asociadas al derivado.
    curvas = ("SELECT TOP (" + str(
        n) + ") [Fecha], [Hora], [Tipo], [Curva] FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE "
             "Tipo = '" + strCurva + "' AND Hora = '1700'")
    curvas = pd.read_sql(curvas, cnn)
    return curvas


def plot_curva_efectiva(mon):
    """
    Plot de la curva efectiva para moneda mon.
    :param mon: Moneda en string. Ej "USD", "CLP".
    :return: Plot.
    """
    df_curvas = buscar_curvas(mon, 1)
    A = parsear_curva(df_curvas["Curva"][0], df_curvas["Fecha"])
    x = []
    y = []
    for i in np.arange(np.size(A, 0)):
        x.append(float(A[i][0]))
        y.append(float(A[i][1]))
    plt.title(mon)
    plt.ylabel("Facto descuento")
    plt.xlabel("Días")
    plt.plot(x, y, '*')
    plt.show()


def historico_factor_derivado(df_curvas, plazo):
    """

    :param df_curvas: Curvas para calcular el historico.
    :param plazo: int. Cantidad de días.
    :return: DataFrame con columnas de fecha y factor del plazo (pasado--futuro).
    """

    # Curvas requeridas (futuro-->pasado) y cantidad de estas.
    N = np.size(df_curvas, 0)

    # DataFrame que guardará el historico con columna de fecha.
    df = pd.DataFrame()

    factores = []
    fechas = []
    for i in np.arange(N):
        # Obtener factor de i-ésima curva en plazo.
        s = df_curvas["Curva"][i]
        fecha = df_curvas["Fecha"][i]
        factores.append(interpolacion_log_escalar(plazo, parsear_curva(s, fecha)))
        fechas.append(fecha)

    # Se da vuelta para que vaya de pasado a futuro.
    df["Fecha"] = fechas[::-1]
    df[str(plazo) + " dias"] = factores[::-1]
    return df


def retorno_piv_der(mon):
    """
    Retorno de los pivotes aplicado a derivados.
    :param mon: Str. Tipo de moneda. Ej: CLP, EUR, USD.
    :return:
    """
    # Pivotes asociados a mon.
    plazos_piv = P[mon]

    # Obtener curvas.
    df_curvas = buscar_curvas(mon, 200)

    # Data frame que en cada columna tendrá el retorno de cada pivotes.
    df = pd.DataFrame()

    # Calculo de retornos para cada pivote.
    for plazo in plazos_piv:
        # Coloca retorno del plazo en df. Retorno viene con solo una columna.
        pre = historico_factor_derivado(df_curvas, plazo)
        ret = retorno(pre)
        df[str(plazo) + " dias"] = ret[ret.columns[0]]
    return df


def proyectar_der(df_tabla, fecha_ini, conv, df_curva, M, vol):
    """
    Proyectalos pagos de la tabla de desarrollo para obtener
    :param df_tabla: DataFrame. Tabla de desarrollo del derivado. Contiene columnas 'FechaPago'  y 'Flujo'.
    :param fecha_ini: Fecha de valorización.
    :param conv: Str. Convención del derivado (?).
    :param df_curva: DataFrame con la curva, en fecha_ini, correspondiente al derivado.
    :param M: Arreglo 2-dim. Matríz de correlaciones de los pivotes.
    :param vol: Arreglo 1-dim. Vector con las volatilidades de los pivotes.
    :return: """

    # Fechas de los pivotes contando deste fecha_ini y matríz de la curva.
    fechas_piv = fecha_pivotes(fecha_ini, plazosPiv)
    A = parsear_curva(df_curva["Curva"][0], df_curva["Fecha"][0])

    # Guarda las proyecciones sobre cada pivote. Con columnas 'FechaPago' y 'Flujo'.
    df = pd.DataFrame()
    df["FechaPago"] = fechas_piv
    cupon = np.zeros(len(fechas_piv))

    # Calculo de las proyecciones.
    # Recorre pagos del bono.
    for i in np.arange(len(df_tabla["FechaPago"])):
        # Solo los pagos después de fecha_ini.
        if df_tabla["FechaPago"][i] >= fecha_ini:

            # Si el pago es antes del primer pivote, se suma al primer pivote.
            if df_tabla["FechaPago"][i] <= fechas_piv[0]:
                plazo_flujo = diferencia_dias_convencion(conv, fecha_ini, df_tabla["Fecha"][i])
                factor = interpolacion_log_escalar(plazo_flujo, A)
                cupon[0] += df_tabla["Flujo"][i] * factor

            # Si el pago es depués del último pivote, se suma al último pivote.
            elif df_tabla["FechaPago"][i] >= fechas_piv[len(fechas_piv) - 1]:
                plazo_flujo = diferencia_dias_convencion(conv, fecha_ini, df_tabla["FechaPago"][i])
                factor = interpolacion_log_escalar(plazo_flujo, A)
                cupon[len(fechas_piv) - 1] += df_tabla["Flujo"][i] * factor

            # Proyectar en pivotes correspondientes.
            else:
                # Info pivotes. Indices: ind_1 pivote izquierdo, ind_2 pivote derecho.
                ind_1 = mas_cercanas(fechas_piv, df_tabla["FechaPago"][i])[0]
                ind_2 = mas_cercanas(fechas_piv, df_tabla["FechaPago"][i])[1]
                piv_1 = fechas_piv[ind_1]
                piv_2 = fechas_piv[ind_2]
                plazo_p1 = diferencia_dias_convencion(conv, fecha_ini, piv_1)  # (piv_1 - fecha_ini).days
                plazo_p2 = diferencia_dias_convencion(conv, fecha_ini, piv_2)  # (piv_2 - fecha_ini).days
                plazo_flujo = diferencia_dias_convencion(conv, fecha_ini, df_tabla["FechaPago"][i])
                alpha_0 = plazo_anual_convencion(conv, piv_1, df_tabla["FechaPago"][i]) / plazo_anual_convencion(conv,
                                                                                                                 piv_1,
                                                                                                                 piv_2)
                # Info tasas y parámetros.
                factor = interpolacion_log_escalar(plazo_flujo, A)
                VP_flujo = df_tabla["Flujo"][i] * factor
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
    df["Flujo"] = cupon
    return df


"""
print("-------------------Retornos-------------------")
print(r)
print("-------------------Volatilidades-------------------")
print(pd.DataFrame(vol))
print("-------------------correlaciones-------------------")
print(pd.DataFrame(cor))
print("-------------------Covarianzas-------------------")
print(pd.DataFrame(covarianzas(cor, vol)))"""

"""# Objeto derivado.
miDerivado = seleccionar_derivado(146854, datetime.date(2018, 4, 18))
miDerivado2 = seleccionar_derivado(146854, datetime.date(2019, 4, 18))

miDerivado.genera_flujos()
miDerivado.valoriza_flujos()
miDerivado2.genera_flujos()
miDerivado2.valoriza_flujos()
frame = miDerivado.get_flujos_valorizados()
frame2 = miDerivado2.get_flujos_valorizados()

r = retorno_piv_der("CLP")
cor, vol = correlaciones(r)

df_curva = ("SELECT TOP (1) [Fecha], [Hora], [Tipo], [Curva] FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE "
            "Tipo = 'CurvaEfectiva_CLP' AND Hora = '1700' AND Fecha = '2018-04-18 00:00:00'")
df_curva = pd.read_sql(df_curva, cnn)

df_proyeccion = proyectar_der(frame[['FechaPago', 'Flujo']], miDerivado.fechaActual, "ACT360", df_curva, cor, vol)
print(df_proyeccion)

print("aaaaaaaaaa")
print(sum(df_proyeccion["Flujo"]))
print(sum(frame["ValorPresenteMonFlujo"]))
print("aaaaaaaaaa")"""


