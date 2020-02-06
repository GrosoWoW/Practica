from Activo import Activo
import datetime
import pandas as pd
import numpy as np
from UtilesValorizacion import parsear_curva, diferencia_dias_convencion
from Matematica import interpolacion_log_escalar
from Util import add_days


class Derivado(Activo):

    def __init__(self, derivado_generico, monedaCartera, fecha_valorizacion, cn):

        super(Derivado, self).__init__(monedaCartera, fecha_valorizacion, cn)

        self.derivado_generico = derivado_generico
        self.derivado_generico.genera_flujos()
        self.derivado_generico.valoriza_flujos()



    def get_derivado_generico(self):

        return self.derivado_generico

    def get_flujos(self):

        return self.get_derivado_generico().flujos_valorizados[["ID","ActivoPasivo", "Fecha"\
            , "FechaFixing", "FechaFlujo", "FechaPago", "Flujo", "ValorPresenteMonFlujo", "Moneda", "MonedaBase"]]

    def seleccionar_curva_derivados(self, moneda, n, fecha=datetime.date(2018, 1, 22)):

        monedas = moneda
        cnn = self.get_cn()

        if moneda == "UF": #Funciona para el error de CLF
            monedas = "CLF"

        curva = ("SELECT TOP(" + str(n) + ")* FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+ str(monedas) +"' AND Hora = '1500' AND Fecha > '" + str(fecha) + "'")
        curva = pd.read_sql(curva, cnn)
        return curva


    def set_historico(self):

        n = 200
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
                matriz[j][i] = interpolacion_log_escalar(valor_dia, curva_parseada)
                
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

            
    def generar_diccionario_table(self, pivotes, fecha_valorizacion, monedas):

        lenght = len(monedas)
        diccionario = dict()
        for i in range(lenght):

            tabla = self.generar_tabla_completa(pivotes, fecha_valorizacion, monedas[i])
            diccionario[monedas[i]] = tabla

        return diccionario    

    def coeficiente_peso(self, pivote1, pivote2, fecha_actual_flujo):

        fecha_valorizacion = self.get_fecha_valorizacion_date()

        fecha_pivote1 = add_days(fecha_valorizacion, int(pivote1*360))
        fecha_pivote2 = add_days(fecha_valorizacion, int(pivote2*360))
        
        numerador = diferencia_dias_convencion("ACT360", fecha_pivote1, fecha_actual_flujo)
        denominador = diferencia_dias_convencion("ACT360", fecha_pivote1 , fecha_pivote2)

        return numerador/denominador 


    def distribucion_pivotes(self):

        pivotes = self.get_plazos()
        flujos = self.get_flujos()
        fecha_valorizacion = self.get_fecha_valorizacion()
        fechas_pago = flujos["FechaFixing"]
        fechas_largo = len(fechas_pago)

        for i in range(fechas_largo):

            fecha_pago_actual = fechas_pago[i]
            pivotes = self.buscar_pivote(fecha_pago_actual)
            alfa = self.coeficiente_peso(pivotes[0], pivotes[1], fecha_pago_actual)
            print(alfa)








 

