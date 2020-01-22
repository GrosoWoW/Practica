# -*- coding: utf-8 -*-
import sys
sys.path.append("..")

from Derivados.DerivadosTipos.DerivadosAbstracto import *
from Derivados.LibreriasUtiles.Util import fecha_str, add_days
from Derivados.LibreriasUtiles.UtilesDerivados import ultimo_habil_paises, siguiente_habil_paises, ultimo_habil_pais, genera_flujos, proyectar_flujos_tabla
from Derivados.LibreriasUtiles.UtilesDerivados import cast_frecuencia, delta_frecuencia
from Derivados.LibreriasUtiles.UtilesDerivados import ultimo_habil_paises, siguiente_habil_paises
from Derivados.LibreriasUtiles.Util import add_days, send_msg
import datetime
import numpy as np


class DerivadosFWD(DerivadosAbstracto):
    
    def revisar_input(self):
        info_cartera = self.info_cartera
        if not ('Fondo' in info_cartera.columns and isinstance(info_cartera.Fondo[0],str)):
            info_cartera["Fondo"] = "Fondo"
        
        if  not ('ID' in info_cartera.columns and not isinstance(info_cartera.ID[0],str) and np.isnan(info_cartera.ID[0]) == False):
            send_msg("ERROR: Falta ingresar columna 'ID'", self.filename)
        
        if not ('FechaVenc' in info_cartera.columns and isinstance(info_cartera.FechaVenc[0],str)):
            send_msg("ERROR: Falta ingresar columna 'FechaVenc'", self.filename)
        
        if not ('FechaFixing' in info_cartera.columns and isinstance(info_cartera.FechaFixing[0],str)):
            info_cartera["FechaFixing"] = info_cartera["FechaVenc"].iloc[0]
            
        if not ('NocionalActivo' in info_cartera.columns and not isinstance(info_cartera.NocionalActivo[0],str) and np.isnan(info_cartera.NocionalActivo[0]) == False):
            send_msg("ERROR: No viene la columna 'NocionalActivo'", self.filename)
            
        if not ('NocionalPasivo' in info_cartera.columns and not isinstance(info_cartera.NocionalPasivo[0],str) and np.isnan(info_cartera.NocionalPasivo[0]) == False):
            send_msg("ERROR: No viene la columna 'NocionalPasivo'", self.filename)
            
        if not ('MonedaActivo' in info_cartera.columns and isinstance(info_cartera.MonedaActivo[0],str)):
            send_msg("ERROR: No viene la columna 'MonedaActivo'", self.filename)
            
        if not ('MonedaPasivo' in info_cartera.columns and isinstance(info_cartera.MonedaPasivo[0],str)):
            send_msg("ERROR: No viene la columna 'MonedaPasivo'", self.filename)
            
        self.info_cartera = info_cartera
        
    def genera_flujos(self):
        fondo = self.info_cartera.Fondo[0]

        id = self.info_cartera.ID[0]

        fecha_fixing = pd.to_datetime(datetime.datetime.strptime(self.info_cartera.FechaFixing[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date()
        fecha_venc = pd.to_datetime(datetime.datetime.strptime(self.info_cartera.FechaVenc[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date()



        ajuste_feriados = self.info_cartera.AjusteFeriados[0]
        paises_feriados = ajuste_feriados.split(',')

        nocional_act = self.info_cartera.NocionalActivo[0]
        nocional_pas = self.info_cartera.NocionalPasivo[0]


        fecha_fixing_ajustada = ultimo_habil_paises(fecha_fixing, paises_feriados, self.cn)
        fecha_pago = siguiente_habil_paises(add_days(fecha_venc, -1), paises_feriados, self.cn)

        moneda_act = self.info_cartera.MonedaActivo[0]
        moneda_pas = self.info_cartera.MonedaPasivo[0]

        col_flujos_derivados = ['Fecha', 'Fondo', 'Tipo', 'ID', 'ActivoPasivo',
                                'FechaFixing', 'FechaFlujo', 'FechaPago', 'Moneda', 'Flujo', 'Amortizacion', 'Interes']

        # Se inserta activopasivo = 1
        self.flujos_derivados = self.flujos_derivados.append(pd.DataFrame([[self.fechaActual, fondo,
                                                                            'FWD', id, 1, fecha_fixing_ajustada,
                                                                            fecha_venc, fecha_pago, moneda_act,
                                                                            nocional_act, nocional_act,
                                                                            0]], columns=col_flujos_derivados),sort='False')
        # Se inserta activopasivo = -1
        self.flujos_derivados = self.flujos_derivados.append(pd.DataFrame([[self.fechaActual, fondo,
                                                                            'FWD', id, -1,
                                                                            fecha_fixing_ajustada,
                                                                            fecha_venc, fecha_pago, moneda_pas,
                                                                            nocional_pas, nocional_pas,
                                                                            0]], columns=col_flujos_derivados),sort='False')

        self.flujos_nosensibles = self.flujos_nosensibles.append(pd.DataFrame([[self.fechaActual, fondo,
                                                                                'FWD', id, 1,
                                                                                fecha_venc, moneda_act, nocional_act]],
                                                                              columns=self.col_flujos_nosensibles),sort='False')

        self.flujos_nosensibles = self.flujos_nosensibles.append(pd.DataFrame([[self.fechaActual, fondo,
                                                                                'FWD', id, -1,
                                                                                fecha_venc, moneda_pas, nocional_pas]],
                                                                              columns=self.col_flujos_nosensibles),sort='False')

        self.set_status("INFO: Flujos generados para FWD con ID " + str(self.info_cartera.ID.iloc[0]))
