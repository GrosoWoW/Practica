# -*- coding: utf-8 -*-
from Derivados.DerivadosAbstracto import *
from UtilIndicadores import add_days
from UtilesDerivados import ultimo_habil_pais, siguiente_habil_paises
from UtilesDerivados import proyectar_flujo


class DerivadosSPD(DerivadosAbstracto):

    def genera_flujos(self):
        hora = self.hora
        cn = self.cn
        fecha = self.fecha

        admin = self.info_cartera.Administradora[0]

        fondo = self.info_cartera.Fondo[0]
        contraparte = self.info_cartera.Contraparte[0]
        id = self.info_cartera.ID[0]

        fecha_efectiva = pd.to_datetime(self.info_cartera.FechaEfectiva[0]).date()
        fecha_venc = pd.to_datetime(self.info_cartera.FechaVenc[0]).date()

        ajuste_feriados = self.info_cartera.AjusteFeriados[0]
        paises_feriados = ajuste_feriados.split(',')

        moneda = self.info_cartera.MonedaActivo[0]

        if self.info_cartera.TipoTasaActivo[0] == 'Fija':
            factor_recibo_fijo = 1
            tasa = self.info_cartera.TasaActivo[0]
        else:
            factor_recibo_fijo = -1
            tasa = self.info_cartera.TasaPasivo[0]

        nocional = self.info_cartera.NocionalActivo[0]
        mercado = self.info_cartera.Mercado[0]
        id_key = self.info_cartera.ID_Key[0]

        moneda_base = self.info_cartera.MonedaBase[0]
        if moneda_base == "--":
            moneda_base = moneda

        fecha_aux1 = fecha_str(add_days(fecha_efectiva, 1))
        fecha_aux2 = fecha_str(fecha_venc)
        fecha_aux3 = fecha_str(add_days(max(fecha_efectiva, fecha), 1))
        fecha_aux4 = fecha_str(fecha_venc)

        plazo_ini = ("SELECT SUM(SiHabil) AS Lab "
                     "FROM dbAlgebra.dbo.TdFeriados "
                     "WHERE Pais = 'BR' AND (Fecha BETWEEN " + fecha_aux1 + " AND " + fecha_aux2 + ")")

        plazo_ini = pd.io.sql.read_sql(plazo_ini, cn).Lab[0]

        plazo = ("SELECT SUM(SiHabil) AS Lab "
                 "FROM dbAlgebra.dbo.TdFeriados "
                 "WHERE Pais = 'BR' AND (Fecha BETWEEN " + fecha_aux3 + " AND " + fecha_aux4 + ")")

        plazo = pd.io.sql.read_sql(plazo, cn).Lab[0]

        pv = nocional / (1 + tasa / 100) ** (plazo_ini / 252)

        if fecha < fecha_efectiva:
            vpv = 1
            flujo_variable_presente = vpv * pv
            fecha_flujo_variable_presente = fecha_efectiva

        else:
            fecha_aux1 = fecha_str(add_days(fecha_efectiva, 1))
            fecha_aux2 = fecha_str(add_days(max(fecha_efectiva, fecha), -1))


            arr_di = ("SELECT COALESCE ((EXP(SUM(LOG(POWER(1 + T.Valor / 100, 1 / CAST(252 AS float))))) - 1) * 100, 0) "
                      "AS DIAcum, COUNT(*) AS N "
                      "FROM dbAlgebra.dbo.TdTasas T "
                      "INNER JOIN dbAlgebra.dbo.TdInfoTasas I "
                      "ON T.Tasa = I.TickerCorto "
                      "INNER JOIN dbAlgebra.dbo.TdFeriados F "
                      "ON T.Fecha = F.Fecha "
                      "WHERE (T.SiValida = 1) AND (T.Hora = 'CIERRE') AND (I.Plazo = '1D') AND (I.TipoTasa = 'SWAP') "
                      "AND (I.MonedaActiva = 'BRL') AND (T.Fecha BETWEEN " + fecha_aux1 + " "
                      "AND " + fecha_aux2 + ") AND (T.Valor >= 0) AND (F.Pais = 'BR') AND (F.SiHabil = 1)")

            arr_di = pd.io.sql.read_sql(arr_di, self.cn)

            if ultimo_habil_pais(fecha, "BR", cn) == fecha and plazo_ini != plazo:
                fecha_aux1 = fecha_str(ultimo_habil_pais(add_days(max(fecha_efectiva, fecha), -1), "BR", cn))

                di_dia = ("SELECT T.Valor AS DIDia "
                          "FROM dbAlgebra.dbo.TdTasas T "
                          "INNER JOIN dbAlgebra.dbo.TdInfoTasas I "
                          "ON T.Tasa = I.TickerCorto WHERE (T.SiValida = 1) AND (T.Hora = 'CIERRE') "
                          "AND (I.Plazo = '1D') AND (I.TipoTasa = 'SWAP') AND (I.MonedaActiva = 'BRL') "
                          "AND (T.Fecha = " + fecha_aux1 + ")")

                di_dia = pd.io.sql.read_sql(di_dia, self.cn).DIDia.iloc[0]

                di_acum = (((arr_di.DIAcum.iloc[0] / 100) + 1) * ((1 + di_dia/100)**(1/252)) - 1) * 100

            else:
                di_acum = arr_di.DIAcum.iloc[0]

            vpv = (di_acum/100) + 1

            flujo_variable_presente = vpv * pv
            fecha_flujo_variable_presente = fecha

            fecha_pago = add_days(fecha_venc, -1)
            fecha_pago = siguiente_habil_paises(fecha_pago, paises_feriados, cn)

        fecha_flujo_variable = fecha_venc

        flujo_variable = proyectar_flujo(fecha_flujo_variable_presente, hora, fecha_venc, fecha_venc, mercado, moneda,
                                        flujo_variable_presente, moneda_base, cn)

        insert = dict()
        insert_nosensible = dict()

        insert["Fecha"] = fecha
        insert["Administradora"] = admin
        insert["Fondo"] = fondo
        insert["Contraparte"] = contraparte
        insert["Tipo"] = "SPD"
        insert["ID"] = id
        insert["ActivoPasivo"] = -factor_recibo_fijo
        insert["FechaFixing"] = fecha_flujo_variable
        insert["FechaFlujo"] = fecha_flujo_variable
        insert["FechaPago"] = fecha_pago
        insert["Moneda"] = moneda
        insert["Flujo"] = flujo_variable
        insert["Amortizacion"] = flujo_variable
        insert["Interes"] = 0
        insert["Id_Key_Cartera"] = id_key

        self.flujos_derivados = self.flujos_derivados.append(insert, ignore_index=True)

        insert_nosensible["Fecha"] = fecha
        insert_nosensible["Administradora"] = admin
        insert_nosensible["Fondo"] = fondo
        insert_nosensible["Contraparte"] = contraparte
        insert_nosensible["Tipo"] = "SPD"
        insert_nosensible["ID"] = id
        insert_nosensible["ActivoPasivo"] = -factor_recibo_fijo
        insert_nosensible["FechaFlujoNoSensible"] = fecha_flujo_variable_presente
        insert_nosensible["Moneda"] = moneda
        insert_nosensible["FlujoNoSensible"] = flujo_variable
        insert_nosensible["Id_Key_Cartera"] = id_key

        self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible, ignore_index=True)

        insert["Flujo"] = nocional
        insert["Amortizacion"] = nocional

        insert_nosensible["FlujoNoSensible"] = nocional

        insert["FechaFixing"] = fecha_venc
        insert["FechaFlujo"] = fecha_venc

        insert_nosensible["FechaFlujoNoSensible"] = fecha_venc

        insert["FechaPago"] = siguiente_habil_paises(add_days(fecha_venc, -1), paises_feriados, cn)

        insert_nosensible["ActivoPasivo"] = factor_recibo_fijo
        insert["ActivoPasivo"] = factor_recibo_fijo

        self.flujos_derivados = self.flujos_derivados.append(insert, ignore_index=True)
        self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible, ignore_index=True)

        self.set_status("INFO: Flujos generados para SPD con ID " + str(self.info_cartera.ID.iloc[0]))










