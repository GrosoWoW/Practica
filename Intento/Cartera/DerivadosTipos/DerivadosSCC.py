# -*- coding: utf-8 -*-
import sys

sys.path.append("..")
from DerivadosTipos.DerivadosAbstracto import *
from Util import fecha_str, add_days
import datetime
from UtilesDerivados import ultimo_habil_paises, siguiente_habil_paises, ultimo_habil_pais, genera_flujos, proyectar_flujos_tabla
from UtilesDerivados import cast_frecuencia, delta_frecuencia
import numpy as np

class DerivadosSCC(DerivadosAbstracto):
    
    def revisar_input(self):

        info_cartera = self.info_cartera
        if not ('Fondo' in info_cartera.columns and isinstance(info_cartera.Fondo[0],str)):
            info_cartera["Fondo"] = "Fondo"
        
        if  not ('ID' in info_cartera.columns and not isinstance(info_cartera.ID[0],str) and np.isnan(info_cartera.ID[0]) == False):
            send_msg("ERROR: Falta ingresar columna 'ID'", self.filename)
        
        if not ('FechaVenc' in info_cartera.columns and isinstance(info_cartera.FechaVenc[0],str)):
            send_msg("ERROR: Falta ingresar columna 'FechaVenc'", self.filename)
        
        if not ('FechaEfectiva' in info_cartera.columns and isinstance(info_cartera.FechaEfectiva[0],str)):
            send_msg("ERROR: Falta ingresar columna 'FechaEfectiva'", self.filename)
            
        if not ('FrecuenciaActivo' in info_cartera.columns and isinstance(info_cartera.FrecuenciaActivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'FrecuenciaActivo'", self.filename)
        
        if not ('TipoTasaActivo' in info_cartera.columns and isinstance(info_cartera.TipoTasaActivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'TipoTasaActivo'", self.filename)
        
        if not ('NocionalActivo' in info_cartera.columns and not isinstance(info_cartera.NocionalActivo[0],str) and np.isnan(info_cartera.NocionalActivo[0]) == False):
            send_msg("ERROR: No viene la columna 'NocionalActivo'", self.filename)
        
        
        if info_cartera.TipoTasaActivo[0][:4] == "Fija":
            
            if not ('TasaActivo' in info_cartera.columns and not isinstance(info_cartera.TasaActivo[0],str) and np.isnan(info_cartera.TasaActivo[0]) == False):
                send_msg("ERROR: No viene la columna 'TasaActivo' y 'TipoTasaActivo' es Fija", self.filename)
        
        else:
            if not ('TasaPasivo' in info_cartera.columns and not isinstance(info_cartera.TasaPasivo[0],str) and np.isnan(info_cartera.TasaPasivo[0]) == False):
                send_msg("ERROR: No viene la columna 'TasaPasivo' y 'TipoTasaActivo' no es Fija", self.filename)

        info_cartera.MonedaActivo[0] = "CLP"        
            
        self.info_cartera = info_cartera

    def genera_flujos(self):
        hora = self.hora
        cn = self.cn
        fechaActual = self.fechaActual
        fechaValores = self.fechaValores


        fondo = self.info_cartera.Fondo[0]
        id = self.info_cartera.ID[0]

        
        fecha_efectiva = pd.to_datetime(datetime.datetime.strptime(self.info_cartera.FechaEfectiva[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date()
        fecha_venc = pd.to_datetime(pd.to_datetime(datetime.datetime.strptime(self.info_cartera.FechaVenc[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date()).date()

        ajuste_feriados = self.info_cartera.AjusteFeriados[0]
        paises_feriados = ajuste_feriados.split(',')

        moneda = self.info_cartera.MonedaActivo[0]

        if self.info_cartera.TipoTasaActivo[0] == 'Fija':
            factor_recibo_fijo = 1
            tasa = self.info_cartera.TasaActivo[0]
        else:
            factor_recibo_fijo = -1
            tasa = self.info_cartera.TasaPasivo[0]

        #tasa = float(tasa.replace(",","."))
        nocional = self.info_cartera.NocionalActivo[0]

        frecuencia = cast_frecuencia(self.info_cartera.FrecuenciaActivo[0])


        if frecuencia == cast_frecuencia("Semi annual"):
            convencion = "ACT360"
        else:
            convencion = "LACT360"

        flujos_f = genera_flujos(max(fechaActual, fecha_efectiva), fecha_efectiva, fecha_venc, tasa, frecuencia, convencion)

        fecha_cupon = flujos_f[0][0]

        fecha_aux = delta_frecuencia(fecha_cupon, frecuencia, -1)
        fecha_aux = max(fecha_aux, fecha_efectiva)
        fecha_cupon_anterior = ultimo_habil_pais(fecha_aux, "CL", cn)
        if fechaActual < fecha_cupon_anterior:
            vpv = 1
        else:
            vpv = ("SELECT ICP1.ICP / ICP0.ICP AS Cupon FROM (SELECT ICP FROM dbAlgebra.dbo.TdIndicadores "
                   "WHERE (Fecha = " + fecha_str(fechaValores) + ")) ICP1 CROSS JOIN ("
                                                           "SELECT ICP FROM dbAlgebra.dbo.TdIndicadores "
                                                           "WHERE (Fecha = " + fecha_str(fecha_cupon_anterior) + ")) "
                                                                                                            "ICP0")
            vpv = pd.io.sql.read_sql(vpv, cn)
            vpv = vpv.Cupon[0]
        flujos_v = proyectar_flujos_tabla(fechaActual, fechaValores, vpv, hora, fecha_efectiva, fecha_venc, frecuencia, moneda, 0,
                                          "Local", ajuste_feriados, cn)

        # Simulamos los insert a base de datos

        col_flujos_derivados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'ActivoPasivo',
                                'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo', 'Amortizacion', 'Interes',
                                'Sensibilidad', 'InteresDevengado']

        col_flujos_nosensibles = ['Fecha', 'Fondo', 'Tipo', 'ID', 'ActivoPasivo',
                                  'FechaFlujoNoSensible', 'Moneda', 'FlujoNoSensible']

        flujos_derivados = pd.DataFrame(columns=col_flujos_derivados)

        flujos_nosensibles = pd.DataFrame(columns=col_flujos_nosensibles)
        for i in flujos_v:
            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fechaActual, fondo, 'SCC', id,
                                                                     -factor_recibo_fijo, i[0], i[0],
                                                                     i[2], moneda, i[1] / 100 * nocional,
                                                                     i[3] / 100 * nocional,
                                                                     i[4] / 100 * nocional, i[5] / 100 * nocional,
                                                                     i[6] / 100 * nocional]],
                                                                    columns=col_flujos_derivados))

        flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fechaActual, fondo, 'SCC', id,
                                                                     -factor_recibo_fijo, max(fechaActual, fecha_efectiva), moneda,
                                                                     vpv * nocional]],
                                                                    columns=col_flujos_nosensibles))

        for i in flujos_f:
            flujo_fijo = i[1] / 100 * nocional
            amortizacion = i[3] / 100 * nocional
            interes_fijo = i[4] / 100 * nocional
            fecha_flujo_f = i[0]
            devengo = i[6] / 100 * nocional
            fecha_pago = siguiente_habil_paises(add_days(fecha_flujo_f, -1), paises_feriados, cn)
            test = pd.DataFrame([fecha_flujo_f], columns=["fech"])
            flujos_derivados = flujos_derivados.append(pd.DataFrame([[fechaActual, fondo, 'SCC', id,
                                                                     factor_recibo_fijo, fecha_flujo_f, fecha_flujo_f,
                                                                     fecha_pago, moneda, flujo_fijo, amortizacion,
                                                                     interes_fijo, 0, devengo]],
                                                                    columns=col_flujos_derivados))

            flujos_nosensibles = flujos_nosensibles.append(pd.DataFrame([[fechaActual, fondo, 'SCC', id,
                                                                         factor_recibo_fijo, fecha_flujo_f, moneda,
                                                                         flujo_fijo]],
                                                                        columns=col_flujos_nosensibles))

        self.flujos_nosensibles = flujos_nosensibles
        self.flujos_derivados = flujos_derivados
        self.set_status("INFO: Flujos generados para SCC con ID " + str(self.info_cartera.ID.iloc[0]))
