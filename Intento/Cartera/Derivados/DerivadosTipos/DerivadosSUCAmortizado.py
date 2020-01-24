"""
Queda pendiente la amortización para genera_flujos y proyectar_flujos_Tabla
Además, en el contrato la fecha de pago corresponde a un día después de la fecha del flujo
"""
from Derivados.DerivadosAbstracto import *
from Util import fecha_str, add_days
from UtilesDerivados import siguiente_habil_paises, ultimo_habil_pais, genera_flujos, proyectar_flujos_tabla
from UtilesDerivados import delta_frecuencia, cast_frecuencia, factor_descuento


def genera_flujos(fecha, fecha_efectiva, fecha_venc, tasa, frecuencia, convencion, amortiza=True):
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
        i += 1
        fechai = delta_frecuencia(fechai, frecuencia, -1)

    if amortiza:
        for i in arr:
            i[3] += 100/len(arr)
            i[1] += 100/len(arr)

    arr.reverse()
    return arr



class DerivadosSUCAmortizado(DerivadosAbstracto):

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

        convencion = "LACT360"

        flujos_f = genera_flujos(max(fecha, fecha_efectiva), fecha_efectiva, fecha_venc, tasa, frecuencia, convencion)
        fecha_cupon = flujos_f[0][0]

        fecha_aux = delta_frecuencia(fecha_cupon, frecuencia, -1)
        fecha_aux = max(fecha_aux, fecha_efectiva)

        fecha_cupon_anterior = ultimo_habil_pais(fecha_aux, "CL", cn)

        if fecha < fecha_cupon_anterior:
            vpv = 1
        else:
            vpv = ("SELECT (ICP1.ICP / ICP0.ICP)/(ICP1.UF / ICP0.UF) AS Cupon FROM "
                   "(SELECT ICP, UF FROM dbAlgebra.dbo.TdIndicadores "
                   "WHERE (Fecha = " + fecha_str(fecha) + ")) ICP1 CROSS JOIN ("
                                                           "SELECT ICP, UF FROM dbAlgebra.dbo.TdIndicadores "
                                                           "WHERE (Fecha = " + fecha_str(fecha_cupon_anterior) + ")) "
                                                                                                                  "ICP0")
            vpv = pd.io.sql.read_sql(vpv, cn)
            vpv = vpv.Cupon[0]

        flujos_v = proyectar_flujos_tabla(fecha, fecha, vpv, hora, fecha_efectiva, fecha_venc, frecuencia, moneda, 0,
                                          "Local", ajuste_feriados, cn)
        # Simulamos los insert a base de datos

        col_flujos_derivados = ['Fecha', 'Administradora', 'Fondo', 'Contraparte', 'Tipo', 'ID', 'ActivoPasivo',
                                'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo', 'Amortizacion', 'Interes',
                                'Sensibilidad', 'InteresDevengado', 'Id_Key_Cartera']

        col_flujos_nosensibles = ['Fecha', 'Administradora', 'Fondo', 'Contraparte', 'Tipo', 'ID', 'ActivoPasivo',
                                  'FechaFlujoNoSensible', 'Moneda', 'FlujoNoSensible', 'Id_Key_Cartera']

        flujos_derivados = pd.DataFrame(columns=col_flujos_derivados)

        flujos_nosensibles = pd.DataFrame(columns=col_flujos_nosensibles)

        for i in flujos_v:
            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SUC', id,
                                                                      -factor_recibo_fijo, i[0], i[0],
                                                                      i[2], moneda, i[1] / 100 * nocional,
                                                                      i[3] / 100 * nocional,
                                                                      i[4] / 100 * nocional, i[5] / 100 * nocional,
                                                                      i[6] / 100 * nocional, id_key]],
                                                                    columns=col_flujos_derivados))

        flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SUC', id,
                                                                      -factor_recibo_fijo, max(fecha, fecha_efectiva),
                                                                      moneda,
                                                                      vpv * nocional, id_key]],
                                                                    columns=col_flujos_nosensibles))

        for i in flujos_f:
            flujo_fijo = i[1] / 100 * nocional
            amortizacion = i[3] / 100 * nocional
            interes_fijo = i[4] / 100 * nocional
            fecha_flujo_f = i[0]
            devengo = i[6] / 100 * nocional
            fecha_pago = siguiente_habil_paises(add_days(fecha_flujo_f, -1), paises_feriados, cn)

            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SUC', id,
                                                                     factor_recibo_fijo, fecha_flujo_f, fecha_flujo_f,
                                                                     fecha_pago, moneda, flujo_fijo, amortizacion,
                                                                     interes_fijo, 0, devengo, id_key]],
                                                                    columns=col_flujos_derivados))

            flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fecha, admin, fondo, contraparte, 'SUC', id,
                                                                         factor_recibo_fijo, fecha_flujo_f, moneda,
                                                                         flujo_fijo, id_key]],
                                                                        columns=col_flujos_nosensibles))

        self.flujos_nosensibles = flujos_nosensibles
        self.flujos_derivados = flujos_derivados
        self.set_status("INFO: Flujos generados para SUC con ID " + str(self.info_cartera.ID.iloc[0]))
