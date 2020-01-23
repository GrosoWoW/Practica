# -*- coding: utf-8 -*-
"""Clase para el cálculo de derivados
Este módulo contiene una clase abstracta
"""
import sys
sys.path.append("..")
import numpy as np


from abc import ABC, abstractmethod
import pandas as pd
from Derivados.LibreriasUtiles.UtilesDerivados import genera_flujos, ultimo_habil_pais
from Derivados.LibreriasUtiles.UtilesValorizacion import parsear_curva, valor_moneda
from Derivados.LibreriasUtiles.Util import fecha_str, add_months, add_days, send_msg
from Derivados.LibreriasUtiles.Matematica import interpolacion_log_escalar
import math
import datetime


class DerivadosAbstracto(ABC):
    """Clase abstracta para el cálculo de derivados
    """

    def __init__(self, fecha, hora, info_cartera, cn, fechaValores=None, filename="placeholder"):
        """
        Constructor para una clase derivados
        :param fecha: datetime.date con la fecha para la cual se está valorizando
        :param hora: string con la hora en la cual se está valorizando (EJ: '1500', '1700')
        :param info_cartera: pandas.DataFrame con la información en cartera de derivados
        :param cn: pyodbc.connect con permisos en base de datos
        :param filename: nombre del archivo para dejar los mensajes de error
        """

        if len(info_cartera) == 0:
            self.set_status("ERROR: Derivado sin información")
            send_msg("ERROR: Se intentó crear un derivado sin información", filename)
            return

        if len(info_cartera) > 1:
            self.set_status("ERROR: Derivado con más de una fila de información")
            self.set_status("ERROR: Se intentó crear un derivado con información de varios")
            return

        self.col_flujos_derivados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'Hora',
                                       'ActivoPasivo', 'FechaFixing', 'FechaTenorFixing', 'FechaFlujo', 'FechaPago',
                                       'Moneda', 'Flujo', 'Amortizacion', 'Interes', 'Sensibilidad', 'InteresDevengado',
                                    ]

        self.col_flujos_nosensibles = ['Fecha', 'Fondo', 'Tipo', 'ID', 'ActivoPasivo',
                                       'FechaFlujoNoSensible', 'Moneda', 'FlujoNoSensible']

        self.col_flujos_valorizados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'Hora',
                                       'Mercado', 'ActivoPasivo', 'FechaFixing', 'FechaTenorFixing', 'FechaFlujo',
                                       'FechaPago', 'Moneda', 'Flujo', 'Amortizacion', 'Interes', 'MonedaBase',
                                       'PlazoTipoCambioFwd', 'PlazoDescuento', 'TipoCambioSpot', 'TipoCambioFwd',
                                       'FactorDescMonBase', 'FactorDescMonFlujo', 'ValorPresenteMonBase',
                                       'ValorPresenteMonFlujo', 'TipoCambioSpotFix', 'FactorDescMonFlujoFix',
                                       'FactorDescMonBaseFix', 'ValorPresenteCLP', 'TipoCambioCLPBase',
                                       'ValorPresenteUSD', 'TipoCambioUSDBase', 'Sensibilidad', 'TipoValorizacion',
                                       ]

        self.col_flujos_DV01_valorizados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'Hora',
                                            'Mercado', 'ActivoPasivo', 'FechaFixing', 'FechaFlujo', 'FechaPago',
                                            'Moneda', 'Flujo', 'Amortizacion', 'Interes', 'MonedaBase',
                                            'PlazoTipoCambioFwd', 'PlazoDescuento', 'TipoCambioSpot', 'TipoCambioFwd',
                                            'FactorDescMonBase', 'FactorDescMonFlujo', 'ValorPresenteMonBase',
                                            'ValorPresenteMonFlujo', 'TipoCambioSpotFix', 'FactorDescMonFlujoFix',
                                            'FactorDescMonBaseFix', 'ValorPresenteCLP', 'TipoCambioCLPBase',
                                            'ValorPresenteUSD', 'TipoCambioUSDBase', 'TasaEqCompAct360', 'TasaDV01',
                                            'FactorDescMonFlujoFixDV01', 'TipoCambioFwdDV01',
                                            'ValorPresenteMonBaseDV01', 'ValorPresenteMonFlujoDV01', 'Dv01MonBase',
                                            'Dv01MonFlujo', 'Dv01CLP', 'Dv01USD', 'Duracion', 'SensibilidadTasa',
                                            ]

        self.flujos_DV01_valorizados = pd.DataFrame(columns=self.col_flujos_DV01_valorizados)
        self.flujos_valorizados = pd.DataFrame(columns=self.col_flujos_valorizados)
        self.flujos_derivados = pd.DataFrame(columns=self.col_flujos_derivados)
        self.flujos_nosensibles = pd.DataFrame(columns=self.col_flujos_nosensibles)
        self.cn = cn
        
        self.filename = filename
        
        
        if not ('MonedaBase' in info_cartera.columns and isinstance(info_cartera.MonedaBase[0],str)):
            info_cartera["MonedaBase"] = 'CLP'
        
        
        if  not ('Mercado' in info_cartera.columns and isinstance(info_cartera.Mercado[0],str)):
            info_cartera["Mercado"] = "Local"
            
        if  not ('AjustesFeriados' in info_cartera.columns and isinstance(info_cartera.Mercado[0],str)):
            info_cartera["AjusteFeriados"] = "CL"
        
        if  fecha>pd.to_datetime(datetime.datetime.strptime(info_cartera.FechaVenc[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date():
            send_msg("ERROR: Fecha vencimiento anterior a la fecha de valorizacion.",self.filename)
        
        
        
        self.info_cartera = info_cartera

        # Fecha en que se valoriza (puede ser feriado)
        self.fechaActual = fecha

        if fechaValores is None:
            # Fecha para obtener datos (se fuerza día hábil)
            # Se utiliza Chile por defecto (ubicación de LVA)
            self.fechaValores = ultimo_habil_pais(fecha, "CL", self.cn)
            if self.fechaActual != self.fechaValores:
                print("Valorizando en un día no hábil")
        else:
            self.fechaValores = fechaValores
            
        self.hora = hora
        self.msg = "INFO: Derivado inicializado"
        self.revisar_input()

    @abstractmethod
    def genera_flujos(self):
        """
        Genera los flujos del derivado para la valorización. Quedan en el atributo flujos_nosensibles y flujos_derivados
        :return: None
        """
        pass
    
    @abstractmethod
    def revisar_input(self):
        """
        Revisa los inputs para el proceso
        :return: None
        """
        pass

    def get_flujos_valorizados(self):
        """
        Retorna los flujos valorizados.
        Si no se ha llamado al método valoriza_flujos retorna un DataFrame vacío
        :return: pandas.DataFrame con la información de los flujos valorizados
        """
        return self.flujos_valorizados

    def get_flujos_nosensibles(self):
        """
        Retorna los flujos no sensibles.
        Si no se ha llamado al método genera_flujos retorna un DataFrame vacío
        :return: pandas.DataFrame con la información de los flujos no sensibles
        """
        return self.flujos_nosensibles

    def get_flujos_derivado(self):
        """
        Retorna los flujos del derivado.
        Si no0 se ha llamado al método genera_flujos retorna un DataFrame vacío
        :return: pandas.Dataframe con la información de los flujos
        """
        return self.flujos_derivados

    def get_flujos_DV01(self):
        """
        Retorna los flujos DV01 del derivado.
        Si no se ha llamado al método valoriza_flujos_DV01 retorna un DataFrame vacío
        :return: pandas.Dataframe con la información de los flujos
        """
        return self.flujos_DV01_valorizados

    def get_status(self):
        """
        Entrega un string con el estado del derivado.
        En caso de error, esto entrega detalles
        :return: String con mensaje de estado
        """
        return self.msg

    def set_status(self, msg):
        """
        Deja como estado el mensaje entregado al derivado.
        todo: En caso de que el mensaje anterior haya sido un error, no se cambia.
        :para msg: String con el mensaje que se desesa dejar
        :return: int: 1
        """
        if self.msg[:5] != "ERROR":
            self.msg = msg
        else:
            if msg[:5] == "ERROR":
                self.msg = "\n" + msg


    def procesar_todo(self):
        """
        Llama al proceso completo para la valorización de derivados. Sirve como azucar sintáctico
        :return: None
        """
        self.genera_flujos()
        self.valoriza_flujos()
        self.agrega_cambio_spot()
        self.valoriza_flujos_DV01()

    def valoriza_flujos(self):
        """
        Valoriza los flujos y los guarda en el atributo flujos_valorizados
        Si no se ha llamado al método genera_flujos puede lanzar error
        :return: None
        """

        col_tabla_aux = ['Fecha', 'Fondo', 'Tipo', 'ID', 'Hora', 'Mercado',
                         'ActivoPasivo', 'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo', 'Amortizacion',
                         'Interes', 'MonedaBase', 'Sensibilidad']

        tabla_aux = pd.DataFrame(columns=col_tabla_aux)

        for i in range(len(self.flujos_derivados)):
            dic = dict()
            dic["Fecha"] = self.flujos_derivados.Fecha.iloc[i]
            dic["Fondo"] = self.flujos_derivados.Fondo.iloc[i]
            dic["Tipo"] = self.flujos_derivados.Tipo.iloc[i]
            dic["ID"] = self.flujos_derivados.ID.iloc[i]
            dic["Hora"] = self.hora
            dic["Mercado"] = self.info_cartera.Mercado.iloc[0]
            dic["ActivoPasivo"] = self.flujos_derivados.ActivoPasivo.iloc[i]
            dic["FechaFixing"] = self.flujos_derivados.FechaFixing.iloc[i]
            dic["FechaFlujo"] = self.flujos_derivados.FechaFlujo.iloc[i]
            dic["FechaPago"] = self.flujos_derivados.FechaPago.iloc[i]
            dic["Moneda"] = self.flujos_derivados.Moneda.iloc[i]
            dic["Flujo"] = self.flujos_derivados.Flujo.iloc[i]
            dic["Amortizacion"] = self.flujos_derivados.Amortizacion.iloc[i]
            dic["Interes"] = self.flujos_derivados.Interes.iloc[i]
            
            dic["MonedaBase"] = self.info_cartera.MonedaBase.iloc[0] 
            
            dic["Sensibilidad"] = self.flujos_derivados.Sensibilidad.iloc[i]

            tabla_aux = tabla_aux.append(dic, ignore_index=True)

        tabla_aux = tabla_aux.reset_index()
        cast_monedas = {'UF': 'CLF', 'CLN': 'COP'}

        plazos_monedas = pd.DataFrame(columns=['Moneda', 'Fecha', 'Plazo'])

        for i in range(len(tabla_aux)):
            insert = dict()
            insert["Fecha"] = tabla_aux.Fecha.iloc[i]
            insert["Plazo"] = (tabla_aux.FechaPago.iloc[i] - tabla_aux.Fecha.iloc[i]).days
            insert["Moneda"] = cast_monedas.get(tabla_aux.Moneda.iloc[i], tabla_aux.Moneda.iloc[i])
            plazos_monedas = plazos_monedas.append(insert, ignore_index=True)
            insert["Moneda"] = cast_monedas.get(tabla_aux.MonedaBase.iloc[i], tabla_aux.MonedaBase.iloc[i])
            plazos_monedas = plazos_monedas.append(insert, ignore_index=True)

        # Nos quedamos con el maximo plazo para cada par Moneda,Fecha
        plazos_monedas = plazos_monedas.sort_values('Plazo', ascending=False).drop_duplicates(
            ['Moneda', 'Fecha']).reset_index()

        # mercado_curvas = pd.DataFrame([['Ambos', '--'],
        #                                ['Ambos', 'Local'],
        #                                ['--', '--'],
        #                                ['Local', 'Local']], columns=['Mercados', 'Mercado'])

        curvas_monedas =  {}
        monedas_str = ""
        for moneda in plazos_monedas.Moneda.drop_duplicates():
            curvas_monedas[moneda] = ""
            monedas_str += "'" + moneda + "',"
        monedas_str = monedas_str[0:-1]
        

        # Se obtienen las curvas
        curvas = ("SELECT Curva, FechaMax, C.Hora, C.Moneda "
                  "FROM dbDerivados.dbo.TdCurvasDerivados A, dbDerivados.dbo.TdParidadMonedasCurvasDescuento B, "
                  "(SELECT MAX(Fecha) AS FechaMax, Hora, Moneda "
                  "FROM dbDerivados.dbo.TdCurvasDerivados A, dbDerivados.dbo.TdParidadMonedasCurvasDescuento B "
                  "WHERE A.Tipo = B.Tipo AND Fecha <= " + fecha_str(self.fechaValores) + " AND Hora = '" + self.hora + "' "
                  "AND Moneda IN (" + monedas_str + ") GROUP BY Hora, Moneda) C "
                  "WHERE A.Tipo = B.Tipo AND A.Fecha = C.FechaMax AND A.Hora = C.Hora AND B.Moneda = C.Moneda")


        curvas = pd.io.sql.read_sql(curvas, self.cn)

        for i in range(len(curvas)):
            curva = curvas.Curva.iloc[i]
            curvas_monedas[curvas.Moneda[i]] = parsear_curva(curva, self.fechaActual)
            if curvas.FechaMax.iloc[i].to_pydatetime().date() < self.fechaValores:
                self.set_status("ERROR: valoriza_flujos: Curva para la moneda " + str(curvas.Moneda[i]) +
                                " no encontrada para la fecha " + str(self.fechaValores) + ". Se utilizó curva de " + str(curvas.FechaMax[i].date()))
                send_msg("ERROR: valoriza_flujos: Curva para la moneda " + str(curvas.Moneda[i]) +
                                " no encontrada para la fecha " + str(self.fechaValores) + ". Se utilizó curva de " + str(curvas.FechaMax[i].date()), self.filename)

        error = False
        for i in curvas_monedas:
            if curvas_monedas[i] == "":
                self.set_status("ERROR: valoriza_flujos: No se encontró curva para la moneda " + i +
                                " en la fecha " + str(self.fechaValores) + " y hora " + self.hora)
                send_msg("ERROR: valoriza_flujos: No se encontró curva para la moneda " + i +
                         " en la fecha " + str(self.fechaValores) + " y hora " + self.hora, self.filename)
                error = True
        if error:
            return

        col_flujos_valorizados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'Hora', 'Mercado',
                                  'ActivoPasivo', 'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo',
                                  'Amortizacion', 'Interes', 'MonedaBase', 'PlazoTipoCambioFwd', 'PlazoDescuento',
                                  'TipoCambioSpot', 'TipoCambioFwd', 'FactorDescMonBase', 'FactorDescMonFlujo',
                                  'ValorPresenteMonBase', 'ValorPresenteMonFlujo', 'TipoCambioSpotFix',
                                  'FactorDescMonFlujoFix', 'FactorDescMonBaseFix', 'ValorPresenteCLP',
                                  'TipoCambioCLPBase', 'ValorPresenteUSD', 'TipoCambioUSDBase', 'Sensibilidad',
                                  'TipoValorizacion']
        flujos_valorizados = pd.DataFrame(columns=col_flujos_valorizados)

        # Por cada flujo, valorizamos
        insert = dict()
        insert["Fecha"] = self.fechaActual
        insert["Tipo"] = self.info_cartera.Tipo.iloc[0]
        insert["Hora"] = self.hora
        for i in range(len(tabla_aux)):
            insert["Fondo"] = tabla_aux.Fondo.iloc[i]
            insert["ID"] = tabla_aux.ID.iloc[i]
            insert["Mercado"] = tabla_aux.Mercado.iloc[i]
            insert["ActivoPasivo"] = tabla_aux.ActivoPasivo.iloc[i]

            fecha_fixing = pd.to_datetime(tabla_aux.FechaFixing.iloc[i]).date()
            insert["FechaFixing"] = fecha_fixing

            fecha_flujo = pd.to_datetime(tabla_aux.FechaFlujo.iloc[i]).date()
            insert["FechaFlujo"] = fecha_flujo

            fecha_pago = pd.to_datetime(tabla_aux.FechaPago.iloc[i]).date()
            insert["FechaPago"] = fecha_pago

            moneda = tabla_aux.Moneda.iloc[i]
            insert["Moneda"] = moneda

            flujo = tabla_aux.Flujo.iloc[i]
            insert["Flujo"] = flujo

            moneda_base = tabla_aux.MonedaBase.iloc[i]
            insert["MonedaBase"] = moneda_base

            insert["Amortizacion"] = tabla_aux.Amortizacion.iloc[i]
            insert["Interes"] = tabla_aux.Interes.iloc[i]
            insert["Sensibilidad"] = tabla_aux.Sensibilidad.iloc[i]

            plazo_fixing = (fecha_fixing - self.fechaActual).days
            insert["PlazoTipoCambioFwd"] = plazo_fixing

            plazo_pago = (fecha_pago - self.fechaActual).days
            insert["PlazoDescuento"] = plazo_pago

            moneda_c = cast_monedas.get(moneda, moneda)
            base_c = cast_monedas.get(moneda_base, moneda_base)

            d1 = interpolacion_log_escalar(plazo_pago, curvas_monedas[base_c])
            insert["FactorDescMonBase"] = d1

            d2 = interpolacion_log_escalar(plazo_fixing, curvas_monedas[moneda_c])
            insert["FactorDescMonFlujoFix"] = d2

            d3 = interpolacion_log_escalar(plazo_fixing, curvas_monedas[base_c])
            insert["FactorDescMonBaseFix"] = d3

            insert["ValorPresenteMonFlujo"] = d1 * flujo * (d2 / d3)
            
            
            # d1/d3 mueve a valor presente desde la fecha pago a la fecha fixing
            # d2 trae a valor presente de la fecha fixing a hoy
            if plazo_fixing == plazo_pago:
                insert["FactorDescMonFlujo"] = d2
            else:
                insert["FactorDescMonFlujo"] = d2 * (d1 / d3)

            flujos_valorizados = flujos_valorizados.append(insert, ignore_index=True)

        self.flujos_valorizados = flujos_valorizados.reset_index()
        self.set_status("INFO: Valorización completada con éxito")

    def valoriza_flujos_DV01(self):

        self.flujos_DV01_valorizados = pd.DataFrame()

        for i in range(len(self.flujos_valorizados)):
            factor_desc_mon_base = self.flujos_valorizados.FactorDescMonBase.iloc[i]
            plazo_tipo_cambio_fwd = self.flujos_valorizados.PlazoTipoCambioFwd.iloc[i]
            tipo_cambio_spot = self.flujos_valorizados.TipoCambioSpot.iloc[i]
            flujo = self.flujos_valorizados.Flujo.iloc[i]
            valor_presente_mon_base = self.flujos_valorizados.ValorPresenteMonBase.iloc[i]
            valor_presente_mon_flujo = self.flujos_valorizados.ValorPresenteMonFlujo.iloc[i]
            tipo_cambio_spot_fix = self.flujos_valorizados.TipoCambioSpotFix.iloc[i]
            factor_desc_mon_flujo_fix = self.flujos_valorizados.FactorDescMonFlujoFix.iloc[i]
            factor_desc_mon_base_fix = self.flujos_valorizados.FactorDescMonBaseFix.iloc[i]
            sensibilidad_tasa = self.flujos_valorizados.Sensibilidad.iloc[i]

            if sensibilidad_tasa == -1000:
                sensibilidad_tasa = 0

            if plazo_tipo_cambio_fwd > 0:
                tasaEqCompAct360 = (((1 / factor_desc_mon_flujo_fix) ** (360 / plazo_tipo_cambio_fwd)) - 1) * 100
                tasaDV01 = tasaEqCompAct360 + 0.01
                factorDescMonFlujoFixDV01 = 1 / ((1 + tasaDV01 / 100) ** (plazo_tipo_cambio_fwd / 360))
                tipoCambioFwdDV01 = tipo_cambio_spot_fix * factorDescMonFlujoFixDV01 / factor_desc_mon_base_fix
                flujoDV01 = flujo + sensibilidad_tasa
                valorPresenteMonBaseDV01 = flujoDV01 * tipoCambioFwdDV01 * factor_desc_mon_base
                valorPresenteMonFlujoDV01 = valorPresenteMonBaseDV01 / tipo_cambio_spot
                dv01MonBase = valorPresenteMonBaseDV01 - valor_presente_mon_base
                dv01MonFlujo = valorPresenteMonFlujoDV01 - valor_presente_mon_flujo

                if flujo == 0:
                    duracion = 0
                else:
                    duracion = (plazo_tipo_cambio_fwd / 360) / (1 + tasaEqCompAct360 / 100) - (
                                sensibilidad_tasa * 10000 / flujo)

            else:
                tasaEqCompAct360 = -1000
                tasaDV01 = -1000
                factorDescMonFlujoFixDV01 = factor_desc_mon_flujo_fix
                valorPresenteMonBaseDV01 = valor_presente_mon_base
                valorPresenteMonFlujoDV01 = valor_presente_mon_flujo
                dv01MonBase = 0
                dv01MonFlujo = 0
                duracion = 0

            insert = dict()
            insert["Fecha"] = self.flujos_valorizados.Fecha.iloc[i]
            insert["Fondo"] = self.flujos_valorizados.Fondo.iloc[i]
            insert["Tipo"] = self.flujos_valorizados.Tipo.iloc[i]
            insert["ID"] = self.flujos_valorizados.ID.iloc[i]
            insert["Hora"] = self.flujos_valorizados.Hora.iloc[i]
            insert["Mercado"] = self.flujos_valorizados.Mercado.iloc[i]
            insert["ActivoPasivo"] = self.flujos_valorizados.ActivoPasivo.iloc[i]
            insert["FechaFixing"] = self.flujos_valorizados.FechaFixing.iloc[i]
            insert["FechaFlujo"] = self.flujos_valorizados.FechaFlujo.iloc[i]
            insert["FechaPago"] = self.flujos_valorizados.FechaPago.iloc[i]
            insert["Moneda"] = self.flujos_valorizados.Moneda.iloc[i]
            insert["Flujo"] = self.flujos_valorizados.Flujo.iloc[i]
            insert["Amortizacion"] = self.flujos_valorizados.Amortizacion.iloc[i]
            insert["Interes"] = self.flujos_valorizados.Interes.iloc[i]
            insert["MonedaBase"] = self.flujos_valorizados.MonedaBase.iloc[i]
            insert["PlazoTipoCambioFwd"] = self.flujos_valorizados.PlazoTipoCambioFwd.iloc[i]
            insert["PlazoDescuento"] = self.flujos_valorizados.PlazoDescuento.iloc[i]
            insert["TipoCambioSpot"] = self.flujos_valorizados.TipoCambioSpot.iloc[i]
            insert["TipoCambioFwd"] = self.flujos_valorizados.TipoCambioFwd.iloc[i]
            insert["FactorDescMonBase"] = self.flujos_valorizados.FactorDescMonBase.iloc[i]
            insert["FactorDescMonFlujo"] = self.flujos_valorizados.FactorDescMonFlujo.iloc[i]
            insert["ValorPresenteMonBase"] = self.flujos_valorizados.ValorPresenteMonBase.iloc[i]
            insert["ValorPresenteMonFlujo"] = self.flujos_valorizados.ValorPresenteMonFlujo.iloc[i]
            insert["TipoCambioSpotFix"] = self.flujos_valorizados.TipoCambioSpotFix.iloc[i]
            insert["FactorDescMonFlujoFix"] = self.flujos_valorizados.FactorDescMonFlujoFix.iloc[i]
            insert["FactorDescMonBaseFix"] = self.flujos_valorizados.FactorDescMonBaseFix.iloc[i]
            insert["TasaEqCompAct360"] = tasaEqCompAct360
            insert["TasaDV01"] = tasaDV01
            insert["FactorDescMonFlujoFixDV01"] = factorDescMonFlujoFixDV01
            insert["TipoCambioFwdDV01"] = tipoCambioFwdDV01
            insert["ValorPresenteMonBaseDV01"] = valorPresenteMonBaseDV01
            insert["ValorPresenteMonFlujoDV01"] = valorPresenteMonFlujoDV01
            insert["Dv01MonBase"] = dv01MonBase
            insert["Dv01MonFlujo"] = dv01MonFlujo
            insert["Duracion"] = duracion
            insert["SensibilidadTasa"] = self.flujos_valorizados.Sensibilidad.iloc[i]

            self.flujos_DV01_valorizados = self.flujos_DV01_valorizados.append(insert, ignore_index=True)

        self.set_status("INFO: Valorización DV01 completada con éxito")




    def agrega_cambio_spot(self):
        fechas_tipo_cambio_spot = list()

        for i in range(len(self.flujos_valorizados)):
            plazo_pago = (self.flujos_valorizados.FechaPago.iloc[i] - self.fechaActual).days
            plazo_flujo = (self.flujos_valorizados.FechaFlujo.iloc[i] - self.fechaActual).days
            plazo_fixing = (self.flujos_valorizados.FechaFixing.iloc[i] - self.fechaActual).days

            if plazo_flujo > 0:
                plazo_flujo = 0

            if plazo_pago > 0:
                plazo_pago = 0

            if plazo_fixing > 0:
                plazo_fixing = 0

            fechas_tipo_cambio_spot.append(fecha_str(add_days(self.fechaActual, plazo_fixing)))
            fechas_tipo_cambio_spot.append(fecha_str(add_days(self.fechaActual, plazo_pago)))
            fechas_tipo_cambio_spot.append(fecha_str(add_days(self.fechaActual, plazo_flujo)))

        fechas_tipo_cambio_spot = list(set(fechas_tipo_cambio_spot))

        fechas_tipo_cambio_spot = str(fechas_tipo_cambio_spot)[1:-1].replace('"', "")


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

        camino_monedas = ("SELECT * FROM dbDerivados.dbo.FnCaminoMonedas()")

        sql_monedas = sql_monedas_observadas_parchadas + " UNION " + sql_monedas_cierre

        cast_monedas = {'UF': 'CLF', 'CLN': 'COP'}
        valores_monedas = pd.io.sql.read_sql(sql_monedas, self.cn)
        camino_monedas = pd.io.sql.read_sql(camino_monedas, self.cn)

        for i in range(len(self.flujos_valorizados)):
            d1 = self.flujos_valorizados.FactorDescMonBase.iloc[i]
            d2 = self.flujos_valorizados.FactorDescMonFlujoFix.iloc[i]
            d3 = self.flujos_valorizados.FactorDescMonBaseFix.iloc[i]

            flujo = self.flujos_valorizados.Flujo.iloc[i]

            moneda = cast_monedas.get(self.flujos_valorizados.Moneda.iloc[i], self.flujos_valorizados.Moneda.iloc[i])
            moneda_base = cast_monedas.get(self.flujos_valorizados.MonedaBase.iloc[i],
                                           self.flujos_valorizados.MonedaBase.iloc[i])

            valores_monedas_t = valores_monedas.loc[valores_monedas['Fecha'] == pd.Timestamp(self.fechaActual)]
            valores_monedas_t = valores_monedas_t.loc[valores_monedas_t['SpotObservado'] == 'Spot']

            tipo_cambio_t = valor_moneda(moneda, moneda_base, camino_monedas, valores_monedas_t)

            if tipo_cambio_t is None:
                self.set_status("ERROR: valor_moneda: No se encontró camino para " + moneda + " " + moneda_base +
                                " en derivado con ID: " + str(self.info_cartera.ID.iloc[0]))
                return

            plazo_fixing = (self.flujos_valorizados.FechaFixing.iloc[i] - self.fechaActual).days

            if plazo_fixing > 0:
                plazo_fixing = 0

            valores_monedas_fix = valores_monedas.loc[valores_monedas['Fecha'] == pd.Timestamp(add_days(self.fechaActual,
                                                                                                        plazo_fixing))]

            if plazo_fixing >= 0:
                valores_monedas_fix = valores_monedas_fix.loc[valores_monedas_fix['SpotObservado'] == 'Spot']
            else:
                valores_monedas_fix = valores_monedas_fix.loc[valores_monedas_fix['SpotObservado'] == 'Observado']

            tipo_cambio_fix = valor_moneda(moneda, moneda_base, camino_monedas, valores_monedas_fix)

            if tipo_cambio_fix is None:
                self.set_status("ERROR: valor_moneda: No se encontró camino para " + moneda + " " + moneda_base +
                                " en derivado con ID: " + str(self.info_cartera.ID.iloc[0]))
                return

            self.flujos_valorizados.TipoCambioSpot.iloc[i] = tipo_cambio_t
            self.flujos_valorizados.TipoCambioSpotFix.iloc[i] = tipo_cambio_fix

            valor_presente_mon_base = d1 * flujo * (d2 / d3) * tipo_cambio_t

            self.flujos_valorizados.ValorPresenteMonBase.iloc[i] = valor_presente_mon_base
            self.flujos_valorizados.TipoCambioFwd.iloc[i] = (d2 / d3) * tipo_cambio_t

            # Agregando valores CLP y USD

            cambio_usd_base = valor_moneda(moneda_base, "USD", camino_monedas, valores_monedas)
            cambio_clp_base = valor_moneda(moneda_base, "CLP", camino_monedas, valores_monedas)

            self.flujos_valorizados.TipoCambioCLPBase.iloc[i] = cambio_clp_base
            self.flujos_valorizados.TipoCambioUSDBase.iloc[i] = cambio_usd_base

            self.flujos_valorizados.ValorPresenteUSD.iloc[i] = valor_presente_mon_base * cambio_usd_base
            self.flujos_valorizados.ValorPresenteCLP.iloc[i] = valor_presente_mon_base * cambio_clp_base
        self.set_status("INFO: Cambio Spot agregado con éxito")
