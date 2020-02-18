import pandas as pd
import numpy as np
from Activo import Activo

"""
Clase principal de Accion hereda de la clase abstracta Activo

"""

class Accion(Activo):


    def __init__(self, nombre, moneda, retornos, montoInvertido, monedaCartera, fecha_valorizacion, cn, n, fondo, nemo):
        
        super(Accion, self).__init__(monedaCartera, fecha_valorizacion, cn, nemo)
        self.n = n

        # Nombre de la accion (empresa, etc)
        self.nombre = nombre

        # Moneda que se esta trabajando la accion
        self.moneda = moneda

        # DataFrame con los historicos
        self.historico = retornos

        self.retornos_accion = retornos

        # Monto que se invierte en la accion
        self.inversion = montoInvertido

        # Funcion para calculo de retornos
        self.set_retorno(retornos)

        # Funcion para calculo de volatilidades
        self.calcular_volatilidad()

        # Funcion de calculo de la correlacion
        self.calcular_correlacion()
        
        # Funcion de calculo de la volatilidad de la accion
        self.set_volatilidad_general()

        # Fondo al que pertenece la accion
        self.fondo = fondo

    def get_fondo(self):

        return self.fondo

    def get_n(self):

        """
        Retorna el parametro self.n correpondiente a la cantidad
        de datos que se desean obtener de historicos

        """

        return self.n

    def get_inversion(self):

        """
        Retorna el monto de la inversion que posee la accion
        :return: float con la inversion de accion

        """

        return self.inversion

    def get_nombre(self):

        """
        Retorna el nombre de la accion
        :return: String con el nombre de la empresa de la accion

        """

        return self.nombre

    def get_moneda(self):

        """
        Retorna la moneda en la que se encuentra la accion
        :return: String con la moneda de la accion

        """
        
        return self.moneda

    def get_historicos(self):

        """
        Retorna los historicos de la accion
        :return: DataFrame con los historicos de la accion

        """

        self.historico.columns = [self.get_nombre()]
        return self.historico

    def set_historico(self):

        """
        Funcion de setear historico

        """

        pass

    def set_volatilidad_general(self):

        """
        Funcion que setea la volatilidad total de la accion

        """

        self.volatilidad_general = self.get_volatilidad()