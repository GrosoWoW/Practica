# -*- coding: utf-8 -*-
"""
Archivo principal para el cálculo de derivados
"""
from Derivados.Empresa import *
from UtilIndicadores import send_msg, fecha_str
from UtilesDerivados import ultimo_habil_pais

import pandas as pd


def flujo_completo_derivados(fecha, servidor_app, instrumentos, empresas, tipo_valorizacion, cnn, reproceso = False):
    """
    Realiza el flujo completo para la valorizacion de derivados
    Si tipo es 1, se asume que el arreglo contiene id's de empresas
    Si tipo es 2, se asume que el arreglo contiene id's de instrumentos
    :param fecha: datetime.date con la fecha en la que se procesa
    :param servidorApp: String con nombre del servidor con el cual trabajar
    :param arr: array de datos según tipo
    :param cn: pyodbc.connect conexión a base de datos
    :param tipo: int indicando el tipo para el calculo (1 empresas, 2 instrumentos)
    :return: None
    """
    hora_curva = '1500'

    if reproceso:
        copiar_fondos_a_cartera(fecha, instrumentos, empresas, cnn)

        empresa = crear_objeto(fecha, hora_curva, instrumentos, empresas, cnn)
        empresa.genera_flujos()
        empresa.valoriza_flujos()
        empresa.agregar_cambio_spot()
        empresa.valoriza_flujos_DV01()

    elif tipo_valorizacion == "PRELIMINAR":
        limpia_tablas(servidor_app, cnn)
        duplica_fondos_habil_anterior(fecha, servidor_app, instrumentos, empresas, cnn)
        copiar_fondos_a_cartera(fecha, instrumentos, empresas, cnn)

        empresa = crear_objeto(fecha, hora_curva, instrumentos, empresas, cnn)
        empresa.genera_flujos()
        empresa.valoriza_flujos()
        empresa.agregar_cambio_spot()
        empresa.valoriza_flujos_DV01()

    elif tipo_valorizacion == "DEFINIIVA":
        pass




def crear_objeto(fecha, hora, instrumentos, empresas, cn):
    """
    Crea un objeto de empresa para valorizar derivados con las condiciones
    :param fecha: datetime.date
    :param hora: string
    :param instrumentos: arr
    :param empresas: arr
    :param cn: pyodbc.connect
    :return: Empresa
    """

    str_condicion(empresas, "Administradora")
    str_condicion(instrumentos, "ID")

    condicion = "WHERE Fecha = " + fecha_str(fecha) + " AND " + str_condicion(empresas, "Administradora") + \
                " AND " + str_condicion(instrumentos, "ID")

    sql = ("SELECT * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] " + condicion)
    info = pd.io.sql.read_sql(sql, cn)

    return Empresa(fecha, hora, info, cn)




def copiar_fondos_a_cartera(fecha, instrumentos, empresas, cnn):
    """
    Copia los elementos desde TdDerivadosFondo a TdCarteraDerivados según la fecha, instrumentos y empresa
    :param fecha: datetime.date
    :param instrumentos: arr
    :param empresas: arr
    :param cnn: pyodbc.connect
    :return:
    """

    borrar_admin = str_condicion(empresas, "Administradora")
    borrar_instr = str_condicion(instrumentos, "ID")

    # Primero borramos los elementos

    sql = ("DELETE FROM dbDerivados.dbo.TdCarteraDerivados_V2 "
           "WHERE Fecha = " + fecha_str(fecha) + " AND " + borrar_admin + " AND " + borrar_instr)


    # Ahora los traemos de TdDerivadosFondo

    inserta_empresa = str_condicion(empresas, "idEmpresa")
    inserta_instrumeto = str_condicion(instrumentos, "idInstrumento")

    sql = ("INSERT INTO dbDerivados.dbo.TdCarteraDerivados_V2 "
           "([Fecha] ,[Administradora], [Fondo], [Contraparte], [Tipo], [ID], "
           "[FechaTransaccion], [FechaFixing], [FechaEfectiva], [FechaVenc], "
           "[AjusteFeriados], [Mercado], [Nemotecnico], [Referencia], [NocionalActivo], "
           "[MonedaActivo], [FrecuenciaActivo], [TipoTasaActivo], [TasaActivo], "
           "[SpreadActivo], [NocionalPasivo], [MonedaPasivo], [FrecuenciaPasivo], "
           "[TipoTasaPasivo], [TasaPasivo], [SpreadPasivo], [MonedaBase]) "
           ""
           "SELECT Fecha, idEmpresa AS Administradora, Fondo, Contraparte, Tipo, "
           "idInstrumento, FechaTransaccion, FechaFixing, FechaEfectiva, FechaVenc, "
           "AjusteFeriados, Mercado, Nemotecnico, Referencia, NocionalActivo, "
           "MonedaActivo, FrecuenciaActivo, TipoTasaActivo, TasaActivo, "
           "SpreadActivo, NocionalPasivo, MonedaPasivo, FrecuenciaPasivo, "
           "TipoTasaPasivo, TasaPasivo, SpreadPasivo, MonedaBase "
           "FROM dbSectorReal.dbo.TdDerivadosFondo "
           "WHERE Fecha = " + fecha_str(fecha) + " AND " + inserta_empresa + " AND " + inserta_instrumeto)




def duplica_fondos_habil_anterior(fecha, servidorApp, instrumentos, empresas, cn):
    """
    Duplica en sector real del servidor las filas con instrumento en el arreglo de instrumentos
    :param fecha: datetime.date del proceso
    :param servidorApp:  String nombre del servidor
    :param instrumentos: array de id's de instrumentos para duplicar
    :param cn: pyodbc.conection conexión a base de datos
    :return:  None
    """

    instrumentos_excluidos = ['939', '929', '930', '931', '932', '933', '934', '857', '864', '883', '884', '885', '886',
                              '887', '891', '894', '896', '899', '919', '924', '927', '935', '936', '937', '938', '940',
                              '941', '942', '943', '944', '945', '946', '947', '950', '982', '989', '1025', '1026',
                              '1027', '1028', '993', '994', '995', '997', '998', '1000', '1001', '1063', '1047', '1108',
                              '1109', '1110', '1111', '1112', '1113', '1115', '1138', '1216']

    instrumentos_excluidos = str(instrumentos_excluidos)[1:-1]

    instrumentos = str_condicion(instrumentos, "idInstrumento")

    empresas = str_condicion(empresas, "idEmpresa")

    sql_servidor = ("INSERT INTO [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo "
            "SELECT idInstrumento, idEmpresa, Visible, '" + fecha_str(fecha) + "' "
            "AS Fecha, Fondo, Nombre, Contraparte, Tipo, FechaTransaccion, FechaFixing, FechaEfectiva, FechaVenc, "
            "AjusteFeriados, Mercado, Nemotecnico, Referencia, NocionalActivo, MonedaActivo, FrecuenciaActivo, "
            "TipoTasaActivo, TasaActivo , SpreadActivo, NocionalPasivo, MonedaPasivo, FrecuenciaPasivo, TipotasaPasivo, "
            "TasaPasivo, SpreadPasivo, MonedaBase "
            "FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo "
            "WHERE " +  instrumentos + " OR " + empresas + " "
            "AND Fecha=" + fecha_str(ultimo_habil_pais(fecha, 'CL', cn)) + " AND FechaVenc > " + fecha_str(fecha) + " "
            "AND idInstrumento NOT IN (SELECT idInstrumento FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo "
            "WHERE Fecha=" + fecha_str(fecha) + ") AND idInstrumento NOT IN (" + instrumentos_excluidos + ")")


    sql = ("INSERT INTO dbSectorReal.dbo.TdDerivadosFondo SELECT idInstrumento, idEmpresa, Visible, " + fecha_str(fecha) + " "
                 "AS Fecha, Fondo, Nombre, Contraparte, Tipo, FechaTransaccion, FechaFixing, FechaEfectiva, FechaVenc, "
                 "AjusteFeriados, Mercado, Nemotecnico, Referencia, NocionalActivo, MonedaActivo, FrecuenciaActivo, "
                 "TipoTasaActivo, TasaActivo , SpreadActivo, NocionalPasivo, MonedaPasivo, FrecuenciaPasivo, TipotasaPasivo, "
                 "TasaPasivo, SpreadPasivo, MonedaBase "
                 "FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo "
                 "WHERE " +  instrumentos + " OR " + empresas + " "
                 "AND Fecha=" + fecha_str(ultimo_habil_pais(fecha, 'CL', cn)) + " "
                 "AND FechaVenc > " + fecha_str(fecha) + " "
                 "AND idInstrumento NOT IN (SELECT idInstrumento "
                 "FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo "
                 "WHERE Fecha=" + fecha_str(fecha) + ") "
                 "AND idInstrumento NOT IN (" + instrumentos_excluidos + ")")

    cursor = cn.cursor()
    cursor.execute(sql)

    cursor.execute(sql_servidor)
    send_msg("")  # todo


def limpia_tablas(servidorApp, cn):
    """
    Se eliminan registros de instrumentos marcados como no visibles tanto de servidor como local
    :param servidorApp: String nombre del servidor al cual eliminar, además del local
    :param cn: pyodbc.connect conexión a base de datos
    :return: None
    """
    # Se crea un cursor para la conexión
    # así poder contar cantidad de elementos eliminados
    cursor = cn.cursor()

    # Limpia WEB
    sql = ("DELETE FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo WHERE Visible=0")
    cursor.execute(sql)
    send_msg(("ValorizaDerivadosSectorReal: limpia_tablas: Se elimina de "
              "[" + servidorApp + "][dbSectorReal][TdDerivadosFondo] " + str(cursor.rowcount) + " registros"))

    sql = ("DELETE FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondoValorizacion WHERE idInstrumento NOT IN "
                                           "(SELECT DISTINCT(idInstrumento) FROM "
                                           "[" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFondo "
                                                               "WHERE Visible=1)")
    cursor.execute(sql)
    send_msg(("ValorizaDerivadosSectorReal: limpia_tablas: Se elimina de "
              "[" + servidorApp + "][dbSectorReal][TdDerivadosFondoValorizacion] "
                                  "" + str(cursor.rowcount) + " registros"))

    sql = ("DELETE FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFlujos WHERE Visible=0")
    cursor.execute(sql)

    sql = (
            "DELETE FROM [" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFlujosValorizacion WHERE idInstrumento NOT IN "
                                            "(SELECT DISTINCT(idInstrumento) FROM "
                                            "[" + servidorApp + "].dbSectorReal.dbo.TdDerivadosFlujos "
                                                                "WHERE Visible=1)")
    cursor.execute(sql)

    # Limpia datos

    sql = ("DELETE FROM dbSectorReal.dbo.TdDerivadosFondo WHERE Visible=0")
    cursor.execute(sql)

    sql = ("DELETE FROM dbSectorReal.dbo.TdDerivadosFondoValorizacion "
           "WHERE idInstrumento NOT IN "
           "(SELECT DISTINCT(idInstrumento) FROM dbSectorReal.dbo.TdDerivadosFondo WHERE Visible=1 )")
    cursor.execute(sql)

    sql = ("DELETE FROM dbSectorReal.dbo.TdDerivadosFlujos WHERE Visible=0")
    cursor.execute(sql)

    sql = ("DELETE FROM dbSectorReal.dbo.TdDerivadosFlujosValorizacion "
           "WHERE idInstrumento NOT IN "
           "(SELECT DISTINCT(idInstrumento) FROM dbSectorReal.dbo.TdDerivadosFlujos WHERE Visible=1 )")
    cursor.execute(sql)



def str_condicion(arr, nombre):
    """
    Retorna condición sql de la forma "nombre in arr". Si el arreglo es vacío, 1=1
    :param arr: array de elementos a consultar
    :param nombre: string nombre de la columna
    :return: string con la condición
    """
    if len(arr) == 0:
        return "1=1"
    return nombre + " IN (" + str(arr)[1:-1] + ")"