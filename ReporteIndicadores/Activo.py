import math
import sys
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from Correlaciones import ewma, ewma_matriz


"""
Clase Abstracta Activo correspondiente a generar los diferentes activos

"""

class Activo(ABC):

    def __init__(self, monedaCartera, fecha_valorizacion, cn, nemo):

        # Moneda en que se desea trabajar dentro de la cartera
        self.monedaCartera = monedaCartera

        # Retornos propios del activo
        self.retornos = pd.DataFrame()

        # Historicos propios del activo
        self.historicos = pd.DataFrame()

        # Volatilidades propias del activo
        self.volatilidad = pd.DataFrame()

        # Correlacion propia del activo
        self.correlacion = pd.DataFrame()

        # Covarianza propia del activo
        self.covarianza = pd.DataFrame()

        # Parametro de cantidad de dias por año
        self.anio = 360 

        # Plazos de tiempo que se trabajaran los pivotes
        self.plazos = [30/self.anio, 90/self.anio, 180/self.anio, 360/self.anio, 2, 3, 4, 5, 7,\
            9, 10, 15, 20, 30]

        # Volatilidad total del activo
        self.volatilidad_general = 0

        # Fecha a la que se desea valorizar (se pasa a string para mejor manejo YYYY-mm-dd)
        self.fecha_valorizacion = str(fecha_valorizacion).split(" ")[0]

        # Fecha de valorizacion en el formate datetime
        self.fecha_valorizacion_date = fecha_valorizacion

        # nemotecnico del activo

        self.nemotecnico = nemo

        # Conexion a base de datos
        self.cn = cn


        # Categorizacion

        self.nivel1 = ''

        self.nivel2 = ''

        self.set_niveles()

        self.distribucion_niveles = dict()

        # Peso del activo en la cartera (Su valor presente dividido en el monto total de la cartera)
        self.peso = 0

        self.peso_condensado = 0

        # Monto total de la cartera a la que pertenece el activo
        self.monto = 0

        self.var_porcentual = 0

        # Valor de la distribucionn Normal inversa al 95% de conﬁanza
        self.N = 1.0

        # FALTA HACER ARBITRARIO EL 60 PARA n
        self.r_d = np.zeros(60)

    def get_rd(self):

        return self.r_d

    def get_peso_condensado(self):

        return self.peso_condensado

    def get_N(self):

        """
        Retorna el parametro de valor de la distribucionn Normal inversa al 95% de conﬁanza
        es del tipo float

        """

        return self.N

    def get_var_porcentual(self):

        """
        Retorna la variacion porcentual del activo

        """

        return self.var_porcentual
        
    def get_distribucion_niveles(self):

        """
        Retorna la distribucion de valor presente del activo por niveles
        es del tipo diccionario. Hay una llave correspondiente al valor del 
        nivel (1, 2, 3, etc), luego otra llave con el nombre del nivel y finalmente
        el valor es un float

        """

        return self.distribucion_niveles

    def get_niveln(self, n):

        if n == 1:
            return self.nivel1
        elif n == 2:
            return self.nivel2

    def get_volatilidad_general(self):

        """
        Retorna la volatilidad total del activo
        
        """
        return self.volatilidad_general

    def get_fecha_valorizacion(self):

        """
        Retorna la fecha de valorizacion
        :return: str con las fechas en el formato YYYY-mm-dd

        """

        return self.fecha_valorizacion

    def get_fecha_valorizacion_date(self):

        """
        Retorna la fecha de valorizacion
        :return: datetime con la fecha de valorizacion

        """

        return self.fecha_valorizacion_date
    
    def get_cn(self):

        """
        Retorna la conexion a base de datos
        :return: pandas sql con la conexion

        """

        return self.cn

    def get_monedaCartera(self):

        """
        Retorna la moneda principal de la cartera
        :return: str con la moneda

        """

        return self.monedaCartera

    def get_historicos(self):

        """
        Retorna el dataframe de los historicos
        :return: DataFrame con historicos propios del activo
        
        """

        return self.historicos

    def get_plazos(self):

        """
        Retorna el vector con los plazos en años de los pivotes
        :return: Vector con periodos

        """

        return self.plazos

    def get_retornos(self):

        """
        Retorna los retornos correspondientes a el activo
        :return: DataFrame con los retornos

        """

        return self.retornos

    def get_volatilidad(self):

        """
        Retorna las volatilidades propias del activo
        :return: DataFrame con las volatilidades

        """

        return self.volatilidad

    def get_correlacion(self):

        """
        Retorna la correlacion propia del activo
        :return: DataFrame con las correlaciones

        """
        return self.correlacion

    def get_covarianza(self):

        """
        Retorna las covarianzas propias del activo
        :return: DataFrame con las covarianzas

        """

        return self.covarianza

    def get_nemotecnico(self):

        """
        Retorna el nemotecnico del activo
        Este nemotecnico tiene el formato de string

        """

        return self.nemotecnico

    def get_peso(self):

        """
        Retorna el peso del activo, este es calculado con el vp del activo
        dividido en el monto total de la cartera
        es del tipo float

        """

        return self.peso

    def get_monto(self):

        """
        Retorna el monto de la cartera a la que pertenece
        el activo, es del formato float

        """

        return self.monto
    
    def set_plazos(self, plazos):

        """
        Funcion set para los plazos
        :param plazos: arreglo con los pivotes de plazos que se desean setear

        """

        self.plazos = plazos
    
    @abstractmethod
    def set_historico(self):

        pass
    

    @abstractmethod
    def set_volatilidad_general(self):
        
        """
        Define la volatilidad del activo

        """
        pass

    def set_var_porcentual(self, var):

        self.var_porcentual = var

    def set_niveles(self):

        """
        Le asigna al activo su categoria correspondiente segun nivel
        
        """

        nemo = self.get_nemotecnico()
        cn = self.get_cn()
        niveles = "SELECT TOP (1) [Nivel1] , [Nivel2] FROM [dbPortFolio].[dbo].[TdPlanvitalAtributos] WHERE Nemotecnico = '" + nemo + "'"
        niveles = pd.read_sql(niveles, cn)
        if (niveles.empty): raise Exception('Para el instrumento de nemotécnico ' + nemo + ' no existe información de sus niveles en base de datos.')
        self.nivel1 = niveles['Nivel1'][0]
        self.nivel2 = niveles['Nivel2'][0]

    def set_peso(self, peso):

        """
        Setea el peso del activo, este peso es del tipo float

        """

        self.peso = peso

    def set_monto(self, monto):

        """
        Setea el monto de la cartera a la que pertenece el activo
        Es del formato float

        """

        self.monto = monto

    def discriminador_sol(self, soluciones):

        """
        Funcion para discriminar las soluciones de la ecuacion
        es decir que se tome una que se encuentre entre 0 y 1

        """

        for i in range(2):
            if (0 <= soluciones[i] and soluciones[i] <= 1):

                return soluciones[i]
        print("Javier, nos fallaste")
        return sys.exit(1) 


    def calcular_retorno(self, monedaActivo, monedaCartera):

        """
        Funcion de calculo de retorno, ajustando la moneda
        a la cartera, retorna y setea en self.retornos
        :param moneda: String con la moneda de ajuste
        :return: DataFrame con los retornos

        """

        historicos = self.get_historicos()
        columna_nombre = list(historicos)
        numero_filas = np.size(historicos, 0)
        numero_columnas = np.size(historicos, 1)
        vector = np.zeros([numero_filas, numero_columnas])

        for nombre in range(len(columna_nombre)):

            columna_nombre[nombre] = columna_nombre[nombre].replace(monedaActivo, monedaCartera)



        for i in range(numero_columnas):

            columna = historicos.iloc[:, i]  # Sacando la columna i del historico
            for j in range(1, numero_filas):

                valor_actual = columna[j]
                valor_previo = columna[j - 1]
                retorno = np.log(valor_actual/valor_previo)
                vector[j][i] = retorno

        data = pd.DataFrame(data = vector, columns=columna_nombre, index=[i for i in range(numero_filas)])

        monedaCartera = self.get_monedaCartera()
        monedaBase = monedaActivo

        # Si la moneda del activo no es la misma de la cartera, se debe realizar un ajuste
        if monedaBase != monedaCartera: 

            historico_moneda = self.getConversionCLP(monedaCartera, monedaBase)
            retorno_moneda = np.zeros(numero_filas)
            retorno_moneda[0] = 0

            for i in range(1,numero_filas):

                retorno_moneda[i] = np.log(historico_moneda['Cambio'][i] / historico_moneda['Cambio'][i-1])

            for i in range(0,np.size(data, 1)):

                for j in range(0,np.size(data, 0)):

                    data.iloc[j][i] = data.iloc[j][i] + retorno_moneda[j]


        self.retornos = data
        return self.retornos

    def set_peso_condensado(self, peso):

        self.peso_condensado = peso

    def set_r_di(self, valor, indice):

        self.r_d[indice] = valor

    def set_retorno(self, retorno):

        """
        Setea el parametro de retorno
        :param retorno: DataFrame con los retornos que se desean setear

        """

        self.retornos = retorno

    def calcular_volatilidad(self):

        """
        Funcion de calculo de la volatilidad del activo
        :return: DataFrame con las volatilidades

        """

        retornos = self.get_retornos()
        columnas_nombre = list(retornos)
        cantidad_columnas = np.size(retornos, 1)
        volatilidades_vector = np.zeros(cantidad_columnas)

        for i in range(cantidad_columnas):

            retornos_vector = retornos.iloc[:,i].values
            volatilidad_aux = ewma(retornos_vector, 0.94)
            volatilidades_vector[i] = volatilidad_aux["Vol c/ajuste"][0]
        
        self.volatilidad = pd.DataFrame(volatilidades_vector, index=columnas_nombre)
        return self.volatilidad

    def set_volatilidad(self, volatilidad):

        
        """
        Setea el parametro de volatilidad
        :param retorno: DataFrame con los volatilidades que se desean setear

        """

        self.volatilidad = volatilidad


    def calcular_correlacion(self):

        """
        Funcion que calcula la correlacion de
        el activo

        """

        lenght = len(list(self.get_historicos()))
        volatilidad = self.get_volatilidad()
        retornos = self.get_retornos()
        corr = ewma_matriz(lenght, retornos, volatilidad)
        self.correlacion = corr

        return self.correlacion

    def set_correlacion(self, correlacion):

        
        """
        Setea el parametro de correlacion
        :param retorno: DataFrame con las correlaciones que se desean setear

        """

        self.correlacion = correlacion

    
    def calcular_covarianza(self):

        """
        Funcion de calculo de las covarianza del activo
        :return: DataFrame con la covarianza del activo

        """

        corr = self.get_correlacion()
        cor = corr.values
        vol = self.volatilidad.iloc[:, 0]
        D = np.diag(vol)
        self.covarianza = pd.DataFrame(np.dot(np.dot(D,cor),D))
        return self.covarianza

    def set_covarianza(self, covarianza):

        
        """
        Setea el parametro de covarianza
        :param retorno: DataFrame con las covarianzas que se desean setear

        """

        self.covarianza = covarianza


    def solucion_ecuacion(self, sigma_flujo, sigma_pivote1, sigma_pivote2, ro):

        """
        Funcion que resuelve la ecuacion cuadratica
        :param sigma_flujo: Volatilidad del flujo
        :param sigma_pivote1: Volatilidad del pivote 1
        :param sigma_pivote2: Volatilidad del pivote 2
        :param ro: Matriz de correlacion del activo
        :return: Arreglo con las soluciones x1, x2 

        """


        A = (sigma_pivote1**2 + sigma_pivote2**2 - 2*ro*sigma_pivote1*sigma_pivote2)
        B = (2 * ro * sigma_pivote1* sigma_pivote2 - 2*sigma_pivote2**2)
        C = (sigma_pivote2**2 - sigma_flujo**2)

        x1 = (-B+math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte positiva
        x2 = (-B-math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte negativa

        return [x1, x2]

    def getConversionCLP(self, monedaCartera, monedaBase, n = '200'):

        """
        Entrega el historico del valor de conversion en CLP/monedaBase por n dias.
        :param monedaBase: String con la moneda que se desea llevar a CLP.
        :param n: String con la cantidad de dias que se quieren.
        :return: Un DataFrame con el historico de conversion.

        """
        if (monedaBase == 'UF' and monedaCartera == 'CLP'):
            conversion = "SELECT TOP(" + n + ") Valor FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = 'CLF' AND Campo = 'PX_LAST' AND Hora = '1700' ORDER BY Fecha DESC "
        else:
            conversion = "SELECT TOP(" + n + ") Valor FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = '" + monedaBase + "' AND Campo = '" + monedaCartera + "' AND Hora = 'CIERRE' ORDER BY Fecha DESC"
        conversion = pd.read_sql(conversion, self.get_cn())
        conversion = conversion.values[::-1]
        conversion = pd.DataFrame(conversion, columns=['Cambio'])
        if (conversion.empty): raise Exception('No existe información de conversión de ' + monedaBase + ' a ' + monedaCartera + ' en base de datos.')
        return conversion

    
    def var_porcentual_instrumento(self):

        """
        Funcion que calcula la variacion porcentual del activo

        """

        N = self.get_N()
        calculo = np.sqrt(252)* N * self.get_peso() * self.get_volatilidad_general()
        return calculo

    def var_dinero_instrumentro(self):

        """
        Funcion que calculo la variacion de dinero del activo

        """

        N = self.get_N()
        calculo = np.sqrt(252)* N * self.get_monto()* self.get_peso() * self.get_volatilidad_general()
        return calculo

