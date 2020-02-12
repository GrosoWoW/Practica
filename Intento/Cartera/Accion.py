import pandas as pd
import numpy as np
from Activo import Activo

"""
Clase principal de Accion hereda de la clase abstracta Activo

"""

class Accion(Activo):


    def __init__(self, nombre, moneda, historico, montoInvertido, monedaCartera, fecha_valorizacion, cn, n):
        
        super(Accion, self).__init__(monedaCartera, fecha_valorizacion, cn)
        self.n = n

        # Nombre de la accion (empresa, etc)
        self.nombre = nombre

        # Moneda que se esta trabajando la accion
        self.moneda = moneda

        # DataFrame con los historicos
        self.historico = historico

        # Monto que se invierte en la accion
        self.inversion = montoInvertido

        # Funcion para calculo de retornos
        self.calcular_retorno(moneda)

        # Funcion para calculo de volatilidades
        self.calcular_volatilidad()

        self.calcular_correlacion()
        
        self.set_volatilidad_general()

    def get_n(self):

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

        pass

    def set_volatilidad_general(self):

        self.volatilidad_general = self.get_volatilidad()



    

