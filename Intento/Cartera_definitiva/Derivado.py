from Activo import Activo
import datetime
import pandas as pd
import numpy as np
from UtilesValorizacion import parsear_curva, diferencia_dias_convencion
from Matematica import interpolacion_log_escalar
from Util import add_days
import sys


class Derivado(Activo):

    def __init__(self, derivado_generico, monedaCartera, fecha_valorizacion, cn):

        super(Derivado, self).__init__(monedaCartera, fecha_valorizacion, cn)

        self.derivado_generico = derivado_generico
        self.derivado_generico.genera_flujos()
        self.derivado_generico.valoriza_flujos()

        self.distribucion_pivotes = np.zeros(len(self.get_plazos()))

    def get_derivado_generico(self):

        return self.derivado_generico

    def get_flujos(self):

        return self.get_derivado_generico().flujos_valorizados[["ID","ActivoPasivo", "Fecha"\
            , "FechaFixing", "FechaFlujo", "FechaPago", "Flujo", "ValorPresenteMonFlujo", "Moneda", "MonedaBase"]]

    def get_distribucion_pivotes(self):

        return self.distribucion_pivotes

    def seleccionar_curva_derivados(self, moneda, n, fecha=datetime.date(2018, 1, 22)):

        monedas = moneda
        cnn = self.get_cn()

        if moneda == "UF": #Funciona para el error de CLF
            monedas = "CLF"

        curva = ("SELECT TOP(" + str(n) + ")* FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+ str(monedas) +"' AND Hora = '1500' AND Fecha > '" + str(fecha) + "'")
        curva = pd.read_sql(curva, cnn)
        return curva


    def set_historico(self):

        n = 1000
        moneda = self.get_flujos()["Moneda"][0]
        curvas = self.seleccionar_curva_derivados(moneda, n)[::-1]

        largo = len(self.get_plazos())
        cantidad_curvas = len(curvas["Curva"])
        pivotes = self.get_plazos()

        matriz = np.zeros([cantidad_curvas, largo])

        # Por cada plazo
        for i in range(largo):
            
            # Por cada curva
            for j in range(cantidad_curvas):

                valor_dia = pivotes[i]
                curva = curvas["Curva"][j]
                fecha_curva = curvas["Fecha"][j]
                curva_parseada = parsear_curva(curva, fecha_curva)
                matriz[j][i] = interpolacion_log_escalar(int(valor_dia*360), curva_parseada)
                
        self.historicos = pd.DataFrame(matriz)

    def corregir_moneda(self):

        pass

    def monedas(self):

        flujos = self.get_flujos()["Moneda"]
        lenght = len(flujos)
        monedas = []

        for i in range(lenght):
            moneda_aux = flujos[i]
            
            if moneda_aux not in monedas:

                monedas.append(moneda_aux)

        return monedas

    def pedir_curva(self, moneda):

        cn = self.get_cn()

        fecha_valorizacion = self.get_fecha_valorizacion_date()
        curva = ("SELECT * FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+moneda+"' AND Fecha = '"+str(fecha_valorizacion)+"'")
        curva = pd.read_sql(curva, cn)
        curva = parsear_curva(curva["Curva"][0], fecha_valorizacion)
        return curva

    def buscar_pivote(self, fecha_pago):

        pivotes = self.get_plazos()
        largo_pivotes = len(pivotes)
        fecha_valorizacion = self.get_fecha_valorizacion_date()

        for i in range(largo_pivotes):

            pos_pivote = pivotes[i]
            
            fecha_pivote = add_days(fecha_valorizacion, int(pos_pivote*360))

            if i == 0 and fecha_pago < fecha_pivote:

                return [pivotes[i], pivotes[i]]

            elif fecha_pivote > fecha_pago:

                return [pivotes[i - 1], pivotes[i]]

    def coeficiente_peso(self, pivote1, pivote2, fecha_actual_flujo):

        fecha_valorizacion = self.get_fecha_valorizacion_date()

        fecha_pivote1 = add_days(fecha_valorizacion, int(pivote1*360))
        fecha_pivote2 = add_days(fecha_valorizacion, int(pivote2*360))
        
        numerador = diferencia_dias_convencion("ACT360", fecha_pivote1, fecha_actual_flujo)
        denominador = diferencia_dias_convencion("ACT360", fecha_pivote1 , fecha_pivote2)

        return numerador/denominador 

    def discrimador_sol(self, soluciones):

        for i in range(2):
            if 0 <= soluciones[i] and soluciones[i] <= 1:

                return soluciones[i]
        print("Javier, nos fallaste")
        return sys.exit(1) 


    def set_distribucion_pivotes(self):

        pivotes = self.get_plazos()
        flujos = self.get_flujos()

        fecha_valorizacion = self.get_fecha_valorizacion()
        fecha_valorizacion_date = self.get_fecha_valorizacion_date()
        fechas_pago = flujos["FechaFixing"]
        fechas_largo = len(fechas_pago)

        corr = self.get_correlacion()

        monedas_pagos = flujos["Moneda"]

        volatilidades = self.get_volatilidad().values

        distruciones = np.zeros(len(pivotes))

        for i in range(fechas_largo):

            fecha_pago_actual = fechas_pago[i]
            moneda_pago_actual = monedas_pagos[i]
            flujo_pago = flujos["Flujo"][i]


            pivote_entremedio = self.buscar_pivote(fecha_pago_actual)
            alfa = self.coeficiente_peso(pivote_entremedio[0], pivote_entremedio[1], fecha_pago_actual)

            indice_pivote1 = pivotes.index(pivote_entremedio[0])
            indice_pivote2 = pivotes.index(pivote_entremedio[1])

            volatilidad_inter = alfa*volatilidades[indice_pivote1][0] + (1 - alfa)*volatilidades[indice_pivote2][0]

            curva_parseada = self.pedir_curva(moneda_pago_actual)

            diferencia_dias = diferencia_dias_convencion("ACT360", fecha_valorizacion_date, fecha_pago_actual)
            factor_descuento = interpolacion_log_escalar(diferencia_dias, curva_parseada)
            valor_alfa = self.solucion_ecuacion(volatilidad_inter, volatilidades[indice_pivote1][0], volatilidades[indice_pivote2][0],\
                     corr[indice_pivote1][indice_pivote2] )

            solucion = self.discrimador_sol(valor_alfa)

            VP = factor_descuento*flujo_pago
    
            distruciones[indice_pivote1] += solucion*VP
            distruciones[indice_pivote2] += (1 - solucion)*VP

        self.distribucion_pivotes = (distruciones)


            










 

