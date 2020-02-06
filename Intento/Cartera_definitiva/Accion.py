from Activo import Activo

class Accion(Activo):


    def __init__(self, moneda, historico, monedaCartera, fecha_valorizacion, cn):
        
        super(Accion, self).__init__(monedaCartera, fecha_valorizacion, cn)

        self.moneda = moneda
        
        #   hay que definir el formato de este input
        self.historico = historico

    
    def get_moneda(self):

        return self.moneda

    def get_historico(self):

        return self.historico

    def set_historico(self):

        pass

    # Conversion de USD/UF/EUR a CLP
    def getConversionCLP(monedaCartera, monedaBase, n = '200'):
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
        conversion = pd.read_sql(conversion, cn)
        conversion = conversion.values[::-1]
        conversion = pd.DataFrame(conversion, columns=['Cambio'])
        return conversion

    def corregir_moneda(self):

        monedaCartera = self.get_monedaCartera()
        monedaBase = self.get_moneda()

        historico_moneda = getConversionCLP(monedaCartera, monedaBase)
        retorno = np.zeros(n)
        retorno[0] = 0

        if monedaBase != monedaCartera: 

            for i in range(1,n):

                retorno[i] = np.log(historico['Cambio'][i]/historico['Cambio'][i-1])

        aux = self.get_retornos()

        self.retornos = aux + retorno

    

