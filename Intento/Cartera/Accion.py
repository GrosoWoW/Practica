import pandas as pd
import numpy as np
from Activo import Activo

"""
Clase principal de Accion hereda de la clase abstracta Activo

"""

class Accion(Activo):


    def __init__(self, nombre, moneda, historico, montoInvertido, monedaCartera, fecha_valorizacion, cn):
        
        super(Accion, self).__init__(monedaCartera, fecha_valorizacion, cn)

        # Nombre de la accion (empresa, etc)
        self.nombre = nombre

        # Moneda que se esta trabajando la accion
        self.moneda = moneda

        # DataFrame con los historicos
        self.historico = historico

        # Monto que se invierte en la accion
        self.inversion = montoInvertido

        # Funcion para calculo de retornos
        self.set_retorno()

        # Funcion para calculo de volatilidades
        self.set_volatilidad()

        self.set_correlacion()
        
        self.set_covarianza()

        self.set_volatilidad_general()


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

    # Conversion de USD/UF/EUR a CLP
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
        return conversion

    def corregir_moneda(self):

        """
        Funcion que se encarga de corregir la moneda de los derivados
        de manera que se este trabajando en un sola moneda, esa moneda
        correponde a la dada en la cartera

        """

        monedaCartera = self.get_monedaCartera()
        monedaBase = self.get_moneda()
        n = 200

        historico_moneda = self.getConversionCLP(monedaCartera, monedaBase)
        retorno = np.zeros(n)
        retorno[0] = 0

        if monedaBase != monedaCartera: 

            for i in range(1,n):

                retorno[i] = np.log(historico_moneda['Cambio'][i]/historico_moneda['Cambio'][i-1])

        aux = self.get_retornos()

        self.retornos = aux + pd.DataFrame(retorno)

    

