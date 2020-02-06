
from abc import ABC, abstractmethod

import pandas as pd
import numpy as np

from Correlaciones import ewma, ewma_matriz

import math

"""
Clase Abstracta Activo correspondiente a generar los diferentes activos

"""

class Activo(ABC):

    def __init__(self, monedaCartera, fecha_valorizacion, cn):

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

        # Fecha a la que se desea valorizar (se pasa a string para mejor manejo YYYY-mm-dd)
        self.fecha_valorizacion = str(fecha_valorizacion).split(" ")[0]

        self.fecha_valorizacion_date = fecha_valorizacion
        # Conexion a base de datos
        self.cn = cn


    def get_fecha_valorizacion(self):

        """
        Retorna la fecha de valorizacion :3
        :return: str con las fechas en el formato YYYY-mm-dd

        """

        return self.fecha_valorizacion

    def get_fecha_valorizacion_date(self):

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

    
    @abstractmethod
    def set_historico(self):

        pass
    
    @abstractmethod
    def corregir_moneda(self):

        pass

    def set_retorno(self):

        historicos = self.get_historicos()
        numero_filas = np.size(historicos, 0)
        print(numero_filas)
        numero_columnas = np.size(historicos, 1)
        print(numero_columnas)
        vector = np.zeros([numero_filas, numero_columnas])

        for i in range(numero_columnas):

            columna = historicos.iloc[:, i]  # Sacando la columna i del historico
            for j in range(1, numero_filas):

                valor_actual = columna[j]
                valor_previo = columna[j - 1]
                retorno = np.log(valor_actual/valor_previo)
                vector[j][i] = retorno

        self.retornos = pd.DataFrame(vector)

    def set_volatilidad(self):

        retornos = self.get_retornos()
        cantidad_columnas = np.size(retornos, 1)
        volatilidades_vector = np.zeros(cantidad_columnas)

        for i in range(cantidad_columnas):

            retornos_vector = retornos.iloc[:,i].values
            volatilidad_aux = ewma(retornos_vector, 0.94)
            volatilidades_vector[i] = volatilidad_aux["Vol c/ajuste"][0]
        
        self.volatilidad = pd.DataFrame(volatilidades_vector)

    def set_correlacion(self):

        lenght = len(self.get_plazos())
        volatilidad = self.get_volatilidad()
        retornos = self.get_retornos()
        corr = ewma_matriz(lenght, retornos, volatilidad)
        self.correlacion = corr

    
    def set_covarianza(self):

        corr = self.get_correlacion()
        cor = corr.values
        vol = self.volatilidad.iloc[:, 0]
        D = np.diag(vol)
        self.covarianza = pd.DataFrame(np.dot(np.dot(D,cor),D))


    def solucion_ecuacion(self, sigma_flujo, sigma_pivote1, sigma_pivote2, ro):


        A = (sigma_pivote1**2 + sigma_pivote2**2 - 2*ro*sigma_pivote1*sigma_pivote2)
        B = (2 * ro * sigma_pivote1* sigma_pivote2 - 2*sigma_pivote2**2)
        C = (sigma_pivote2**2 - sigma_flujo**2)

        x1 = (-B+math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte positiva
        x2 = (-B-math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte negativa

        return[x1, x2]


    





    
        