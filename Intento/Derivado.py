import datetime
import sys

import numpy as np
import pandas as pd

from Activo import Activo
from Matematica import interpolacion_log_escalar
from UtilIndicadores import add_days
from UtilesValorizacionIndicadores import diferencia_dias_convencion, parsear_curva


"""
Clase principal de derivado hereda de la clase abstracta Activo
funciona como un adapter entre las clases derivado Abstracto y la clase cartera

"""

class Derivado(Activo):

    def __init__(self, derivado_generico, monedaCartera, fecha_valorizacion, cn, n, fechaEfectiva, nemo):

        # Super para la clase DerivadoAbstracto y entregar los valores
        super(Derivado, self).__init__(monedaCartera, fecha_valorizacion, cn, nemo)
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

        return self.get_flujos()

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

        """
        Retorna la moneda base del derivado

        """

        return self.get_flujos()["MonedaBase"][0]

    def set_moneda(self, moneda):

        """
        Setea la moneda del derivado
        La moneda debe ser del tipo string

        """

        self.moneda = moneda

    

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

        curva = ("SELECT TOP(" + str(n) + ")* FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+ str(monedas) +"' AND Hora = '1500' AND Fecha < '" + str(fecha) + "' ORDER BY Fecha")
        curva = pd.read_sql(curva, cnn)[::-1]
        if (curva.empty): raise Exception('Para la moneda ' + moneda + ' en la fecha ' + str(fecha) + ' no se encontró curva en TdCurvasDerivados.')
        return curva

    def obtener_monedas(self):

        """
        Funcion que permite obtener las monedas de los derivados
        correspondientes a los activos y pasivos
        :return: arreglo con string de monedas

        """

        tabla = self.derivado_generico.flujos_valorizados[["ID","ActivoPasivo", "Fecha", "FechaFixing", "FechaFlujo", "FechaPago", "Flujo", "ValorPresenteMonFlujo", "Moneda", "MonedaBase"]]
        monedas = tabla["Moneda"]
        arreglo_monedas = []
        for i in range(len(monedas)):

            moneda = monedas[i]
            if moneda in arreglo_monedas: continue
            arreglo_monedas.append(moneda)

        return arreglo_monedas


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
        monedas_derivado = self.obtener_monedas()
        
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
        if (curva.empty): raise Exception('Para la moneda ' + moneda + ' no se encontró curva efectiva para la fecha ' + str(fecha_valorizacion) + '.')
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

            # Se encuentra en el primer pivote (caso borde)
            if i == 0 and fecha_pago < fecha_pivote:

                return [pivotes[i], pivotes[i]]

            # Se encuentra entre dos pivotes
            elif fecha_pivote > fecha_pago:

                return [pivotes[i - 1], pivotes[i]]

            # Se encuentra en el ultimo pivote (caso borde)
            else:

                return [pivotes[i], pivotes[i]]

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

    def set_distribucion_pivotes(self, diccionario):

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

        nivel = diccionario
        
        # Por cada fecha de pago del derivado
        for i in range(fechas_largo):

            fecha_pago_actual = fechas_pago[i]
            moneda_pago_actual = monedas_pagos[i]
            flujo_pago = flujos["Flujo"][i]

            # Calculamos los pivotes entre los cuales se encuentra la fecha de pago [pivote1, pivote2] si estos son iguales
            # Corresponde a un caso borde el cual esta cubierto
            pivote_entremedio = self.buscar_pivote(fecha_pago_actual)

            # Se obtiene el nombre del pivote que corresponde a Moneda#NumPivote (EJ: CLP#30), es para luego buscar en la matriz de correlacion
            nombre_pivote1 = moneda_pago_actual + "#" + str(int(pivote_entremedio[0]*360))
            nombre_pivote2 = moneda_pago_actual + "#" + str(int(pivote_entremedio[1]*360))

            indice_pivote1 = pivotes.index(pivote_entremedio[0])
            indice_pivote2 = pivotes.index(pivote_entremedio[1])

            curva_parseada = self.pedir_curva(moneda_pago_actual)
            diferencia_dias = diferencia_dias_convencion("ACT360", fecha_valorizacion_date, fecha_pago_actual)
            factor_descuento = interpolacion_log_escalar(diferencia_dias, curva_parseada)

            # Caso borde, los dos pivotes son iguales, todo el calculo de valor presente va a ese pivote
            if indice_pivote1 == indice_pivote2:

                VP = factor_descuento*flujo_pago
                distruciones[indice_pivote1] += VP

                # Tambien se introduce este calculo a el diccionario de niveles, de esta manera se aprovecha el calculo
                for a in range(1,3):
                    nivel_nombre = self.get_niveln(a)
                    nivel[a][nivel_nombre, "Derivado"][indice_pivote1] += VP

            # Caso donde existen dos pivotes distintos, en este caso se necesita alfa para distribuir
            else:

                # Valor de alfa_0, coeficiente de peso
                alfa = self.coeficiente_peso(pivote_entremedio[0], pivote_entremedio[1], fecha_pago_actual)

                # Interpolacion de la volatilidad con el valor de alfa
                volatilidad_inter = alfa*volatilidades[0][nombre_pivote1] + (1 - alfa)*volatilidades[0][indice_pivote2]

                # Alfa solucion de la ecuacion cuadratica, se utilizara para la distribucion de valor presente 
                valor_alfa = self.solucion_ecuacion(volatilidad_inter, volatilidades[0][nombre_pivote1], volatilidades[0][indice_pivote2],\
                        corr[nombre_pivote1][indice_pivote2] )

                # Se discrimina la solucion, es decir se toma la que se encuentre entre 0 y 1
                solucion = self.discriminador_sol(valor_alfa)

                # Valor presente
                VP = factor_descuento*flujo_pago
        
                # Se agregan las distribuciones a los pivotes con el valor de alfa
                distruciones[indice_pivote1] += solucion*VP
                distruciones[indice_pivote2] += (1 - solucion)*VP

                # Por cada nivel solicitado se introduce el calculo en el diccionario de niveles
                for a in range(1,3):
                    nivel_nombre = self.get_niveln(a)
                    nivel[a][nivel_nombre, "Derivado"][indice_pivote1] += VP
                    nivel[a][nivel_nombre, "Derivado"][indice_pivote2] += VP

            
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


