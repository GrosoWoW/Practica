# -*- coding: utf-8 -*-
import datetime
import pandas as pd
from Util import add_days, add_months, add_years, es_bisiesto, fecha_str, send_msg


def cast_convencion(conv):
    """Castea la convención conv a un string estandar para consultas SQL

    :param conv: String con la convención
    :return: String con la convención casteada
    """
    res = {
        "30/360A": "30/360",
        "30/360": "30/360",
        "30/360 US": "30/360",
        "30/360US": "30/360",
        "30U/360": "30/360",
        "Bond basis": "30/360",
        "360/360": "30/360",
        "ISMA-30/360": "30/360",
        "ISMA-30/360 NONEOM": "30/360",
        "30/360 NON-EOM": "30/360",

        "ACT/365": "ACT365",
        "ACT365": "ACT365",
        "NL365": "ACT365",
        "NL/365": "ACT365",

        "ACT/360": "ACT360",
        "ACT360": "ACT360",

        "ACT/ACT": "ACTACT",
        "ACTACT": "ACTACT",
        "ISDA ACT/ACT": "ACTACT",
        "ACT/ACT NON-EOM": "ACTACT",

        "LACT360": "LACT360",
        "LACT/360": "LACT360",

        "LACT30": "LACT30",
        "LACT/30": "LACT30",
        
        "BUS DAYS/252": "ACTACT"  # Provisorio
    }.get(conv.strip(), "")

    return res


def diferencia_dias_convencion(convencion, fechaini, fechafin):
    """Entrega la diferencia de días entre fechaini y fechafin según la convencion.
    Es importante para el caso 30/360, ya que usa 30/360 USA
    :param convencion: Sring indicando la convención
    :param fechaini: datetime.date con fecha inicial
    :param fechafin: datetime.date con fecha final
    :return: int cantidad de días entre fechaini y fechafin con la convención
    """
    y1 = fechaini.year
    y2 = fechafin.year
    m1 = fechaini.month
    m2 = fechafin.month
    d1 = fechaini.day
    d2 = fechafin.day

    conv = cast_convencion(convencion)

    if conv == "30/360":
        if add_days(fechaini, 1).day == 1 and m1 == 2:
            d1 = 30
            if add_days(fechafin, 1).day == 1 and m2 == 2:
                d2 = 30
        if d2 == 31 and 31 >= d1 >= 30:
            d2 = 30
        if d1 == 31:
            d1 = 30
        plazo = (360*(y2-y1) + 30*(m2-m1) + (d2-d1))

    elif conv in ["ACT360", "LACT360", "ACT365", "ACTACT", "LACT30"]:
        plazo = (fechafin - fechaini).days
    else:
        print("ERROR")
        pass  # todo
    return plazo


def factor_ACTACT_day_count(fecha1, fecha2):
    """Retorna el factor ACT/ACT según las fechas ingresadas.
    Implementado según la definición ISDA

    :param fecha1: datetime.date
    :param fecha2: datetime.date
    :return: float con el factor ACT/ACT entre las fechas
    """
    # Si las fechas son iguales
    if fecha1 == fecha2:
        return 0

    # Pasan días de forma negativa
    if fecha1 > fecha2:
        return -1 * factor_ACTACT_day_count(fecha2, fecha1)

    # Se preparan divisores
    if es_bisiesto(fecha1):
        div1 = 366
    else:
        div1 = 365

    if es_bisiesto(fecha2):
        div2 = 366
    else:
        div2 = 365

    # Si es el mismo año
    if fecha1.year == fecha2.year:
        return (fecha2-fecha1).days / div1

    # Aporte por años completos entre fechas
    year_dif = fecha2.year - fecha1.year - 1

    # Aporte de la fecha1 en su año
    factor_fecha1 = (datetime.date(fecha1.year+1, 1, 1) - fecha1).days / div1
    # Aporte de la fecha2 en su año
    factor_fecha2 = (fecha2 - datetime.date(fecha2.year, 1, 1)).days / div2

    # Se suma
    return year_dif + factor_fecha1 + factor_fecha2


def plazo_anual_convencion(convencion, fechaini, fechafin):

    dif = diferencia_dias_convencion(convencion, fechaini, fechafin)
    res = {
        "30/360": dif/360,
        "ACT360": dif/360,
        "LACT360": dif/360,
        "LACT30": dif/30,
        "ACT365": dif/365,
        "ACTACT": dif/365
    }.get(cast_convencion(convencion), "")
    if res == "":
        # todo
        pass

    return res


def base_convencion(conv):
    res = {"30/360": 360,
           "ACT360":360,
           "LACT360":360,

           "LACT30":30,

           "ACT365":365,
           "ACTACT":365}.get(cast_convencion(conv), "")

    return res


def factor_descuento(tir, fechaini, fechafin, convencion, orden):
    plazo = plazo_anual_convencion(convencion, fechaini, fechafin)

    if convencion == "LACT360" or convencion == "LACT30":
        res = {
            0: 1/(1 + tir*plazo),
            1: -plazo / (1 + tir*plazo)**2,
            2: 2*plazo*plazo / ((1+tir*plazo)**3)
        }.get(orden, "")

        if res == "":
            pass  # ERROR
        return res
    else:
        res = {
            0: 1 / ((1 + tir) ** plazo),
            1: -plazo / (1 + tir) ** (plazo + 1),
            2: plazo * (plazo + 1) / ((1 + tir) ** (plazo + 2))
        }.get(orden, "")

        if str(res) == "":
            pass  # ERROR
        return res


def parsear_curva(curva, fecha):
    """
    Parsea la curva para la fecha indicada y entrega un arreglo con los valores sin header
    :param curva: String con los valores de la curva en el formato 'plazo#valor|plazo1#valor1|..'
    :param fecha: datetime.date con la fecha para la curva
    :return: array de dos columnas con los valores (SIN HEADER)
    """
    res = []
    filas = curva.split('|')
    header = filas[0].split("#")
    if header[0] == 'Plazo':
        for fila in filas[1:]:
            valores_fila = fila.split('#')
            valores_fila[0].replace(",", ".")
            valores_fila[1] = valores_fila[1].replace(",", ".")
            res.append(valores_fila)
    else:
        for fila in filas[1:]:
            valores_fila = fila.split('#')
            if int(valores_fila[0]) >= 30:
                valores_fila[0] = (add_months(fecha, int(int(valores_fila[0]) / 30)) - fecha).days
            valores_fila[1] = valores_fila[1].replace(",", ".")
            res.append(valores_fila)
    return res


def tipo_cambio_FWD(moneda1, moneda2, mercado, fecha, hora, plazo, cn):
    res = [0, 0, 0, 0]
    if plazo <= 0:
        res[0] = tipo_cambio(moneda1, moneda2, add_days(fecha, plazo), hora, cn)
        res[1] = res[0]
        res[2] = 1
        res[3] = 1
    else:
        tc = tipo_cambio(moneda1, moneda2, fecha, hora, cn)
        fd1 = factor_descuento_monedas(moneda1, mercado, fecha, hora, plazo, cn)
        fd2 = factor_descuento_monedas(moneda2, mercado, fecha, hora, plazo, cn)
        res[0] = tc * fd1 / fd2
        res[1] = tc
        res[2] = fd1
        res[3] = fd2
    return res


def tipo_cambio(moneda1, moneda2, fecha, hora, cn):
    arr = ("SELECT * "
           "FROM dbAlgebra.dbo.VwMonedas_Temp Vw1 "
           "WHERE Plazo360 = 0 AND Hora = '" + hora + "' AND Tipo = 'TipoCambio' "
           "AND Fecha = " + fecha_str(fecha) + " AND Campo = 'PX_LAST'")
    arr = pd.io.sql.read_sql(arr, cn)
    camino = ("SELECT * FROM dbDerivados.dbo.FnCaminoMonedas()")
    camino = pd.io.sql.read_sql(camino, cn)

    return valor_moneda(moneda1, moneda2, camino, arr)


def valor_moneda(moneda_inicio, moneda_fin, camino_monedas, valores):
    """

    :param moneda_inicio:
    :param moneda_fin:
    :param camino_monedas:
    :param valores:
    :return:
    """

    if moneda_inicio == moneda_fin:
        return 1

    df_camino = camino_monedas.loc[camino_monedas['MonedaActiva'] == moneda_inicio]
    df_camino = df_camino.loc[df_camino['MonedaPasiva'] == moneda_fin]

    if len(df_camino) == 0 or len(df_camino) != df_camino.Total.iloc[0]:
        send_msg("ERROR: valor_moneda: No se encontró camino para", moneda_inicio, moneda_fin)
        return

    cambios = df_camino[['MonedaActivaPuente', 'MonedaPasivaPuente']]
    cambios.columns = ['mAct', 'mPas']

    res = 1
    for i in range(len(cambios)):
        aux = valores[(valores.MonedaActiva == cambios.mAct.iloc[i]) & (valores.MonedaPasiva == cambios.mPas.iloc[i])]
        res = res * aux.Valor.iloc[0]
    return res


def factor_descuento_inv_arr(fecha, arr, convencion):

    for i in range(len(arr)):
        plazo = plazo_anual_convencion(convencion, fecha, add_days(fecha, int(float(arr[i][0]))))

        if plazo == 0:
            arr[i][1] = -1000

        else:
            if convencion == "LACT360" or convencion == "LACT30":
                arr[i][1] = 100 * ((1 / float(arr[i][1])) - 1) / plazo

            else:
                arr[i][1] = 100 * (float(arr[i][1]) ** (-1 / plazo) - 1)

        if len(arr) > 0 and arr[0][0] == 0:
            arr[0][1] = arr[1][1]

    if len(arr) > 0 and int(float(arr[0][0])) == 0:
        arr[0][1] = arr[1][1]
    return arr

def StrTabla2ArrTabla(strTabla, fechaEmision):
    tabla = "0#"+fechaEmision+"#0#0#100#0|"+strTabla
    arreglo = tabla.split("|")
    Flujos = pd.DataFrame(columns=['flujos'])
    row = Flujos
    row = pd.DataFrame({'flujos':arreglo})
    Flujos = Flujos.append(row)
    Flujos = Flujos["flujos"].str.split("#")
    for i in range(1, len(Flujos)):
        Flujos[i][3] = float(Flujos[i][3].replace(',','.'))
        Flujos[i][4] = float(Flujos[i][4].replace(',','.'))
        Flujos[i][2] = float(Flujos[i][2].replace(',','.'))
        Flujos[i][5] = float(Flujos[i][5].replace(',','.'))
        Flujos[i][1] = datetime.datetime.strptime(Flujos[i][1], '%d-%m-%Y').strftime('%Y-%m-%d')
        Flujos[i][1] = datetime.datetime.strptime(Flujos[i][1], '%Y-%m-%d')
    Flujos[0][3] = float(Flujos[0][3].replace(',','.'))
    Flujos[0][4] = float(Flujos[0][4].replace(',','.'))
    Flujos[0][2] = float(Flujos[0][2].replace(',','.'))
    Flujos[0][5] = float(Flujos[0][5].replace(',','.'))
    Flujos[0][1] = datetime.datetime.strptime(Flujos[0][1], '%Y-%m-%d')
    array = np.insert(Flujos.values[0], 2, fechaEmision)
    for i in range(1,len(Flujos.values)):
        array = np.vstack((array, np.insert(Flujos.values[i], 2, fechaEmision)))

    return array


def SumaDelta(Tasa, delta):
    if type(Tasa) == int or type(Tasa) == float:
        return Tasa+delta
    else:
        for i in range(0, len(Tasa)):
            Tasa[i] = Tasa[i] +delta
        return Tasa