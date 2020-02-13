from Activo import Activo
import datetime
import pandas as pd
import numpy as np
from UtilesValorizacion import parsear_curva, diferencia_dias_convencion
from Matematica import interpolacion_log_escalar
from Util import add_days
import sys

"""
Clase principal de derivado hereda de la clase abstracta Activo
funciona como un adapter entre las clases derivado Abstracto y la clase cartera

"""

class Derivado(Activo):

    def __init__(self, derivado_generico, monedaCartera, fecha_valorizacion, cn, n, fechaEfectiva):

        # Super para la clase DerivadoAbstracto y entregar los valores
        super(Derivado, self).__init__(monedaCartera, fecha_valorizacion, cn)
        self.n = n

        self.fecha_efectiva = fechaEfectiva

        # Derivado de la clase abstracta DerivadoAbstracto
        self.derivado_generico = derivado_generico

        # Se generan y valorizan los flujos del derivado
        self.derivado_generico.genera_flujos()
        self.derivado_generico.valoriza_flujos()

        # Vector con las distribuciones de sus pivotes
        self.distribucion_pivotes = np.zeros(len(self.get_plazos()))

    def get_fecha_efectiva(self):

        return self.fecha_efectiva

    def get_n(self):

        """
        Retorna el parametro self.n correpondiente a la cantidad
        de datos que se desean obtener de historicos

        """

        return self.n


    def get_derivado_generico(self):

        """
        Retorna el derivado abstracto de la clase DerivadoAbstracto
        :return: DerivadoAbstracto 

        """

        return self.derivado_generico

    def get_flujos(self):

        """
        Retorna los flujos de el derivado
        :return: DataFrame con los flujos del derivado

        """

        return self.get_derivado_generico().flujos_valorizados[["ID","ActivoPasivo", "Fecha"\
            , "FechaFixing", "FechaFlujo", "FechaPago", "Flujo", "ValorPresenteMonFlujo", "Moneda", "MonedaBase"]]

    def get_distribucion_pivotes(self):

        """
        Retorna el vector con la distribucion de los flujos en los
        pivotes
        :return: Vector con las distintas distribuciones

        """

        return self.distribucion_pivotes

    def get_moneda(self):

        return self.get_flujos()["Moneda"][0]

    def seleccionar_curva_derivados(self, moneda, n, fecha=datetime.date(2018, 1, 22)):

        """
        Funcion encargada de seleccionar la curva correspondiende en TdCurvasDerivados
        :param moneda: Str con la moneda correspondiente a la curva
        :param n: int con la cantidad de curvas que se desean consultar a la db

        """

        monedas = moneda
        cnn = self.get_cn()

        if moneda == "UF": #Funciona para el error de CLF
            monedas = "CLF"

        curva = ("SELECT TOP(" + str(n) + ")* FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+ str(monedas) +"' AND Hora = '1500' AND Fecha > '" + str(fecha) + "'")
        curva = pd.read_sql(curva, cnn)
        return curva


    def calcular_historico(self):

        """
        Funcion encargada de calcular el historico de los derivados
        Setea self.historicos con el DataFrame resultante

        """

        n = self.get_n()
        moneda = self.get_flujos()["Moneda"][0]
        curvas = self.seleccionar_curva_derivados(moneda, n, self.get_fecha_valorizacion_date())[::-1]

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

        self.historicos = pd.DataFrame(matriz, columns=self.nombre_df(moneda))
        return self.historicos

    def set_historico(self, historico):

        """
        Funcion de seteo del historico
        :param historico: DataFrame con el historico que se desea setear

        """

        self.historicos = historico
        

    def monedas(self):

        """
        Funcion encargada de obtener las distintas monedas del bono
        :return: Vector con las monedas sin repeticion

        """

        flujos = self.get_flujos()["Moneda"]
        lenght = len(flujos)
        monedas = []

        for i in range(lenght):
            moneda_aux = flujos[i]
            
            if moneda_aux not in monedas:

                monedas.append(moneda_aux)

        return monedas

    def nombre_df(self, moneda):

        """
        Funcion encargada de obtener el nombre de las columnas 
        del DataFrame, el formato es Moneda#Plazo
        :param moneda: String con la moneda que se desea poner en la columna
        :return: Arreglo con los nombres

        """

        pivotes = self.get_plazos()
        arreglo = []

        for j in range(len(pivotes)):

            arreglo.append(moneda + "#" + str(int(pivotes[j]*360)))

        return arreglo


    def pedir_curva(self, moneda):

        """
        Funcion encargada de pedir la cirva a la base de datos 
        con los factores de descuento correspondientes
        :return: DataFrame con las distintas curvas

        """

        cn = self.get_cn()

        fecha_valorizacion = self.get_fecha_valorizacion_date()
        curva = ("SELECT * FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+moneda+"' AND Fecha = '"+str(fecha_valorizacion)+"'")
        curva = pd.read_sql(curva, cn)
        curva = parsear_curva(curva["Curva"][0], fecha_valorizacion)
        return curva

    def buscar_pivote(self, fecha_pago):

        """
        Funcion encargada de buscar los pivotes entre donde se encuentra la
        fecha de pago
        :param fecha_pago: Fecha que se desea pivotear
        :return: Vector de dos dimensiones con los dos pivotes calculados

        """

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

        """
        Funcion encargada de calcular el alfa_0
        :param pivote1: int con el valor del pivote1 en años
        :param pivote2: int con el valor del pivote2 en años
        :param fecha_actual_flujo: Fecha con el flujo que se desea pivotear

        """

        fecha_valorizacion = self.get_fecha_valorizacion_date()

        fecha_pivote1 = add_days(fecha_valorizacion, int(pivote1*360))
        fecha_pivote2 = add_days(fecha_valorizacion, int(pivote2*360))
        
        numerador = diferencia_dias_convencion("ACT360", fecha_pivote1, fecha_actual_flujo)
        denominador = diferencia_dias_convencion("ACT360", fecha_pivote1 , fecha_pivote2)

        return numerador/denominador 

    def set_distribucion_pivotes(self):

        """
        Funcion de calculo principal de la distribucion
        de los pivotes
        Setea la distribucion en self.distribucion_pivotes

        """

        pivotes = self.get_plazos()
        flujos = self.get_flujos()

        fecha_valorizacion = self.get_fecha_valorizacion()
        fecha_valorizacion_date = self.get_fecha_valorizacion_date()
        fechas_pago = flujos["FechaFixing"]
        fechas_largo = len(fechas_pago)

        corr = self.get_correlacion()

        monedas_pagos = flujos["Moneda"]

        volatilidades = self.get_volatilidad()

        distruciones = np.zeros(len(pivotes))

        for i in range(fechas_largo):

            fecha_pago_actual = fechas_pago[i]
            moneda_pago_actual = monedas_pagos[i]
            flujo_pago = flujos["Flujo"][i]


            pivote_entremedio = self.buscar_pivote(fecha_pago_actual)
            alfa = self.coeficiente_peso(pivote_entremedio[0], pivote_entremedio[1], fecha_pago_actual)

            nombre_pivote1 = moneda_pago_actual + "#" + str(int(pivote_entremedio[0]*360))
            nombre_pivote2 = moneda_pago_actual + "#" + str(int(pivote_entremedio[1]*360))

            indice_pivote1 = pivotes.index(pivote_entremedio[0])
            indice_pivote2 = pivotes.index(pivote_entremedio[1])

            volatilidad_inter = alfa*volatilidades[0][nombre_pivote1] + (1 - alfa)*volatilidades[0][indice_pivote2]

            curva_parseada = self.pedir_curva(moneda_pago_actual)

            diferencia_dias = diferencia_dias_convencion("ACT360", fecha_valorizacion_date, fecha_pago_actual)
            factor_descuento = interpolacion_log_escalar(diferencia_dias, curva_parseada)
            valor_alfa = self.solucion_ecuacion(volatilidad_inter, volatilidades[0][nombre_pivote1], volatilidades[0][indice_pivote2],\
                     corr[nombre_pivote1][indice_pivote2] )

            solucion = self.discriminador_sol(valor_alfa)

            VP = factor_descuento*flujo_pago
    
            distruciones[indice_pivote1] += solucion*VP
            distruciones[indice_pivote2] += (1 - solucion)*VP

        self.distribucion_pivotes = (distruciones)

    def set_volatilidad_general(self):

        """
        Funcion que calcula la volatilidad general del derivado

        """

        vector = self.get_distribucion_pivotes()
        suma = sum(vector)
        vector = vector/suma
        covarianza = self.get_covarianza()
        self.volatilidad_general = np.sqrt(np.dot(np.dot(vector, covarianza), np.transpose(vector)))      