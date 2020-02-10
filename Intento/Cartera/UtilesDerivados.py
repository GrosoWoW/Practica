# -*- coding: utf-8 -*-
"""Módulo con funciones auxiliares para el cálculo de derivados.
"""
import datetime
import pandas as pd
import numpy as np
from UtilesValorizacion import tipo_cambio, cast_convencion, factor_descuento
from Util import remove_col, fecha_str, add_days, add_months, add_years, send_msg, sub_arr
from Matematica import interpolacion_log_escalar


def siguiente_habil_pais(fecha, pais, cn):
    """Retorna el día hábil siguiente a la fecha en el país indicado

        :param fecha: datetime.date con la fecha que se desea el día hábil siguiente
        :param pais: String con el código de país ("BR","MX","US"...)
        :param cn: pyodbc.connect conexión a base de datos
        :return: datetime.date con el día hábil siguiente
        """
    # Si la fecha es inválida
    if fecha == datetime.date(1900, 1, 1):
        return datetime.date(1900, 1, 1)

    # Países en TdFeriados
    paises = ["BR", "MX", "US", "CO", "UK", "PE", "CR", "RD"]
    if pais in paises:
        # Hábil mínimo y máximo en TdFeriados
        sql = ("SELECT MAX(fecha) AS maxi, MIN(fecha) AS mini "
               "FROM dbAlgebra.dbo.TdFeriados "
               "WHERE Pais='" + pais + "' AND SiHabil=1")

    else:  # elseif pais = 'CL'
        # Hábil mínimo y máximo en TdIndicadores
        sql = ("SELECT MAX(fecha) AS maxi, MIN(fecha) AS mini "
               "FROM dbAlgebra.dbo.TdIndicadores "
               "WHERE Feriado = 0")

    # Se consulta y extrae hábil máximo y mínimo
    fechas = pd.io.sql.read_sql(sql, cn)
    fecha_max = fechas.iloc[0]['maxi'].to_pydatetime().date()
    fecha_min = fechas.iloc[0]['mini'].to_pydatetime().date()
    if fecha_min <= fecha <= fecha_max and pais != "--":
        sql += " AND Fecha > " + fecha_str(fecha)
        fecha = pd.io.sql.read_sql(sql, cn).iloc[0]['mini'].to_pydatetime().date()


    else:
        fecha = add_days(fecha, 1)
    # Si es domingo
    if fecha.weekday() == 6:
        fecha = add_days(fecha, 1)
    # Si es sábado
    elif fecha.weekday() == 5:
        fecha = add_days(fecha, 2)

    return fecha


def siguiente_habil_paises(fecha, paises, cn):
    """Retorna el día hábil siguiente a la fecha tal que en todos los paises es día hábil.
        Si realiza más de 10 recursiones retorna False como error

        :param fecha: datetime.date con la fecha que se desea el día hábil siguiente
        :param paises: Arreglo de string con los códigos de países ("BR","MX","US"...)
        :param cn: Objeto de conexión a base de datos a través de pyodbc.connect
        :return: datetime.date con el día hábil siguiente. False como error
        """
    # Si la fecha es minima
    if fecha == datetime.date(1900, 1, 1):
        return fecha  # No se busca otra

    pais_fechas = {}
    fecha_max = fecha

    for c in range(10):
        valido = True
        fecha_aux = siguiente_habil_pais(fecha, paises[0], cn)
        for pais in paises[1:]:
            if siguiente_habil_pais(fecha, pais, cn) != fecha_aux:
                valido = False
                break
        if valido:
            return fecha_aux
        fecha = fecha_aux

    #    for pais in paises:
#
    #        pais_fechas[pais] = siguiente_habil_pais(fecha, pais, cn)
#
    #        if pais_fechas[pais] > fecha_max:
    #            fecha_max = pais_fechas[pais]
#
    #    valido = True
    #    for pais in paises:
    #        if pais_fechas[pais] != fecha_max:
    #            valido = False
#
    #    if valido:
    #        return fecha_max
    #    else:
    #        fecha = add_days(fecha_max, -1)

    # Se hicieron 10 intentos
    return False


def ultimo_habil_pais(fecha, pais, cn):
    """Retorna el día hábil anterior a la fecha en el país indicado
    Si la fecha es hábil, se retorna la misma

    :param fecha: datetime.date con la fecha que se desea el día hábil anterior
    :param pais: String con el código de país ("BR","MX","US"...)
    :param cn: Objeto de conexión a base de datos a través de pyodbc.connect
    :return: datetime.date con el día hábil anterior
    """

    # Si la fecha es inválida
    if fecha == datetime.date(1900, 1, 1):
        return datetime.date(1900, 1, 1)

    # Países en TdFeriados
    paises = ["BR", "MX", "US", "CO", "UK", "PE", "CR", "RD"]
    if pais in paises:
        # Hábil mínimo y máximo en TdFeriados
        sql = ("SELECT MAX(fecha) AS maxi, MIN(fecha) AS mini "
               "FROM dbAlgebra.dbo.TdFeriados "
               "WHERE Pais='" + pais + "' AND SiHabil=1")

    else:  # elseif pais = 'CL'
        # Hábil mínimo y máximo en TdIndicadores
        sql = ("SELECT MAX(fecha) AS maxi, MIN(fecha) AS mini "
               "FROM dbAlgebra.dbo.TdIndicadores "
               "WHERE Feriado = 0")

    # Se consulta y extrae hábil máximo y mínimo
    fechas = pd.io.sql.read_sql(sql, cn)
    fecha_max = fechas.iloc[0]['maxi'].to_pydatetime().date()
    fecha_min = fechas.iloc[0]['mini'].to_pydatetime().date()

    if fecha_min <= fecha <= fecha_max and pais != "--":
        sql += " AND Fecha <= " + fecha.strftime("'%Y%m%d'")
        fecha = pd.io.sql.read_sql(sql, cn).iloc[0]['maxi'].to_pydatetime().date()

    else:
        # Si es domingo
        if fecha.weekday() == '6':
            fecha = fecha.AddDays(-2)
        # Si es sábado
        elif fecha.weekday() == '5':
            fecha = fecha.AddDays(-1)

    return fecha


def ultimo_habil_paises(fecha, paises, cn):
    """Retorna el día hábil anterior a la fecha tal que en todos los paises es día hábil.
    Si realiza más de 10 recursiones retorna False como error

    :param fecha: datetime.date con la fecha que se desea el día hábil anterior
    :param paises: Arreglo de string con los códigos de países ("BR","MX","US"...)
    :param cn: Objeto de conexión a base de datos a través de pyodbc.connect
    :return: datetime.date con el día hábil anterior. False como error
    """

    # Si la fecha es minima
    if fecha == datetime.date(1900, 1, 1):
        return fecha  # No se busca otra

    fecha_aux = fecha  # Primero se revisa la fecha actual

    # Se revisan máximo 10 días
    for c in range(10):
        valido = True  # Se asume es un día hábil para todos

        for pais in paises:  # Por cada país

            s = ultimo_habil_pais(fecha_aux, pais, cn)  # Se revisa el día hábil

            if s != fecha_aux:  # Si aux no era hábil para todos
                valido = False  # Ya no es válido
                fecha_aux = s
                break  # No es necesario preguntar por el resto de países (se sale del for)

        # Si aún es válido, la fecha_aux cumple
        if valido:
            return fecha_aux

    # Se hicieron 10 intentos
    return False


def cast_frecuencia(frecuencia):
    """Castea un string de frecuencia a una forma más standar
    Si la frecuencia ingresada no corresponde, se retorna un String vacío

    :param frecuencia: String con alguna frecuencia
    :return: String correspondiente a la frecuencia de forma standar para el proceso. String vacío si no corresponde
    """

    # Se maneja como un diccionario
    # Equivalente a un switch
    res = {
        'Semi Annual': '6M',
        'Semi annual': '6M',
        '6M': '6M',
        'Semi anual': '6M',
        'Semianual': '6M',
        'Semi_Annual': '6M',
        'Quarterly': '3M',
        '3M': '3M',
        'Trimestral': '3M',
        'Annualy': '1A',
        '1A': '1A',
        'Anual': '1A',
        '28 Dias': '28D',
        '28D': '28D',
        'Mensual': '1M',
        '1M': '1M',
        'Cero': 'Cero',
    }.get(frecuencia, "")
    # .get busca la frecuencia y si no la encuentra entrega el segundo parametro

    return res


def delta_frecuencia(fecha, frecuencia, n):
    fecha_aux = fecha
    signo = n/abs(n)
    for i in range(1, abs(n) + 1):
        fecha_aux = {
            '6M': add_months(fecha_aux, signo * 6),
            '3M': add_months(fecha_aux, signo * 3),
            '1A': add_years(fecha_aux, signo),
            '28D': add_days(fecha_aux, signo * 28),
            '1M': add_months(fecha_aux, signo),
            'Cero': datetime.date(1900, 1, 1),
        }.get(cast_frecuencia(frecuencia), "")
    return fecha_aux


def genera_flujos(fecha, fecha_efectiva, fecha_venc, tasa, frecuencia, convencion, si_principal=1):
    i = 0
    fechai = fecha_venc
    arr = []
    while fechai > fecha and fechai > add_days(fecha_efectiva, 10):
        arr.append([None] * 7)
        fecha_cupon_ant = max(delta_frecuencia(fechai, frecuencia, -1), fecha_efectiva)
        arr[i][0] = fechai
        arr[i][1] = (1 / factor_descuento(tasa / 100, fecha_cupon_ant, fechai, convencion, 0)
                     - 1) * 100
        arr[i][2] = arr[i][0]
        arr[i][3] = 0
        arr[i][4] = arr[i][1]
        arr[i][5] = 0
        if fecha_cupon_ant <= fecha:
            arr[i][6] = arr[i][1] * (fecha - fecha_cupon_ant).days / (fechai - fecha_cupon_ant).days
        else:
            arr[i][6] = 0
        if i == 0 and si_principal == 1:
            arr[i][1] = arr[i][1] + 100
            arr[i][3] = arr[i][3] + 100
        i += 1
        fechai = delta_frecuencia(fechai, frecuencia, -1)

    arr.reverse()
    return arr


def cast_moneda(moneda):
    if moneda == "UF":
        return "CLF"
    if moneda == "CLN":
        return "COP"
    return moneda


def cast_mercado(mercado, moneda):
    if mercado.lower() == "local":
        mercado = "Local"
    if mercado == "":
        mercado = "--"
    if cast_moneda(moneda) != "BRL" and cast_moneda(moneda) != "USD":
        return "--"
    else:
        return mercado


def curva_efectiva(moneda, fecha, mercado, hora, filtro, cn):
    """ Entrega los plazos y factores de descuento para flujos en la moneda correspondiente en un dataframe de pandas

    :param moneda:
    :param fecha:
    :param mercado:
    :param hora:
    :param filtro:
    :param cn:
    :return: dataframe de pandas con la información de plazos y factores de descuento
    """
    mercado = cast_mercado(mercado, moneda)
    moneda = cast_moneda(moneda)
    if mercado == "--":
        m2 = ""
    else:
        m2 = "_" + mercado

    arr = []
    if filtro == -2:
        # Puntos de la curva de 1 a 365 dias
        for i in range(365+1):  # +1 para que incluya el 365
            arr.append(i)

        # Puntos de la curva de 30 días en 30 días durante 10 años
        for i in range(1, 10*12+1): # +1 para que incluya el 10+12
            arr.append(i*30 + 365)

        # Puntos de la curva de 180 días en 180 días durante 20 años
        for i in (1, 20*2 + 1):  # +1 para que se incluya el 20*2
            arr.append((i * 180) + (10 * 12 * 30) + 365)

        # Se genera un string para todos los plazos
        plazos = arr[0]
        for i in range(1, len(arr)):
            plazos = plazos + ", " + arr[i]

        sql = ("SELECT DATEADD(day, Plazo, Fecha) AS Fecha, Plazo, Valor as FD, "
               "ROUND(CASE WHEN Plazo = 0 THEN 0 ELSE 1/Power(Valor,Cast(360 AS float)/Plazo)-1 End * 100,2) as Act360 "
               "FROM [dbDerivados].[dbo].[FnCompletaCurvasDerivados] "
               "(" + fecha_str(fecha) + ",'" + hora + "','CurvaEfectiva_" + moneda + m2 +"', " + arr[-1] + ",'Log',1)"
               "WHERE Plazo in (" + plazos + ") ORDER BY Plazo")

    elif filtro == -1:  # básicos
        sql = ("SELECT DATEADD(day, Plazo, Fecha) AS Fecha, Plazo, Valor as FD, "
               "ROUND(CASE WHEN Plazo = 0 THEN 0 ELSE 1/Power(Valor,Cast(360 AS float)/Plazo)-1 End * 100,2) as Act360 "
               "FROM [dbDerivados].[dbo].[FnParseaCurvasDerivados] "
               "(" + fecha_str(fecha) + ", '" + hora + "', 'CurvaEfectiva_" + moneda + m2 + "') "
                "ORDER BY Plazo")

    elif filtro == 0:  # completa hasta donde se pueda
        sql = ("SELECT DATEADD(day, Plazo, Fecha) AS Fecha, Plazo, Valor as FD, "
               "ROUND(CASE WHEN Plazo = 0 THEN 0 ELSE 1/Power(Valor,Cast(360 AS float)/Plazo)-1 End * 100,2) as Act360 "
               "FROM [dbDerivados].[dbo].[FnCompletaCurvasDerivados] "
               "(" + fecha_str(fecha) + ",'" + hora + "','CurvaEfectiva_" + moneda + m2 + "', -1, 'Log',1) "
                "ORDER BY Plazo")

    elif filtro > 0:  # completa hasta un plazo fijo
        sql = ("SELECT DATEADD(day, Plazo, Fecha) AS Fecha, Plazo, Valor as FD, "
               "ROUND(CASE WHEN Plazo = 0 THEN 0 ELSE 1/Power(Valor,Cast(360 AS float)/Plazo)-1 End * 100,2) as Act360 "
               "FROM [dbDerivados].[dbo].[FnCompletaCurvasDerivados] "
               "(" + fecha_str(fecha) + ",'" + hora + "','CurvaEfectiva_" + moneda + m2 + "'," + str(filtro) + ", 'Log',1) "
                "ORDER BY Plazo")

    return pd.io.sql.read_sql(sql, cn)



def proyectar_flujos_tabla(fecha, fecha_curva, devengo, hora, fecha_efectiva, fecha_venc, frecuencia, moneda,
                           hay_flujo_fecha_efectiva, mercado, ajuste_feriados, cn):
    """

    :param fecha: Fecha del proceso
    :param fecha_curva: Fecha de la curva a utilizar
    :param devengo:  El devengo acumulado desde el flujo anterior a la fecha del proceso
    :param hora: Hora del proceso
    :param fecha_efectiva: Fecha efectiva del contrato
    :param fecha_venc: Fecha vencimiento del contrato
    :param frecuencia: Frecuencia con la que se pagan los cupones
    :param moneda: La moneda de los flujos
    :param hay_flujo_fecha_efectiva: (1 => Flujo inicial en la fecha efectiva (XCCY))
    :param mercado: Tipo de mercado (Sólo con algunos países)
    :param ajuste_feriados: Arreglo de países para ajustar feriados
    :param cn: Conexión con permiso a base de datos
    :return: array  con la proyeccion de flujos en la tabla
    """

    # Evita casos de borde en que la fecha efectiva ya pasó
    if fecha_efectiva <= fecha:
        hay_flujo_fecha_efectiva = 0

    # Se guardan los plazos y factores de descuento para flujos en la moneda correspondiente
    arr_factor_descuento = remove_col(remove_col(curva_efectiva(moneda, fecha_curva, mercado, hora, -1, cn), 0), 2)

    if int(arr_factor_descuento.values[0][0]) == 0:  # Se elimina el plazo 0
        arr_factor_descuento = arr_factor_descuento.drop([arr_factor_descuento.index[0]])

    if int(arr_factor_descuento.values[0][0]) != 1:  # Si no hay plazo 1, se calcula
        valor_plazo1 = interpolacion_log_escalar(1, arr_factor_descuento.values)

        # Se dejan los factores de descuento agregando el plazo 1

        arr_factor_descuento = np.append(np.array([[1, valor_plazo1]]), arr_factor_descuento.values, axis=0)

    else:  # Si no, el arreglo ya tiene el plazo 1
        arr_factor_descuento = arr_factor_descuento.values


    paises = ajuste_feriados.split(",")

    # 'Recordar que Genera flujos crea los flujos desde la fecha de vencimiento hacia atrás usando la frecuencia como
    # paso, hasta inmediatamente después de la fechaInicioGeneraFlujos,
    # 'por lo que si no hay flujo en la fecha efectiva no se considerará esta fecha para los flujos, en cambio si hay
    # flujo en esta fecha, se considerará esta fecha en caso de ser posterior a la fecha de proceso
    if hay_flujo_fecha_efectiva == 0:
        fecha_inicio_genera_flujos = max(fecha, fecha_efectiva)
    else:
        fecha_inicio_genera_flujos = max(fecha, ultimo_habil_paises(add_days(fecha_efectiva, -1), paises, cn))

    flujos_f = genera_flujos(fecha_inicio_genera_flujos, fecha_efectiva, fecha_venc, 0, frecuencia, "ACT360", 1)

    # 'Recorro todos los flujos
    for i in range(len(flujos_f)):

        # 'Hay que ajustar el devengo y las fechas de tasas para cuando el cupón se fija con anticipación. Es esos casos
        # ', el primer cupon no es necesario proyectarlo y los que vienen se usa la curva con los fix corridos
        # 'Quizas basta con incluir el parametro siFijacionCupunAnticipadamente, que sería 1 para las libor y
        # 'cero para las del día.

        fecha_aux = max(delta_frecuencia(flujos_f[i][0], frecuencia, -1), fecha_efectiva)
        fecha_aux = add_days(fecha_aux, -1)
        fecha_tasa_inicial = siguiente_habil_paises(fecha_aux, paises, cn)  # Ajuste día hábil siguiente

        fecha_aux = max(flujos_f[i][0], fecha_efectiva)
        fecha_aux = add_days(fecha_aux, -1)
        fecha_tasa_final = siguiente_habil_paises(fecha_aux, paises, cn)  # Ajuste día hábil siguiente

        if fecha_tasa_final == False:
            print("ERROR")
            print(paises)
            print(fecha_aux)

        flujos_f[i][2] = fecha_tasa_final  # Ajuste día hábil siguiente para la fechaPago

        plazo_ini = (fecha_tasa_inicial - fecha_curva).days
        plazo_fin = (fecha_tasa_final - fecha_curva).days
        fd_ini = interpolacion_log_escalar(plazo_ini, arr_factor_descuento)

        fd_fin = interpolacion_log_escalar(plazo_fin, arr_factor_descuento)

        if i - hay_flujo_fecha_efectiva == 0:
            fd_ini = devengo
            flujos_f[i][6] = (devengo-1) * 100
        else:
            flujos_f[i][6] = 0
        flujos_f[i][4] = ((fd_ini/fd_fin)-1)*100
        flujos_f[i][1] = flujos_f[i][3] + flujos_f[i][4]

        if plazo_ini <= 0:
            fd_ini_DV01 = fd_ini
        else:
            tasa_eq_comp_act_360_ini = (((1/fd_ini)**(360/plazo_ini))-1)*100
            tasa_eq_comp_act_360_ini_DV01 = tasa_eq_comp_act_360_ini + 0.01
            fd_ini_DV01 = (tasa_eq_comp_act_360_ini_DV01 / 100 + 1)**(-plazo_ini/360)

        tasa_eq_comp_act_360_fin = (((1/fd_fin)**(360/plazo_fin))-1)*100
        tasa_eq_comp_act_360_fin_DV01 = tasa_eq_comp_act_360_fin + 0.01
        fd_fin_DV01 = (tasa_eq_comp_act_360_fin_DV01 / 100 + 1)**(-plazo_fin/360)

        flujos_f[i][5] = ((fd_ini_DV01/fd_fin_DV01)-(fd_ini/fd_fin)) * 100

    if hay_flujo_fecha_efectiva == 1:
        flujos_f[0][4] = 100
        flujos_f[0][4] = 0
        flujos_f[0][5] = 0

    return flujos_f

def plazo360_a_plazo(plazo360, fecha):
    dias = int(plazo360) % 30
    meses = int((plazo360-dias)/30 % 12)
    anhos = int((plazo360-dias-meses*30) / 360)
    return (add_days(add_months(add_years(fecha, anhos), meses), dias) - fecha).days

def get_tabla_desarrollo_fecha_emision_EX(fecha, nemo, cn):
    fecha = fecha_str(fecha)
    sql = ("SELECT T.Cupon, T.FechaCupon, T.FechaCupon, T.Interes, T.Amortizacion, 0 as Saldo, T.Flujo "
           "FROM TdTablasdeDesarrolloExt T INNER JOIN (SELECT Min(Fecha) as Fecha, Nemotecnico FROM ("
           "SELECT MAX(Fecha) AS Fecha, Nemotecnico FROM dbalgebra.dbo.TdTablasdeDesarrolloExt "
           "WHERE Nemotecnico = '" + nemo + "' AND Fecha <= '" + fecha + "' GROUP BY Nemotecnico "
           "UNION "
           "SELECT MIN(Fecha) AS Fecha, Nemotecnico "
           "FROM dbalgebra.dbo.TdTablasdeDesarrolloExt "
           "WHERE Nemotecnico = '" + nemo + "' AND Fecha > '" + fecha + "' GROUP BY Nemotecnico) A "
           "GROUP BY Nemotecnico) FN ON T.Fecha = FN.Fecha AND T.Nemotecnico = FN.Nemotecnico "
           "ORDER BY T.Cupon")

    arr_aux = pd.io.sql.read_sql(sql, cn).values

    for i in range(len(arr_aux)-1, -1, -1):
        arr_aux[i][5] = arr_aux[i+1][5] + arr_aux[i+1][4]
    return arr_aux


def get_tabla_desarrollo_fecha_emision(fecha, nemo, familia, cn):
    fecha = fecha_str(fecha)
    sql = ("SELECT TOP 1 FechaEmision, TablaDesarrollo "
           "FROM (SELECT Fecha, FechaEmision, TablaDesarrollo, 1 AS Prioridad "
            "FROM dbAlgebra.dbo.TdNemoRF WHERE Nemotecnico = '" + nemo + "' AND Fecha <= " + fecha + ""
            "UNION ALL "
            "SELECT Fecha, FechaEmision, TablaDesarrollo, 2 AS Prioridad "
            "FROM dbAlgebra.dbo.TdNemoRF WHERE Nemotecnico = '" + nemo + "' AND Fecha > " + fecha + ""
            ") A "
           "ORDER BY Prioridad, Fecha DESC")

    arr = pd.io.sql.read_sql(sql, cn)
    fecha_emision = arr.FechaEmision.iloc[0]
    tabla = arr.TablaDesarrollo.iloc[0]

    res = []
    res.append([0, fecha_emision, 0, 0, 100, 0])
    filas = tabla.split('|')
    for fila in filas:
        res.append(fila.split("#"))

    return res


def proyectar_flujo(fecha, hora, fecha_fixing, fecha_pago, mercado, moneda, flujo, moneda_base, cn):
    plazo_descuento = (fecha_pago - fecha).days

    fecha_fwd = add_days(fecha, (fecha_fixing - fecha).days)

    tipo_cambio_fwd = tipo_cambio(moneda, moneda_base, fecha_fwd, hora, cn)
    tipo_cambio_spot = tipo_cambio(moneda, moneda_base, fecha, hora, cn)
    factor_desc_mon_base = factor_descuento_monedas(moneda_base, mercado, fecha, hora, plazo_descuento, cn)

    return flujo / (tipo_cambio_spot/tipo_cambio_fwd * factor_desc_mon_base)


def factor_descuento_monedas(moneda, mercado, fecha,  hora, plazo, cn):
    if plazo == 0:
        return 1
    else:
        arr_factor_descuento = remove_col(remove_col(curva_efectiva(moneda, fecha, mercado, hora, -1, cn), 0), 2).values
        return interpolacion_log_escalar(plazo, arr_factor_descuento)



def fecha_hora_valores(fechaActual, cn):
    """
    Retorna la fecha en que se deben obtener valores en base de datos
    """
    
    sql = """SELECT Curva, FechaMax, C.Hora, C.Moneda
     FROM dbDerivados.dbo.TdCurvasDerivados A, dbDerivados.dbo.TdParidadMonedasCurvasDescuento B, 
    (SELECT MAX(Fecha) AS FechaMax, Hora, Moneda
    FROM dbDerivados.dbo.TdCurvasDerivados A, dbDerivados.dbo.TdParidadMonedasCurvasDescuento B
    WHERE A.Tipo = B.Tipo AND Fecha <= @Fecha GROUP BY Hora, Moneda) C
    WHERE A.Tipo = B.Tipo AND A.Fecha = C.FechaMax AND A.Hora = C.Hora AND B.Moneda = C.Moneda
    ORDER BY Fecha DESC, Hora DESC"""
    
    sql = sql.replace("@Fecha", fecha_str(fechaActual))
    
    datos = pd.io.sql.read_sql(sql, cn)
    return (datos.FechaMax.iloc[0].to_pydatetime().date(), datos.Hora.iloc[0])