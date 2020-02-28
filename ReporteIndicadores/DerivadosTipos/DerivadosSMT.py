# -*- coding: utf-8 -*-
from Derivados.DerivadosAbstracto import *
from UtilesDerivados import cast_frecuencia, delta_frecuencia, ultimo_habil_pais, proyectar_flujos_tabla, \
    siguiente_habil_paises
from UtilesValorizacionIndicadores import factor_descuento
from UtilIndicadores import add_days

class DerivadosSMT(DerivadosAbstracto):

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

        frecuencia = cast_frecuencia(self.info_cartera.FrecuenciaActivo[0])

        id_key = self.info_cartera.ID_Key[0]

        convencion = "ACT360"
        flujos_f = genera_flujos(max(fecha, fecha_efectiva), fecha_efectiva, fecha_venc, tasa, frecuencia, convencion)

        fecha_cupon = flujos_f[0][0]

        fecha_aux = delta_frecuencia(fecha_cupon, frecuencia, -1)
        fecha_aux = max(fecha_aux, fecha_efectiva)

        fecha_cupon_anterior = ultimo_habil_pais(fecha_aux, "MX", cn)

        flujos_v = proyectar_flujos_tabla(fecha, fecha, 1, hora, fecha_efectiva, fecha_venc, frecuencia, moneda, 0,
                                          "Local", ajuste_feriados, cn)

        if fecha >= fecha_cupon_anterior:
            tasaV = ("SELECT T.Valor FROM dbAlgebra.dbo.TdInfoTasas I "
                     "INNER JOIN dbAlgebra.dbo.TdTasas T "
                     "ON I.TickerCorto = T.Tasa "
                     "INNER JOIN (SELECT MAX(T.Fecha) AS Fecha FROM "
                     "dbAlgebra.dbo.TdInfoTasas I INNER JOIN "
                     "dbAlgebra.dbo.TdTasas T ON I.TickerCorto = T.Tasa "
                     "WHERE (T.SiValida = 1) AND (T.Hora = 'CIERRE') AND (I.TipoTasa = 'TIIE') "
                     "AND (I.MonedaActiva = 'MXN') AND (T.Fecha <= " + fecha_str(fecha_cupon_anterior) + ") "
                    "AND (I.Plazo = '28D')) F ON T.Fecha = F.Fecha "
                    "WHERE (T.SiValida = 1) AND (T.Hora = 'CIERRE') AND (I.TipoTasa = 'TIIE') "
                    "AND (I.MonedaActiva = 'MXN') AND (I.Plazo = '28D')")
            tasaV = pd.io.sql.read_sql(tasaV, cn)
            tasaV = tasaV.Valor[0]

            cupon = (1/factor_descuento(tasaV/100, fecha_cupon_anterior, fecha_cupon, "ACT360", 0)-1) * 100

            devengo = cupon * (fecha_cupon_anterior-fecha).days / (fecha_cupon_anterior-fecha_cupon).days

            fecha_flujo_variable = fecha_cupon

            fecha_pago = siguiente_habil_paises(add_days(fecha_flujo_variable, -1), paises_feriados, cn)

            flujos_v[0][0] = fecha_flujo_variable

            flujos_v[0][1] = cupon
            flujos_v[0][2] = fecha_pago
            flujos_v[0][3] = 0
            flujos_v[0][4] = cupon
            flujos_v[0][5] = 0
            flujos_v[0][6] = devengo

            fecha_FNS = fecha_flujo_variable
            flujo_FNS = nocional * ((cupon/100)+1)

        else:
            fecha_FNS = fecha_cupon_anterior
            flujo_FNS = nocional

        col_flujos_derivados = ['Fecha', 'Administradora', 'Fondo', 'Contraparte', 'Tipo', 'ID', 'ActivoPasivo',
                                'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo', 'Amortizacion', 'Interes',
                                'Sensibilidad', 'InteresDevengado', 'Id_Key_Cartera']

        col_flujos_nosensibles = ['Fecha', 'Administradora', 'Fondo', 'Contraparte', 'Tipo', 'ID', 'ActivoPasivo',
                                  'FechaFlujoNoSensible', 'Moneda', 'FlujoNoSensible', 'Id_Key_Cartera']

        flujos_derivados = pd.DataFrame(columns=col_flujos_derivados)

        flujos_nosensibles = pd.DataFrame(columns=col_flujos_nosensibles)

        for i in flujos_v:
            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SMT', id,
                                                                      -factor_recibo_fijo, i[0], i[0],
                                                                      i[2], moneda, i[1] / 100 * nocional,
                                                                      i[3] / 100 * nocional,
                                                                      i[4] / 100 * nocional, i[5] / 100 * nocional,
                                                                      i[6] / 100 * nocional, id_key]],
                                                                    columns=col_flujos_derivados))

        flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SMT', id,
                                                                      -factor_recibo_fijo, fecha_FNS,
                                                                      moneda,
                                                                      flujo_FNS, id_key]],
                                                                    columns=col_flujos_nosensibles))

        for i in flujos_f:
            flujo_fijo = i[1] / 100 * nocional
            amortizacion = i[3] / 100 * nocional
            interes_fijo = i[4] / 100 * nocional
            fecha_flujo_f = i[0]
            devengo = i[6] / 100 * nocional
            fecha_pago = siguiente_habil_paises(add_days(fecha_flujo_f, -1), paises_feriados, cn)

            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SMT', id,
                                                                     factor_recibo_fijo, fecha_flujo_f, fecha_flujo_f,
                                                                     fecha_pago, moneda, flujo_fijo, amortizacion,
                                                                     interes_fijo, 0, devengo, id_key]],
                                                                    columns=col_flujos_derivados))

            flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SMT', id,
                                                                         factor_recibo_fijo, fecha_flujo_f, moneda,
                                                                         flujo_fijo, id_key]],
                                                                        columns=col_flujos_nosensibles))

            self.flujos_nosensibles = flujos_nosensibles
            self.flujos_derivados = flujos_derivados

        self.set_status("INFO: Flujos generados para SMT con ID " + str(self.info_cartera.ID.iloc[0]))
