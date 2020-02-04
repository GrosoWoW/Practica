# -*- coding: utf-8 -*-
from Derivados.DerivadosAbstracto import *
from UtilesDerivados import genera_flujos, proyectar_flujos_tabla, ultimo_habil_pais, delta_frecuencia, siguiente_habil_paises
from Util import fecha_str, add_days, add_months
import pandas as pd


class DerivadosIBR(DerivadosAbstracto):

    def genera_flujos(self):
        hora = self.hora
        cn = self.cn
        fecha = self.fecha


        fondo = self.info_cartera.Fondo[0]
        
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

        frecuencia = self.info_cartera.FrecuenciaActivo[0]

        id_key = self.info_cartera.ID_Key[0]

        flujos_f = genera_flujos(max(fecha, fecha_efectiva), fecha_efectiva, fecha_venc, tasa, frecuencia, "LACT360")
        fecha_cupon = flujos_f[0][0]

        fecha_aux = delta_frecuencia(fecha_cupon, frecuencia, -1)
        fecha_aux = max(fecha_aux, fecha_efectiva)

        fecha_cupon_anterior = ultimo_habil_pais(fecha_aux, "CO", cn)

        fecha_aux1 = fecha_str(add_months(max(fecha_efectiva, fecha_cupon_anterior), -1))
        fecha_aux2 = fecha_str(add_days(ultimo_habil_pais(max(fecha_efectiva, fecha), "CO", cn), -1))
        fecha_aux3 = fecha_str(max(fecha_efectiva, fecha_cupon_anterior))
        fecha_aux4 = fecha_str(add_days(ultimo_habil_pais(max(fecha_efectiva, fecha), "CO", cn), -1))

        ibr_acum = ("SELECT COALESCE (EXP(SUM(LOG(1 + T.Valor / CAST(36000 as float)))), 1) AS IbrAcum "
                    "FROM ("
                        "SELECT MAX(T.Fecha) AS FechaMax, I.Fecha "
                        "FROM dbAlgebra.dbo.TdTasas T INNER JOIN dbAlgebra.dbo.TdIndicadores I "
                           "ON T.Fecha <= I.Fecha "
                        "WHERE T.SiValida = 1 AND T.Hora = 'CIERRE' AND T.Tasa = 'COOVIBR' "
                            "AND T.Fecha BETWEEN " + fecha_aux1 + " AND " + fecha_aux2 + ""
                            "AND I.Fecha BETWEEN " + fecha_aux3 + " AND " + fecha_aux4 + ""
                            "AND T.SiValida = 1 "
                        "GROUP BY I.Fecha) F "
                        "INNER JOIN dbAlgebra.dbo.TdTasas T "
                            "ON F.FechaMax = T.Fecha "
                    "WHERE T.SiValida = 1 AND T.Hora = 'CIERRE' AND T.Tasa = 'COOVIBR'")

        ibr_acum = pd.io.sql.read_sql(ibr_acum, cn)
        ibr_acum = ibr_acum.IbrAcum[0]
        flujos_v = proyectar_flujos_tabla(fecha, fecha, ibr_acum, hora, fecha_efectiva, fecha_venc, frecuencia, moneda,
                                          0, "Local", ajuste_feriados, cn)


        # Simulamos los insert a base de datos

        col_flujos_derivados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'ActivoPasivo',
                                'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo', 'Amortizacion', 'Interes',
                                'Sensibilidad', 'InteresDevengado', 'Id_Key_Cartera']

        col_flujos_nosensibles = ['Fecha', 'Fondo', 'Tipo', 'ID', 'ActivoPasivo',
                                  'FechaFlujoNoSensible', 'Moneda', 'FlujoNoSensible', 'Id_Key_Cartera']

        flujos_derivados = pd.DataFrame(columns=col_flujos_derivados)

        flujos_nosensibles = pd.DataFrame(columns=col_flujos_nosensibles)
        c = 0
        for i in flujos_v:
            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fecha, fondo, 'IBR', id,
                                                                     -factor_recibo_fijo, i[0], i[0],
                                                                     i[2], moneda, i[1]/100*nocional,
                                                                     i[3]/100 * nocional,
                                                                     i[4]/100*nocional, i[5] / 100 * nocional,
                                                                     i[6] / 100 * nocional, id_key]],
                                                                    columns=col_flujos_derivados))

        flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fecha, fondo, 'IBR', id,
                                                                     -factor_recibo_fijo, max(fecha, fecha_efectiva),
                                                                     moneda, ibr_acum*nocional, id_key]],
                                                                    columns=col_flujos_nosensibles))

        for i in flujos_f:
            flujo_fijo = i[1] / 100 * nocional
            amortizacion = i[3] / 100 * nocional
            interes_fijo = i[4] / 100 * nocional
            fecha_flujo_f = i[0]
            devengo = i[6] / 100 * nocional
            fecha_pago = siguiente_habil_paises(add_days(fecha_flujo_f, -1), paises_feriados, cn)

            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fecha, fondo, 'IBR', id,
                                                                     factor_recibo_fijo, fecha_flujo_f, fecha_flujo_f,
                                                                     fecha_pago, moneda, flujo_fijo, amortizacion,
                                                                     interes_fijo, 0, devengo, id_key]],
                                                                    columns=col_flujos_derivados))

            flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fecha, fondo, 'IBR', id,
                                                                         factor_recibo_fijo, fecha_flujo_f, moneda,
                                                                         flujo_fijo, id_key]],
                                                                        columns=col_flujos_nosensibles))

        self.flujos_nosensibles = flujos_nosensibles
        self.flujos_derivados = flujos_derivados
        self.set_status("INFO: Flujos generados para IBR con ID " + str(self.info_cartera.ID.iloc[0]))

