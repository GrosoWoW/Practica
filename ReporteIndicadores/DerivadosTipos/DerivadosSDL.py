# -*- coding: utf-8 -*-
from Derivados.DerivadosAbstracto import *
from UtilesDerivados import cast_frecuencia, ultimo_habil_pais, delta_frecuencia, siguiente_habil_pais, siguiente_habil_paises
from UtilIndicadores import add_days
from Matematica import interpolacion_log_escalar
from Curves.CurvaCero import curva_cero_swapUSD

def tasa_FRA_y_tasa_DV01(plazo_ini, plazo_fin, spread, arr_factor_descuento):

    fd_ini = interpolacion_log_escalar(plazo_ini, arr_factor_descuento)
    fd_fin = interpolacion_log_escalar(plazo_fin, arr_factor_descuento)

    tasa_eq_comp_act_360_ini = (((1/fd_ini)**(360/plazo_ini))-1)*100
    tasa_eq_comp_act_360_ini_DV01 = tasa_eq_comp_act_360_ini + 0.01

    fd_ini_DV01 = (tasa_eq_comp_act_360_ini_DV01 / 100 + 1)**(-plazo_ini/360)

    tasa_eq_comp_act_360_fin = (((1 / fd_fin) ** (360 / plazo_fin)) - 1) * 100
    tasa_eq_comp_act_360_fin_DV01 = tasa_eq_comp_act_360_fin + 0.01

    fd_fin_DV01 = (tasa_eq_comp_act_360_fin_DV01 / 100 + 1) ** (-plazo_fin / 360)

    tasa = (((fd_ini / fd_fin) ** (360 / (plazo_fin - plazo_ini))) - 1) * 100 + spread / 100
    tasaDV01 = (((fd_ini_DV01 / fd_fin_DV01) ^ (360 / (plazo_fin - plazo_ini))) - 1) * 100 + spread / 100

    return [tasa, tasaDV01]


class DerivadosSDL(DerivadosAbstracto):

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
            frecuencia_fija = self.info_cartera.FrecuenciaActivo[0]
            frecuencia_variable = self.info_cartera.FrecuenciaPasivo[0]
        else:
            factor_recibo_fijo = -1
            tasa = self.info_cartera.TasaPasivo[0]
            frecuencia_fija = self.info_cartera.FrecuenciaPasivo[0]
            frecuencia_variable = self.info_cartera.FrecuenciaActivo[0]

        nocional = self.info_cartera.NocionalActivo[0]

        frecuencia_fija = cast_frecuencia(frecuencia_fija)
        frecuencia_variable = cast_frecuencia(frecuencia_variable)

        id_key = self.info_cartera.ID_Key[0]

        fecha_aux = add_days(max(fecha, fecha_efectiva), -1)
        fecha_aux = add_days(ultimo_habil_pais(fecha_aux, "US", cn), 1)

        flujos_f = genera_flujos(fecha_aux, fecha_efectiva, fecha_venc, tasa, frecuencia_fija, "ACT360")

        arr_factor_descuento = curva_cero_swapUSD(fecha, hora, frecuencia_variable, "ACT360", cn)

        print("arr", arr_factor_descuento)

        flujos_v = genera_flujos(fecha_aux, fecha_efectiva, fecha_venc, 0, frecuencia_variable, "ACT360")

        flujos_v_DV01 = flujos_v

        flujos_f_ns = flujos_v

        for i in range(len(flujos_v)):
            fecha_anterior = delta_frecuencia(flujos_v[i][0], frecuencia_variable, -1)

            print(flujos_v[i][0])

            fecha_fijacion_libor = add_days(ultimo_habil_pais(add_days(fecha_anterior, -1), "UK", cn), -1)
            fecha_fijacion_libor = ultimo_habil_pais(fecha_fijacion_libor, "UK", cn)

            fecha_fijacion_libor_siguiente = add_days(ultimo_habil_pais(add_days(flujos_v[i][0], -1), "UK", cn), -1)
            fecha_fijacion_libor_siguiente = ultimo_habil_pais(fecha_fijacion_libor_siguiente, "UK", cn)

            flujos_v[i][0] = siguiente_habil_pais(add_days(flujos_v[i][0], -1), "US", cn)
            flujos_v_DV01[i][0] = flujos_v[i][0]
            flujos_f_ns[i][0] = flujos_v[i][0]

            max_fecha_libor = ("SELECT Max(T.Fecha) as FechaMax "
                               "FROM dbAlgebra.dbo.TdInfoTasas I "
                               "INNER JOIN "
                                "dbAlgebra.dbo.TdTasas T "
                               "ON I.TickerCorto = T.Tasa "
                               "WHERE T.SiValida = 1 AND T.Hora = 'CIERRE' AND I.Plazo = '" + frecuencia_variable + "' "
                               "AND I.TipoTasa = 'LIBOR' AND I.MonedaActiva = 'USD' "
                               "AND T.Fecha <= " + fecha_str(fecha_fijacion_libor) + "")

            max_fecha_libor = pd.io.sql.read_sql(max_fecha_libor, self.cn).FechaMax.iloc[0]

            if fecha_fijacion_libor <= fecha:
                libor = ("SELECT T.Valor "
                         "FROM dbAlgebra.dbo.TdInfoTasas I "
                         "INNER JOIN "
                            "dbAlgebra.dbo.TdTasas T "
                         "ON I.TickerCorto = T.Tasa "
                         "WHERE T.SiValida = 1 AND T.Hora = 'CIERRE' AND I.Plazo = '" + frecuencia_variable + "' "
                         "AND I.TipoTasa = 'LIBOR' AND I.MonedaActiva = 'USD' "
                         "AND T.Fecha = " + fecha_str(max_fecha_libor) + " ORDER BY I.Plazo360")

                libor = pd.io.sql.read_sql(libor, self.cn).Valor.iloc[0]
                tasa = libor
                tasaDV01 = tasa

                if fecha_fijacion_libor_siguiente > fecha or len(flujos_v) - 1 == i:
                    flujos_f_ns[i][1] = 100 + tasa * (flujos_f_ns[i][0] - fecha_anterior).days / 360
                else:
                    flujos_f_ns[i][1] = tasa * (flujos_f_ns[i][0] - fecha_anterior).days / 360
                flujos_v[i][6] = tasa * (fecha - fecha_anterior).days / 360
            else:

                plazo_ini = (fecha_fijacion_libor - fecha).days
                plazo_fin = (fecha_fijacion_libor_siguiente - fecha).days

                tasa_arr = tasa_FRA_y_tasa_DV01(plazo_ini, plazo_fin, 0, arr_factor_descuento)
                tasa = tasa_arr[0]
                tasaDV01 = tasa_arr[1]

                flujos_f_ns[i][1] = 0
                flujos_v[i][6] = 0

            flujos_v[i][1] = flujos_v[i][1] + tasa * (flujos_v[i][0] - fecha_anterior).days / 360
            flujos_v[i][4] = tasa * (flujos_v[i][0] - fecha_anterior).days / 360
            flujos_v_DV01[i][1] = flujos_v_DV01[i][1] + tasaDV01 * (flujos_v_DV01[i][0] - fecha_anterior).days / 360

        insert = dict()
        insert["Fecha"] = fecha
        insert["Administradora"] = admin
        insert["Fondo"] = fondo
        insert["Contraparte"] = contraparte
        insert["Tipo"] = "SDL"
        insert["ID"] = id
        insert["Hora"] = hora
        insert["ActivoPasivo"] = -factor_recibo_fijo
        insert["Id_Key_Cartera"] = id_key

        for i in range(len(flujos_v)):

            insert["FechaFixing"] = flujos_v[i][0]
            insert["FechaFlujo"] = flujos_v[i][0]
            insert["FechaPago"] = siguiente_habil_paises(add_days(flujos_v[i][0], -1), paises_feriados, cn)
            insert["Moneda"] = moneda
            insert["Flujo"] = flujos_v[i][1] / 100 * nocional
            insert["Amortizacion"] = flujos_v[i][3] / 100 * nocional
            insert["Interes"] = flujos_v[i][4] / 100 * nocional
            insert["Sensibilidad"] = (flujos_v_DV01[i][1] - flujos_v[i][1]) / 100 * nocional
            insert["InteresDevengado"] = flujos_v[i][6] / 100 * nocional

            self.flujos_derivados = self.flujos_derivados.append(insert)

        insert_nosensible = dict()
        insert_nosensible["Fecha"] = fecha
        insert_nosensible["Administradora"] = admin
        insert_nosensible["Fondo"] = fondo
        insert_nosensible["Contraparte"] = contraparte
        insert_nosensible["Tipo"] = "SDL"
        insert_nosensible["ID"] = id
        insert_nosensible["Hora"] = hora
        insert_nosensible["ActivoPasivo"] = factor_recibo_fijo
        insert_nosensible["Id_Key_Cartera"] = id_key
        insert["ActivoPasivo"] = factor_recibo_fijo

        for i in flujos_f:
            insert["FechaFixing"] = i[0]
            insert["FechaFlujo"] = i[0]
            insert["FechaPago"] = siguiente_habil_paises(add_days(i[0], -1), paises_feriados, cn)
            insert["Moneda"] = moneda
            insert["Flujo"] = i[1] / 100 * nocional
            insert["Amortizacion"] = i[3] / 100 * nocional
            insert["Interes"] = i[4] / 100 * nocional
            insert["InteresDevengado"] = i[6] / 100 * nocional
            self.flujos_derivados = self.flujos_derivados.append(insert)

            insert_nosensible["FechaFlujoNoSensible"] = i[0]
            insert_nosensible["Moneda"] = moneda
            insert_nosensible["FlujoNoSensible"] = i[1] / 100 * nocional
            self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible)

        insert_nosensible["ActivoPasivo"] = -factor_recibo_fijo
        for i in flujos_f_ns:
            insert_nosensible["FechaFlujoNoSensible"] = i[0]
            insert_nosensible["FlujoNoSensible"] = i[1] / 100 * nocional
            self.flujos_nosensibles = self.flujos_nosensibles.append(insert_nosensible)

        self.set_status("INFO: Flujos generados para SDL con ID " + str(self.info_cartera.ID.iloc[0]))



