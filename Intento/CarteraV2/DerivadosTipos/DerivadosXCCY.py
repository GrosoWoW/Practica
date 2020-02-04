# -*- coding: utf-8 -*-
from Derivados.DerivadosAbstracto import *
from UtilesDerivados import ultimo_habil_paises, siguiente_habil_paises, cast_frecuencia, cast_convencion, \
    delta_frecuencia, ultimo_habil_pais
from Util import add_days
import datetime
from Curvas import curva_cero_swapUSD
from Curves.CurvaCero import curva_cero_CLP_TAB, curva_cero_CLP_libre_riesgo
import numpy as np
from Curves.FuncionesCurvas import parsear_curva


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
    tasaDV01 = (((fd_ini_DV01 / fd_fin_DV01) ** (360 / (plazo_fin - plazo_ini))) - 1) * 100 + spread / 100

    return [tasa, tasaDV01]


class DerivadosXCCY(DerivadosAbstracto):
    
    
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
            
        if not ('FrecuenciaPasivo' in info_cartera.columns and isinstance(info_cartera.FrecuenciaPasivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'FrecuenciaPasivo'", self.filename)
        
        if not ('TipoTasaActivo' in info_cartera.columns and isinstance(info_cartera.TipoTasaActivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'TipoTasaActivo'", self.filename)
            
        if not ('TipoTasaPasivo' in info_cartera.columns and isinstance(info_cartera.TipoTasaPasivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'TipoTasaPasivo'", self.filename)
        
        if not ('NocionalActivo' in info_cartera.columns and not isinstance(info_cartera.NocionalActivo[0],str) and np.isnan(info_cartera.NocionalActivo[0]) == False):
            send_msg("ERROR: No viene la columna 'NocionalActivo'", self.filename)
            
        if not ('NocionalPasivo' in info_cartera.columns and not isinstance(info_cartera.NocionalPasivo[0],str) and np.isnan(info_cartera.NocionalPasivo[0]) == False):
            send_msg("ERROR: No viene la columna 'NocionalPasivo'", self.filename)
            
        if not ('SpreadActivo' in info_cartera.columns):
            info_cartera.SpreadActivo[0] = 0
            
        elif isinstance(info_cartera.SpreadActivo[0], str) or np.isnan(info_cartera.SpreadActivo[0]) == True:
            send_msg("ERROR: Valor en la columna 'SpreadActivo' no es un numero", self.filename)
        
        if not ('SpreadPasivo' in info_cartera.columns):
            info_cartera.SpreadPasivo[0] = 0
            
        elif isinstance(info_cartera.SpreadPasivo[0], str) or np.isnan(info_cartera.SpreadPasivo[0]) == True:
            send_msg("ERROR: Valor en la columna 'SpreadPasivo' no es un numero", self.filename)
        
        
        if info_cartera.TipoTasaActivo[0][:4] == "Fija":
            
            if not ('TasaActivo' in info_cartera.columns and not isinstance(info_cartera.TasaActivo[0],str) and np.isnan(info_cartera.TasaActivo[0]) == False):
                send_msg("ERROR: No viene la columna 'TasaActivo' y 'TipoTasaActivo' es Fija", self.filename)
        
        if info_cartera.TipoTasaPasivo[0][:4] == "Fija":
            if not ('TasaPasivo' in info_cartera.columns and not isinstance(info_cartera.TasaPasivo[0],str) and np.isnan(info_cartera.TasaPasivo[0]) == False):
                send_msg("ERROR: No viene la columna 'TasaPasivo' y 'TipoTasaActivo' no es Fija", self.filename)

        if not ('MonedaActivo' in info_cartera.columns and isinstance(info_cartera.MonedaActivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'MonedaActivo'", self.filename)   
        
        if not ('MonedaPasivo' in info_cartera.columns and isinstance(info_cartera.MonedaPasivo[0],str)):
            send_msg("ERROR: Falta ingresar columna 'MonedaPasivo'", self.filename)
        
        self.info_cartera = info_cartera

    
    
    
    def genera_flujos(self):
        info = dict()
        # Se sacan los datos para generar flujos
        info["Fecha"] = self.fechaActual
        info["Fondo"] = self.info_cartera.Fondo[0]
        info["Tipo"] = "XCCY"
        info["ID"] = self.info_cartera.ID[0]
        info["FechaEfectiva"] = pd.to_datetime(datetime.datetime.strptime(self.info_cartera.FechaEfectiva.iloc[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date()
        info["FechaVenc"] = pd.to_datetime(datetime.datetime.strptime(self.info_cartera.FechaVenc.iloc[0].split(" ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")).date()
        info["AjusteFeriados"] = self.info_cartera.AjusteFeriados[0]

        
        # Datos para la parte activa

        info["ActivoPasivo"] = 1
        info["Moneda"] = self.info_cartera.MonedaActivo[0]
        info["TipoTasa"] = self.info_cartera.TipoTasaActivo[0]
        info["Nocional"] = self.info_cartera.NocionalActivo[0]
        info["Frecuencia"] = cast_frecuencia(self.info_cartera.FrecuenciaActivo[0])
        info["Tasa"] = self.info_cartera.TasaActivo[0]
        info["Spread"] = self.info_cartera.SpreadActivo[0]

        self.genera_flujos_aux(info)

        # Datos para la parte pasiva

        info["ActivoPasivo"] = -1
        info["Moneda"] = self.info_cartera.MonedaPasivo[0]
        info["TipoTasa"] = self.info_cartera.TipoTasaPasivo[0]
        info["Nocional"] = self.info_cartera.NocionalPasivo[0]
        info["Frecuencia"] = cast_frecuencia(self.info_cartera.FrecuenciaPasivo[0])
        info["Tasa"] = self.info_cartera.TasaPasivo[0]
        info["Spread"] = self.info_cartera.SpreadPasivo[0]
        
        self.genera_flujos_aux(info)
        self.set_status("INFO: Flujos generados para XCCY con ID " + str(self.info_cartera.ID.iloc[0]))


    def genera_flujos_aux(self, info):
        cn = self.cn
        fechaActual = self.fechaActual
        fechaValores = self.fechaValores
        hora_insert = "--"
        fondo = info["Fondo"]
        id = info["ID"]
        fecha_efectiva = info["FechaEfectiva"]
        fecha_venc = info["FechaVenc"]
        ajuste_feriados = info["AjusteFeriados"]
        paises_feriados = ajuste_feriados.split(",")

        activo_pasivo = info["ActivoPasivo"]
        moneda = info["Moneda"]
        tipo_tasa = info["TipoTasa"]
        tasa = info["Tasa"]
        spread = info["Spread"]
        frecuencia = info["Frecuencia"]
        nocional = info["Nocional"]

        flujos_f_DV01 = -1000

        if tipo_tasa[0:4] == "Fija":
            if len(tipo_tasa) == 4:
                convencion = "30/360"

            else:
                convencion = cast_convencion(tipo_tasa[-5:])
                if convencion == "":
                    convencion = "30/360"
            #Conversion a float
            
            flujos_f = genera_flujos(max(fechaActual, fecha_efectiva), fecha_efectiva, fecha_venc, tasa + spread/100,
                                     frecuencia, convencion)


            for i in flujos_f:
                i[0] = siguiente_habil_paises(add_days(i[0], -1), paises_feriados, cn)
            flujos_f_ns = np.array(flujos_f)

        elif moneda == "USD":
            hora_insert = self.hora
            
            arr_factor_descuento = ("SELECT Curva FROM dbDerivados.dbo.TdCurvasDerivados "
                                    "WHERE Hora = '" + hora_insert + "' AND Fecha = " + fecha_str(fechaValores) + " AND Tipo = 'CurvaCero_SwapUSD_V2_6M'")

            arr_factor_descuento = pd.io.sql.read_sql(arr_factor_descuento, cn).Curva.iloc[0]
            
            arr_factor_descuento = parsear_curva(arr_factor_descuento)
            
            fecha_aux = add_days(max(fechaActual, fecha_efectiva), -1)
            fecha_aux = add_days(ultimo_habil_paises(fecha_aux, paises_feriados, cn), 1)

            flujos_f = genera_flujos(fecha_aux, fecha_efectiva, fecha_venc, 0, frecuencia, "ACT360")
            flujos_f_DV01 = np.array(flujos_f)
            flujos_f_ns = np.array(flujos_f)
            
            
            for j in range(len(flujos_f)):
                fecha_anterior = delta_frecuencia(flujos_f[j][0], frecuencia, -1)

                fecha_fijacion_libor = ultimo_habil_pais(add_days(ultimo_habil_pais(add_days(fecha_anterior, -1), "UK",
                                                                                    cn), -1), "UK", cn)

                fecha_fijacion_libor_siguiente = ultimo_habil_pais(add_days(ultimo_habil_pais(add_days(flujos_f[j][0],
                                                                                                       -1), "UK", cn),
                                                                            -1), "UK", cn)
                
                flujos_f[j][0] = siguiente_habil_paises(add_days(flujos_f[j][0], -1), paises_feriados, cn)
                flujos_f_DV01[j][0] = flujos_f[j][0]
                flujos_f_ns[j][0] = flujos_f[j][0]
				

                max_fecha_libor = ("SELECT Max(T.Fecha) as FechaMax "
                                   "FROM dbAlgebra.dbo.TdInfoTasas I "
                                   "INNER JOIN dbAlgebra.dbo.TdTasas T "
                                   "ON I.TickerCorto = T.Tasa WHERE (T.SiValida = 1) "
                                   "AND (T.Hora = 'CIERRE') "
                                   "AND (I.Plazo = '" + frecuencia + "') "
                                                                     "AND (I.TipoTasa = 'LIBOR') "
                                                                     "AND (I.MonedaActiva = 'USD') "
                                                                     "AND (T.Fecha <= " + fecha_str(fecha_fijacion_libor) + ")")
																	 
                max_fecha_libor = pd.io.sql.read_sql(max_fecha_libor, cn).FechaMax.iloc[0].to_pydatetime().date()
                if fecha_fijacion_libor <= fechaActual:
                    libor = ("SELECT T.Valor "
                             "FROM dbAlgebra.dbo.TdInfoTasas I "
                             "INNER JOIN dbAlgebra.dbo.TdTasas T "
                             "ON I.TickerCorto = T.Tasa "
                             "WHERE (T.SiValida = 1) AND (T.Hora = 'CIERRE') "
                             "AND (I.Plazo = '" + frecuencia + "') AND (I.TipoTasa = 'LIBOR') "
                                                               "AND (I.MonedaActiva = 'USD') "
                                                               "AND (T.Fecha = " + fecha_str(max_fecha_libor) + ") ORDER BY I.Plazo360")

                    libor = pd.io.sql.read_sql(libor, cn).Valor.iloc[0]

                    tasa = libor + spread/100
                    tasa_DV01 = tasa

                    if fecha_fijacion_libor_siguiente > fechaActual or len(flujos_f) == j:
                        flujos_f_ns[j][1] = 100 + tasa * (flujos_f_ns[j][0] - fecha_anterior).days/360
                        flujos_f[j][6] = tasa * ((flujos_f[j][0] - fecha_anterior).days) / 360 * (fechaActual-fecha_anterior).days / (flujos_f[j][0] - fecha_anterior).days

                    else:
                        flujos_f_ns[j][1] = tasa * (flujos_f_ns[j][0] - fecha_anterior).days / 360
                        flujos_f[j][6] = 0
                else:
                    plazo_ini = (fecha_fijacion_libor - fechaActual).days
                    plazo_fin = (fecha_fijacion_libor_siguiente - fechaActual).days

                    tasa_arr = tasa_FRA_y_tasa_DV01(plazo_ini, plazo_fin, spread, arr_factor_descuento)
                    tasa = tasa_arr[0]
                    tasa_DV01 = tasa_arr[1]

                    flujos_f_ns[j][1] = (spread / 100) * (flujos_f_ns[j][0] - fecha_anterior).days / 360
                    flujos_f[j][6] = 0

                flujos_f[j][1] += tasa * (flujos_f[j][0] - fecha_anterior).days / 360
                flujos_f[j][4] = tasa * (flujos_f[j][0] - fecha_anterior).days / 360

                flujos_f_DV01[j][1] += tasa_DV01 * (flujos_f_DV01[j][0] - fecha_anterior).days / 360

        elif moneda == "CLP":
            hora_insert = self.hora
            if tipo_tasa == "Flotante_Tab30dNom" or tipo_tasa == "Flotante_Tab":
                arr_factor_descuento = curva_cero_CLP_TAB(fechaValores, hora_insert, cn)

                fecha_aux = add_days(max(fechaActual, fecha_efectiva), -1)
                fecha_aux = add_days(ultimo_habil_paises(fecha_aux, paises_feriados, cn), 1)

                flujos_f = genera_flujos(fecha_aux, fecha_efectiva, fecha_venc, 0, frecuencia, "ACT360")

                flujos_f_DV01 = np.array(flujos_f)
                flujos_f_ns = np.array(flujos_f)

                for j in range(len(flujos_f)):
                    if j == 0:
                        fecha_anterior = delta_frecuencia(flujos_f[j][0], frecuencia, -1)
                    else:
                        fecha_anterior = flujos_f[j-1][0]

                    fecha_fijacion_tab = ultimo_habil_pais(
                        add_days(ultimo_habil_pais(add_days(fecha_anterior, -1), "CL",
                                                   cn), -1), "CL", cn)

                    fecha_fijacion_tab_siguiente = ultimo_habil_pais(
                        add_days(ultimo_habil_pais(add_days(flujos_f[j][0],
                                                            -1), "CL", cn),
                                 -1), "CL", cn)

                    flujos_f[j][0] = siguiente_habil_paises(add_days(flujos_f[j][0], -1), paises_feriados, cn)
                    flujos_f_DV01[j][0] = flujos_f[j][0] # REVISAR
                    flujos_f_ns[j][0] = flujos_f[j][0]

                    if fecha_fijacion_tab <= fechaActual:
                        if frecuencia == "1M":
                            campo = "TabNominal30"
                        elif frecuencia == "3M":
                            campo = "TabNominal90"
                        elif frecuencia == "6M":
                            campo = "TabNominal180"
                        elif frecuencia == "1A":
                            campo = "TabNominal360"
                        else:
                            pass #TODO ERROR

                        tab = ("SELECT Top 1 " + campo + " FROM [dbAlgebra].[dbo].[TdIndicadores] "
                                "Where Fecha <= " + fecha_str(fecha_fijacion_tab) + " and " + campo + " <> -1000 Order by Fecha desc")

                        tab = pd.io.sql.read_sql(tab, cn)

                        tasa = tab + spread/100
                        tasa_DV01 = tasa

                        if fecha_fijacion_tab_siguiente > fechaActual or len(flujos_f) == j:
                            flujos_f_ns[j][1] = 100 + tasa * (flujos_f_ns[j][0] - fecha_anterior).days / 360
                            flujos_f[j][6] = tasa * ((flujos_f[j][0] - fecha_anterior).days / 360) * (fechaActual - fecha_anterior).days / (flujos_f[j][0] - fecha_anterior).days
                        else:
                            flujos_f_ns[j][1] = tasa * (flujos_f_ns[j][0] - fecha_anterior).days / 360
                            flujos_f[j][6] = 0

                    else:

                        plazo_ini = (fecha_fijacion_tab - fechaActual).days
                        plazo_fin = (fecha_fijacion_tab_siguiente - fechaActual).days

                        tasa_arr = tasa_FRA_y_tasa_DV01(plazo_ini, plazo_fin, spread, arr_factor_descuento)
                        tasa = tasa_arr[0]
                        tasa_DV01 = tasa_arr[1]

                        flujos_f_ns[j][1] = (spread / 100) * (flujos_f_ns[j][0] - fecha_anterior).days / 360
                        flujos_f[j][6] = 0

                    flujos_f[j][1] += tasa * (flujos_f[j][0] - fecha_anterior).days / 360
                    flujos_f[j][4] = tasa * (flujos_f[j][0] - fecha_anterior).days / 360

                    flujos_f_DV01[j][1] += tasa_DV01 * (flujos_f_DV01[j][0] - fecha_anterior).days / 360

            else:
                
                arr_factor_descuento = ("SELECT Curva FROM dbDerivados.dbo.TdCurvasDerivados "
                                    "WHERE Hora = '" + hora_insert + "' AND Fecha = " + fecha_str(fechaValores) + " AND Tipo = 'CurvaCero_CLP_LibreRiesgo'")
                arr_factor_descuento = pd.io.sql.read_sql(arr_factor_descuento, cn).Curva.iloc[0]
                arr_factor_descuento = parsear_curva(arr_factor_descuento)


                flujos_f = genera_flujos(max(fechaActual, fecha_efectiva), fecha_efectiva, fecha_venc, 0, frecuencia, "ACT360")

                flujos_f_DV01 = np.array(flujos_f)

                for j in range(len(flujos_f)):
                    fecha_IPC_inicial = delta_frecuencia(flujos_f[j][0], frecuencia, -1)
                    fecha_IPC_inicial = siguiente_habil_paises(fecha_IPC_inicial, paises_feriados, cn)

                    fecha_IPC_final = siguiente_habil_paises(flujos_f[j][0], paises_feriados, cn)

                    flujos_f[j][0] = fecha_IPC_final

                    flujos_f_DV01[j][0] = flujos_f[j][0]

                    plazo_ini = (fecha_IPC_inicial - fechaActual).days
                    plazo_fin = (fecha_IPC_final - fechaActual).days

                    if fecha_IPC_inicial <= fechaActual:
                        vpv = ("SELECT ICP1.ICP / ICP0.ICP AS Cupon FROM (SELECT ICP FROM dbAlgebra.dbo.TdIndicadores "
                               "WHERE (Fecha = " + fecha_str(fechaValores) + ")) ICP1 "
                                "CROSS JOIN (SELECT ICP FROM dbAlgebra.dbo.TdIndicadores "
                                    "WHERE (Fecha = " + fecha_str(fecha_IPC_inicial) + ")) ICP0")

                        vpv = pd.io.sql.read_sql(vpv, cn).Cupon.iloc[0]
                        tasa = ((vpv/interpolacion_log_escalar(plazo_fin, arr_factor_descuento[1:])) ** (360/(plazo_fin-plazo_ini)) -1) * 100 + spread/100

                        tasa_DV01 = tasa

                        if fechaActual < fecha_IPC_final:
                            flujos_f_ns = [[fechaActual, vpv * 100]]

                        flujos_f[j][6] = tasa * ((flujos_f[j][0] - fecha_IPC_inicial).days / 360) * (
                                    fechaActual - fecha_IPC_inicial).days / (flujos_f[j][0] - fecha_IPC_inicial).days


                    else:
                        tasa_arr = tasa_FRA_y_tasa_DV01(plazo_ini, plazo_fin, spread, arr_factor_descuento)
                        tasa = tasa_arr[0]
                        tasa_DV01 = tasa_arr[1]
                        flujos_f_ns = [[fecha_IPC_inicial, 100]]
                        flujos_f[j][6] = 0

                    flujos_f[j][1] += tasa * (flujos_f[j][0] - fecha_IPC_inicial).days / 360
                    flujos_f[j][4] = tasa * (flujos_f[j][0] - fecha_IPC_inicial).days / 360

                    flujos_f_DV01[j][1] += tasa_DV01 * (flujos_f_DV01[j][0] - fecha_IPC_inicial).days / 360

        else:
            send_msg("ERROR: Moneda '" + moneda + "' no soportada para tasa flotante", self.filename)

        
        if fecha_efectiva >= fechaActual:

            flujos_f = np.append([[fecha_efectiva, -100, fecha_efectiva, -100, 0, 0, 0]], flujos_f, axis=0)

            if type(flujos_f_DV01) != int:
                flujos_f_DV01 = np.append([[fecha_efectiva, -100, fecha_efectiva, -100, 0, 0, 0]], flujos_f_DV01, axis=0)


        insert = dict()
        insert["Fecha"] = fechaActual
        insert["Fondo"] = fondo
        insert["Tipo"] = "XCCY"
        insert["ID"] = id
        insert["Hora"] = hora_insert
        insert["ActivoPasivo"] = activo_pasivo
        insert["Moneda"] = moneda
        
        for j in range(len(flujos_f)):
            insert["Flujo"] = flujos_f[j][1] / 100 * nocional
            insert["Amortizacion"] = flujos_f[j][3] / 100 * nocional
            insert["Interes"] = flujos_f[j][4] / 100 * nocional
            insert["FechaFixing"] = flujos_f[j][0]
            insert["FechaFlujo"] = flujos_f[j][0]
            insert["FechaPago"] = flujos_f[j][0]
            insert["InteresDevengado"] = flujos_f[j][6] / 100 * nocional


            try:
                insert["Sensibilidad"] = (flujos_f_DV01[j][1] - flujos_f[j][1]) / 100 * nocional
            except:
                insert["Sensibilidad"] = 0

            self.flujos_derivados = self.flujos_derivados.append(insert, ignore_index=True)

        insert = dict()
        insert["Fecha"] = fechaActual
        insert["Fondo"] = fondo
        insert["Tipo"] = "XCCY"
        insert["ID"] = id
        insert["ActivoPasivo"] = activo_pasivo
        insert["Moneda"] = moneda

        for j in range(len(flujos_f_ns)):
            insert["FlujoNoSensible"] = flujos_f_ns[j][1] / 100 * nocional
            insert["FechaFlujoNoSensible"] = flujos_f_ns[j][0]

            self.flujos_nosensibles = self.flujos_nosensibles.append(insert, ignore_index=True)













