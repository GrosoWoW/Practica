# -*- coding: utf-8 -*-
from Derivados.DerivadosAbstracto import *
from UtilesDerivados import get_tabla_desarrollo_fecha_emision_EX, get_tabla_desarrollo_fecha_emision, \
    siguiente_habil_paises
from UtilesValorizacion import base_convencion
from Calculadora import meta_calculadora_CO, meta_calculadora_CL

class DerivadosFRF(DerivadosAbstracto):

    def genera_flujos(self):
        hora = self.hora
        cn = self.cn
        fecha = self.fecha

        admin = self.info_cartera.Administradora[0]

        fondo = self.info_cartera.Fondo[0]
        contraparte = self.info_cartera.Contraparte[0]
        id = self.info_cartera.ID[0]

        fecha_venc = self.info_cartera.FechaVenc[0].to_pydatetime().date()

        ajuste_feriados = self.info_cartera.AjusteFeriados[0]
        paises_feriados = ajuste_feriados.split(',')

        nemotecnico = self.info_cartera.Nemotecnico[0]

        referencia = self.info_cartera.Referencia[0]

        moneda_base = self.info_cartera.MonedaBase[0]
        moneda = self.info_cartera.MonedaActivo[0]

        if self.info_cartera.TipoTasaActivo[0] == 'Fija':
            factor_recibo_fijo = 1
            tasa = self.info_cartera.TasaActivo[0]
        else:
            factor_recibo_fijo = -1
            tasa = self.info_cartera.TasaPasivo[0]

        nocional = self.info_cartera.NocionalActivo[0]
        id_key = self.info_cartera.ID_Key[0]
        vencimiento_frf = (fecha_venc - fecha).days

        vff = 0 # valor futuro pata fija

        if nemotecnico[0:3] == "COL":
            if moneda_base == '--':
                moneda_base = moneda

            convencion = ("SELECT I.Valor FROM dbIncoming.dbo.TdBLGInfoTicker I "
                   "INNER JOIN (SELECT MAX(Fecha) AS Fecha, BlgField, Ticker "
                   "FROM dbIncoming.dbo.TdBLGInfoTicker "
                   "WHERE (BlgField = 'DAY_CNT_DES') AND Ticker = '" + nemotecnico + "') "
                   "GROUP BY BlgField, Ticker) TF ON I.Fecha = TF.Fecha "
                   "AND I.BlgField = TF.BlgField AND I.Ticker = TF.Ticker ")

            convencion = pd.io.sql.read_sql(convencion, self.cn).Valor[0]

            arr_tir = ("SELECT I.Valor FROM dbincoming.dbo.TdBLGDatos I "
                       "INNER JOIN (SELECT MAX(Fecha) AS Fecha, BlgField, Ticker "
                       "FROM dbincoming.dbo.TdBLGDatos "
                       "WHERE (BlgField = 'YLD_YTM_MID') "
                       "AND (Ticker = '" + nemotecnico + "') AND Fecha <= " + fecha_str(fecha) + " "
                       "GROUP BY Ticker, BlgField) TF ON I.Fecha = TF.Fecha AND I.BlgField = TF.BlgField "
                       "AND I.Ticker = TF.Ticker")

            arr_tir = pd.io.sql.read_sql(arr_tir, self.cn)

            if len(arr_tir) > 0:
                tir_mercado = arr_tir.Valor[0]
            else:
                tir_mercado = -1000

            flujos = get_tabla_desarrollo_fecha_emision_EX(fecha, nemotecnico, cn)
            idxs = list(range(len(flujos[0])))
            idxs.pop(1)  # this removes elements from the list

            arr_tabla = flujos[:, idxs][1:]

            vft = meta_calculadora_CO(fecha_venc, nemotecnico, convencion, flujos, tasa, ["VPRESS"], cn)[0]
            vtv = meta_calculadora_CO(fecha_venc, nemotecnico, convencion, flujos, tir_mercado, ["VPRESS"], cn)[0]

            t = ((1 + tir_mercado / 100) ** (360 / base_convencion(convencion)) - 1) * 100 + 0.01
            vfvDV01 = meta_calculadora_CO(fecha_venc, nemotecnico, "ACT/360", flujos, t, ["VPRESS"], cn)[0]

            tir_valorizacion = tir_mercado

        else:
            tera = ("SELECT tera "
                    "FROM dbAlgebra.dbo.VwNemoRF "
                    "WHERE Nemotecnico='" + nemotecnico + "' and Fecha = " + fecha_str(fecha) + "")
            tera = pd.io.sql.read_sql(tera, self.cn).tera.iloc[0]

            duracion_tir_mercado_dias = ("SELECT ROUND(DurModSc*365,0) AS DurTirMer "
                                         "FROM dbalgebra.dbo.TdValorizaRFLva "
                                         "WHERE Nemotecnico='" + nemotecnico + "' and Fecha=" + fecha_str(fecha) + "")
            duracion_tir_mercado_dias = int(pd.io.sql.read_sql(duracion_tir_mercado_dias, self.cn).DurTirMer.iloc[0])

            tir_mercado = ("SELECT T.Tir "
                           "FROM dbDerivados.dbo.TdBenchmark T "
                           "INNER JOIN "
                            "(SELECT MAX(Fecha) AS Fecha, Benchmark "
                            "FROM dbDerivados.dbo.TdBenchmark "
                            "WHERE (Benchmark = '" + referencia + "') AND (Fecha <= " + fecha_str(fecha) + ") "
                            "AND (Tir <> - 1000) "
                            "GROUP BY Benchmark) FN "
                           "ON T.Fecha = FN.Fecha AND T.Benchmark = FN.Benchmark ")

            tir_mercado = pd.io.sql.read_sql(tir_mercado, self.cn).Tir.iloc[0]

            if moneda == 'UF':
                tir_vencimiento = ("SELECT * "
                                   "FROM dbalgebra.dbo.FnParseaCurvaSvensson("+fecha_str(fecha)+",'UF',1,15000) "
                                    "WHERE plazoDias =" + str(vencimiento_frf))
                tir_vencimiento = pd.io.sql.read_sql(tir_vencimiento, self.cn).tasa.iloc[0]

                tir_duracion = ("SELECT * "
                                   "FROM dbalgebra.dbo.FnParseaCurvaSvensson("+fecha_str(fecha)+",'UF',1,15000) "
                                    "WHERE plazoDias =" + str(duracion_tir_mercado_dias))

                tir_duracion = pd.io.sql.read_sql(tir_duracion, self.cn).tasa.iloc[0]

            elif moneda == 'CLP':
                tir_vencimiento = ("SELECT * "
                                   "FROM dbalgebra.dbo.FnParseaCurvaSvensson(" + fecha_str(fecha) + ",'PESOS',1,15000) "
                                   "WHERE plazoDias =" + vencimiento_frf)
                tir_vencimiento = pd.io.sql.read_sql(tir_vencimiento).tasa.iloc[0]

                tir_duracion = ("SELECT * "
                                "FROM dbalgebra.dbo.FnParseaCurvaSvensson(" + fecha_str(fecha) + ",'PESOS',1,15000) "
                                "WHERE plazoDias =" + duracion_tir_mercado_dias)

                tir_duracion = pd.io.sql.read_sql(tir_duracion).tasa.iloc[0]

            else:
                pass #todo ERROR

            FRA_tir_mercado = 100*((((1+tir_duracion/100)**(duracion_tir_mercado_dias/365))/((1+tir_vencimiento/100)**(vencimiento_frf/365) ) )**(365/(duracion_tir_mercado_dias-vencimiento_frf))-1)

            tir_mercado_ajustada = tir_mercado + FRA_tir_mercado - tir_duracion

            arr_tabla = ("SELECT Cupon, Fecha, Interes, Amortizacion, Saldo, Flujo "
                        "FROM dbAlgebra.dbo.FnParseaTablaDesarrollo(" + fecha_str(fecha) + ", 'BT', '" + nemotecnico + "')")

            arr_aux = ("SELECT Moneda, base1, base2 "
                       "FROM dbAlgebra.dbo.VwNemo "
                       "WHERE Fecha = " + fecha_str(fecha) + " AND Nemotecnico = '" + nemotecnico + "' AND Familia = 'BT'")

            arr_aux = pd.io.sql.read_sql(arr_aux, self.cn)

            if arr_aux.base1.iloc[0] == -1 and arr_aux.base2.iloc[0] == 360:
                day_count = 'ACT360'
            elif arr_aux.base1.iloc[0] == -1 and arr_aux.base2.iloc[0] == 365:
                day_count = 'ACT365'
            else:
                pass # todo ERROR

            td_desarrollo = get_tabla_desarrollo_fecha_emision(fecha, nemotecnico, "BT", cn)
            vff = meta_calculadora_CL("BT", nemotecnico, fecha_venc, td_desarrollo, arr_aux[0][1], arr_aux[0][2], tasa,
                                      tera, ["VPRESS"], cn)[0]

            vfv = meta_calculadora_CL("BT", nemotecnico, fecha_venc, td_desarrollo, arr_aux[0][1], arr_aux[0][2],
                                      tir_mercado_ajustada, tera, ["VPRESS"], cn)[0]

            vfvDV01 = meta_calculadora_CL("BT", nemotecnico, fecha_venc, td_desarrollo, -1, 360,
                                          ((1 + tir_mercado_ajustada / 100) ^ (360 / arr_aux[0][2]) - 1) * 100 + 0.01,
                                          tera, ["VPRESS"], cn)[0]

            tir_valorizacion = tir_mercado_ajustada

        fecha_pago = siguiente_habil_paises(add_days(fecha_venc, -1), paises_feriados, cn)

        insert = dict()
        insert_nosensible = dict()

        insert["Fecha"] = fecha
        insert["Administradora"] = admin
        insert["Fondo"] = fondo
        insert["Contraparte"] = contraparte
        insert["Tipo"] = "SPD"
        insert["ID"] = id
        insert["ActivoPasivo"] = factor_recibo_fijo
        insert["FechaFixing"] = fecha_venc
        insert["FechaFlujo"] = fecha_venc
        insert["FechaPago"] = fecha_pago
        insert["Moneda"] = moneda
        insert["Flujo"] = vff * nocional
        insert["Amortizacion"] = vff * nocional
        insert["Interes"] = 0
        insert["Sensibilidad"] = 0
        insert["Id_Key_Cartera"] = id_key

        self.flujos_derivados = self.flujos_derivados.append(insert, ignore_index=True)

        insert_nosensible["Fecha"] = fecha
        insert_nosensible["Administradora"] = admin
        insert_nosensible["Fondo"] = fondo
        insert_nosensible["Contraparte"] = contraparte
        insert_nosensible["Tipo"] = "SPD"
        insert_nosensible["ID"] = id
        insert_nosensible["ActivoPasivo"] = factor_recibo_fijo
        insert_nosensible["FechaFlujoNoSensible"] = fecha_venc
        insert_nosensible["Moneda"] = moneda
        insert_nosensible["FlujoNoSensible"] = vff * nocional
        insert_nosensible["Id_Key_Cartera"] = id_key

        self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible, ignore_index=True)

        insert["Flujo"] = vfv * nocional
        insert["FechaPago"] = fecha_venc
        insert["Amortizacion"] = vfv * nocional
        insert["Sensibilidad"] = (vfv - vfvDV01) * nocional
        insert["ActivoPasivo"] = -factor_recibo_fijo

        self.flujos_derivados = self.flujos_derivados.append(insert, ignore_index=True)

        kmin = 0
        kmax = 0
        while arr_tabla[kmin][1] <= fecha:
            kmin += 1

        while arr_tabla[kmax][1] <= fecha_venc:
            kmax += 1

        for k in range(kmin, kmax):
            valor_futuro_cupon = nocional * arr_tabla[k][5] / 100
            fecha_pago = siguiente_habil_paises(add_days(arr_tabla[k][1], -1), paises_feriados, cn)

            insert_nosensible["FlujoNoSensible"] = valor_futuro_cupon
            insert_nosensible["FechaFlujoNoSensible"] = arr_tabla[k][1]
            self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible, ignore_index=True)

        for k in range(max(kmin, kmax), len(arr_tabla)):
            valor_futuro_cupon = nocional * arr_tabla[k][5] / 100

            insert_nosensible["FechaFlujoNoSensible"] = arr_tabla[k][1]
            insert_nosensible["FlujoNoSensible"] = valor_futuro_cupon
            insert_nosensible["ActivoPasivo"] = -factor_recibo_fijo
            self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible, ignore_index=True)












