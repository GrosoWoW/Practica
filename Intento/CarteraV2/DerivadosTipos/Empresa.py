# -*- coding: utf-8 -*-
"""Archivo para la clase Empresa.
"""
from Derivados.DerivadosFWD import *
from Derivados.DerivadosIBR import *
from Derivados.DerivadosSCC import *
from Derivados.DerivadosSUC import *
from Derivados.DerivadosSMT import *
from Derivados.DerivadosXCCY import *

from UtilesDerivados import fecha_hora_valores

class Empresa:

    def __init__(self, fecha, df, cn, filename = 'placeholder'):
        """Constructor de la clase Empresa
        :param df: pandas.dataframe con la informacion de los instrumentos
        :param cn: conexión a base de datos
        """

        # Diccionario para guardar los derivados
        derivados = {"FWD": [], "SCC": [], "SUC": [], "XCCY": []}

        if "Tipo" not in df.columns:
            send_msg("ERROR: No viene la columna 'Tipo'", filename)

        # Por cada tipo de derivado
        contar = 0
        for tipo in derivados:
            # Obtenemos la informacion de cada derivado por separado en el diccionario
            df_tipo = df.loc[df['Tipo'] == tipo]

            contar += len(df_tipo)
                
            derivados[tipo] = df_tipo

        # Habían derivados que no se tomaron en cuenta
        if len(df) != contar:
            send_msg("ERROR: Existe un derivado con Tipo no soportado", filename)


        self.derivados_dic = derivados
        self.derivados = {"FWD": [],"SCC": [], "SUC": [],"XCCY": []}
        self.fecha = fecha

        (fechaValores, hora) = fecha_hora_valores(fecha, cn)

        print("Valorizando con valores de",fechaValores)
        print("Valorizando a la hora", hora)
        

        self.fechaValores = fechaValores

        if fecha != fechaValores:
            self.estado_valorizacion = "Curvas de otra fecha"
        
        else:
            if hora != '1700':
                self.estado_valorizacion = "Preliminar"
            else:
                self.estado_valorizacion = "Definitiva"

        self.hora = hora
        self.cn = cn
        self.filename = filename
        self.flujos_valorizados = None
        self.flujos_nosensibles = None
        self.flujos_derivados = None

    def crear_derivados(self):
        """
        Recorre el DataFrame recibido y genera objetos para valorizar cada derivado
        :return:
        """
        fecha = self.fecha
        hora = self.hora
        cn = self.cn
        fechaValores = self.fechaValores
        filename = self.filename

        dic = self.derivados_dic
        
        for i in range(len(dic["FWD"])):
            info_cartera = pd.DataFrame(dic["FWD"].iloc[i]).transpose().reset_index(drop=True)
            self.derivados["FWD"].append(DerivadosFWD(fecha, hora, info_cartera, cn, fechaValores, filename))

        for i in range(len(dic["SCC"])):
            info_cartera = pd.DataFrame(dic["SCC"].iloc[i]).transpose().reset_index(drop=True)
            self.derivados["SCC"].append(DerivadosSCC(fecha, hora, info_cartera, cn, fechaValores, filename))

        for i in range(len(dic["SUC"])):
            info_cartera = pd.DataFrame(dic["SUC"].iloc[i]).transpose().reset_index(drop=True)
            self.derivados["SUC"].append(DerivadosSUC(fecha, hora, info_cartera, cn, fechaValores, filename))

        for i in range(len(dic["XCCY"])):
            info_cartera = pd.DataFrame(dic["XCCY"].iloc[i]).transpose().reset_index(drop=True)
            self.derivados["XCCY"].append(DerivadosXCCY(fecha, hora, info_cartera, cn, fechaValores, filename))
        

    def genera_flujos(self):
        """
        Llama al método genera_flujos para cada derivado que posee el objeto
        :return: None
        """
        derivados = self.derivados
        for tipo in derivados:
            for derivado in derivados[tipo]:
                derivado.genera_flujos()

    def valoriza_flujos(self):
        """
        Llama al método valoriza_flujos para cada derivado que posee el objeto
        :return:
        """
        derivados = self.derivados
        for tipo in derivados:
            for derivado in derivados[tipo]:
                derivado.valoriza_flujos()

    def agrega_cambio_spot(self):
        fechas_tipo_cambio_spot = list()

        flujos_valorizados = self.get_flujos_valorizados(forzar=True)

        for i in range(len(flujos_valorizados)):
            plazo_pago = (flujos_valorizados.FechaPago.iloc[i] - self.fecha).days
            plazo_flujo = (flujos_valorizados.FechaFlujo.iloc[i] - self.fecha).days
            plazo_fixing = (flujos_valorizados.FechaFixing.iloc[i] - self.fecha).days

            if plazo_flujo > 0:
                plazo_flujo = 0

            if plazo_pago > 0:
                plazo_pago = 0

            if plazo_fixing > 0:
                plazo_fixing = 0

            fechas_tipo_cambio_spot.append(fecha_str(add_days(self.fecha, plazo_fixing)))
            fechas_tipo_cambio_spot.append(fecha_str(add_days(self.fecha, plazo_pago)))
            fechas_tipo_cambio_spot.append(fecha_str(add_days(self.fecha, plazo_flujo)))
            fechas_tipo_cambio_spot = list(set(fechas_tipo_cambio_spot))

        fechas_tipo_cambio_spot = str(fechas_tipo_cambio_spot)[1:-1].replace('"', "")

        camino_monedas = ("SELECT * FROM dbDerivados.dbo.FnCaminoMonedas()")


        sql_monedas_cierre = ("SELECT M.Fecha, M.FechaDato, M.MonedaActiva, M.MonedaPasiva, M.Valor, "
                              "'Spot' as SpotObservado FROM dbDerivados.dbo.VwMonedasDia M "
                              "WHERE (M.Plazo360 = 0) AND (M.Hora = '" + self.hora + "') AND (M.Tipo = 'TipoCambio') "
                                "AND (M.Fecha in (" + fechas_tipo_cambio_spot + ")) AND (M.Campo = 'PX_LAST')")



        sql_monedas_observadas = ("SELECT Fecha, FechaDato, MonedaActiva, MonedaPasiva, Valor "
                                  "FROM dbDerivados.dbo.VwMonedasObservadas "
                                  "WHERE Fecha in (" + fechas_tipo_cambio_spot + ")")

        sql_monedas_observadas_parchadas = ("SELECT DISTINCT Coalesce(O.Fecha, S.Fecha) as Fecha, "
                                            "Coalesce(O.FechaDato, S.FechaDato) as FechaDato, "
                                            "Coalesce(O.MonedaActiva, S.MonedaActiva) as MonedaActiva, "
                                            "Coalesce(O.MonedaPasiva, S.MonedaPasiva) as MonedaPasiva, "
                                            "Coalesce(O.Valor, S.Valor) as Valor, 'Observado' as SpotObservado "
                                            "FROM (" + sql_monedas_cierre + ") AS S "
                                            "FULL OUTER JOIN (" + sql_monedas_observadas + ") AS O "
                                            "ON S.Fecha = O.Fecha AND S.MonedaActiva = O.MonedaActiva "
                                            "AND S.MonedaPasiva = O.MonedaPasiva")




        sql_monedas = sql_monedas_observadas_parchadas + " UNION " + sql_monedas_cierre

        cast_monedas = {'UF': 'CLF', 'CLN': 'COP'}
        valores_monedas = pd.io.sql.read_sql(sql_monedas, self.cn)
        camino_monedas = pd.io.sql.read_sql(camino_monedas, self.cn)

        # Pasando el dataframe a un diccionario

        flujos_valorizados_dict = flujos_valorizados.to_dict()


        for i in range(len(flujos_valorizados)):
            
            d1 = flujos_valorizados_dict["FactorDescMonBase"][i]
            d2 = flujos_valorizados_dict["FactorDescMonFlujoFix"][i]
            d3 = flujos_valorizados_dict["FactorDescMonBaseFix"][i]

            flujo = flujos_valorizados_dict["Flujo"][i]

            moneda = cast_monedas.get(flujos_valorizados_dict["Moneda"][i], flujos_valorizados_dict["Moneda"][i])

            moneda_base = cast_monedas.get(flujos_valorizados_dict["MonedaBase"][i],
                                           flujos_valorizados_dict["MonedaBase"][i])

            valores_monedas_t = valores_monedas.loc[valores_monedas['Fecha'] == pd.Timestamp(self.fecha)]
            valores_monedas_t = valores_monedas_t.loc[valores_monedas_t['SpotObservado'] == 'Spot']

            tipo_cambio_t = valor_moneda(moneda, moneda_base, camino_monedas, valores_monedas_t)

            plazo_fixing = (flujos_valorizados_dict["FechaFixing"][i] - self.fecha).days

            if plazo_fixing > 0:
                plazo_fixing = 0

            valores_monedas_fix = valores_monedas.loc[valores_monedas['Fecha'] == pd.Timestamp(add_days(self.fecha,
                                                                                                        plazo_fixing))]

            if plazo_fixing >= 0:
                valores_monedas_fix = valores_monedas_fix.loc[valores_monedas_fix['SpotObservado'] == 'Spot']
            else:
                valores_monedas_fix = valores_monedas_fix.loc[valores_monedas_fix['SpotObservado'] == 'Observado']

            tipo_cambio_fix = valor_moneda(moneda, moneda_base, camino_monedas, valores_monedas_fix)

            flujos_valorizados_dict["TipoCambioSpot"][i] = tipo_cambio_t
            flujos_valorizados_dict["TipoCambioSpotFix"][i] = tipo_cambio_fix

            valor_presente_mon_base = d1 * flujo * (d2 / d3) * tipo_cambio_t

            flujos_valorizados_dict["ValorPresenteMonBase"][i] = d1 * flujo * (d2 / d3) * tipo_cambio_t
            flujos_valorizados_dict["TipoCambioFwd"][i] = (d2 / d3) * tipo_cambio_t

            # Agregando valores CLP y USD

            cambio_usd_base = valor_moneda(moneda_base, "USD", camino_monedas, valores_monedas)
            cambio_clp_base = valor_moneda(moneda_base, "CLP", camino_monedas, valores_monedas)

            flujos_valorizados_dict["TipoCambioCLPBase"][i] = cambio_clp_base
            flujos_valorizados_dict["TipoCambioUSDBase"][i] = cambio_usd_base

            flujos_valorizados_dict["ValorPresenteUSD"][i] = valor_presente_mon_base * cambio_usd_base
            flujos_valorizados_dict["ValorPresenteCLP"][i] = valor_presente_mon_base * cambio_clp_base

        self.flujos_valorizados = pd.DataFrame.from_dict(flujos_valorizados_dict)


    def valoriza_flujos_DV01(self):
        """
        Llama al método valoriza_flujos_DV01 para cada derivado que posee el objeto
        :return:
        """
        derivados = self.derivados
        for tipo in derivados:
            for derivado in derivados[tipo]:
                derivado.valoriza_flujos_DV01()


    def get_flujos_valorizados(self, forzar=False):
        """
        Entrega los flujos valorizados de todos los derivados que posee el objeto.
        Extrae todos los flujos_valorizados de los derivados si es la primera vez que se llama al método.
        Opcionalmente, se puede forzar la extracción de la información para cada derivado
        :param forzar: bool para indicar si se debe forzar la extracción de los flujos valorizados de cada derivado
        :return: pandas.DataFrame con todos los flujos valorizados
        """

        if self.flujos_valorizados is None or forzar:

            self.flujos_valorizados = pd.DataFrame()

            for tipo in self.derivados:
                for derivado in self.derivados[tipo]:
                    self.flujos_valorizados = self.flujos_valorizados.append(derivado.get_flujos_valorizados(),
                                                                             ignore_index=True)

        return self.flujos_valorizados

    def get_flujos_nosensibles(self, forzar=True):
        """
        Entrega los flujos no sensibles de todos los derivados que posee el objeto.
        Extrae todos los flujos_nosensibles de los derivados si es la primera vez que se llama al método.
        Opcionalmente, se puede forzar la extracción de la información para cada derivado
        :param forzar: bool para indicar si se debe forzar la extracción de la información
        :return: pandas.DataFrame con todos los flujos no sensibles
        """

        if self.flujos_nosensibles is None or forzar:
            self.flujos_nosensibles = pd.DataFrame()
            for tipo in self.derivados:
                for derivado in self.derivados[tipo]:
                    self.flujos_nosensibles = self.flujos_nosensibles.append(derivado.get_flujos_nosensibles(),
                                                                             ignore_index=True)
        return self.flujos_nosensibles

    def get_flujos_derivados(self, forzar=True):
        """
        Entrega los flujos de todos los derivados que posee el objeto.
        Extrae todos los flujos_derivados de los derivados si es la primera vez que se llama al método.
        Opcionalmente, se puede forzar la extracción de la información para cada derivado
        :param forzar: bool para indicar si se debe forzar la extracción de la información
        :return: pandas.DataFrame con todos los flujos
        :param forzar:
        :return:
        """
        if self.flujos_derivados is None or forzar:
            self.flujos_derivados = pd.DataFrame()
            for tipo in self.derivados:
                for derivado in self.derivados[tipo]:
                    self.flujos_derivados = self.flujos_derivados.append(derivado.get_flujos_derivado(),
                                                                         ignore_index=True)
        return self.flujos_derivados


    def procesar_todo(self):
        """
        Llama a todas las funciones para el proceso de valorización de derivados. Sirve como azucar sintáctico.
        :return: None
        """

        self.crear_derivados()

        self.flujos_valorizados = pd.DataFrame()

        derivados = self.derivados
        for tipo in derivados:
            for derivado in derivados[tipo]:
                derivado.genera_flujos()
                derivado.valoriza_flujos()

        self.agrega_cambio_spot()


    def get_error_status(self):
        derivados = self.derivados
        res = ""

        for tipo in derivados:
            for derivado in derivados[tipo]:

                status = derivado.get_status()

                if status[:5] == "ERROR":
                    res = res + status + "\n"

        return res[:-1]


