
from BonoUtil import *
from UtilesValorizacion import *
from Util import *
from Matematica import interpolacion_escalar

from Activo import Activo

from math import exp, log
class Bono(Activo):

    def __init__(self, riesgo, moneda, cupones, convencion, fechaEmision, monedaCartera, fecha, cn):


        super(Bono, self).__init__(monedaCartera, fecha, cn)

        self.riesgo = riesgo

        self.moneda = moneda

        self.monedaCartera = monedaCartera

        #  Hay que parsearlo
        self.cupones = cupones

        self.convencion = convencion

        self.distribucionPlazos = []

        self.fecha_emision = fechaEmision

        self.cn = cn

        # En la base de datos, los casos enunciados traen la informacion de la curva por parametros, los otros vienen listos
        # para parsear e interpolar el caso requerido.
        self.parametroInterpolado = True if(((riesgo == 'AAA' or riesgo == 'A')  and moneda == 'CLP') or moneda == 'USD') else False

    def get_fecha_emision(self):

        return self.fecha_emision

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

        monedaCartera = self.get_monedaCartera()
        monedaBase = self.get_moneda()
        n = 200

        historico_moneda = self.getConversionCLP(monedaCartera, monedaBase)
        print(historico_moneda)
        retorno = np.zeros(n)
        retorno[0] = 0

        if monedaBase != monedaCartera: 

            for i in range(1,n):

                retorno[i] = np.log(historico_moneda['Cambio'][i] / historico_moneda['Cambio'][i-1])

        aux = self.get_retornos()

        for i in range(np.size(aux,1)):

            aux.iloc[:,i] = aux.iloc[:,i] + retorno

        self.retornos = aux

    def get_distribucionPlazos(self):

        return self.distribucionPlazos

    def get_riesgo(self):

        """
        Retorna el riesgo correspondiente al bono que se trabaja

        """

        return self.riesgo

    def get_moneda(self):

        """
        Retorna la moneda del bono

        """

        return self.moneda

    def get_monedaCartera(self):

        """
        Retorna la moneda en que se esta trabajando la cartera

        """

        return self.monedaCartera

    def get_cupones(self):

        """
        Retorna los cupones de pago de los bonos (en tabla de desarrollo)

        """

        return self.cupones

    def get_convencion(self):

        """
        Retorna la convencion correspondiente al bono

        """

        return self.convencion

    def get_parametroInterpolado(self):

        """
        Retorna el parametroInterpolado para verificar que
        las curvas se consulten de manera correcta

        """

        return self.parametroInterpolado

    def TIR(self, param, p):
        '''
        Calcula el TIR para el periodo p, en base a los parametros entregados, usando la formula de interpolacion.
        :param param: Dataframe con los parametros de la curva.
        :param p: Plazo donde se evaluará la curva.
        :return: TIR.
        '''

        coef0 = param[1]
        coef1 = param[2]
        coef2 = param[3]
        coef3 = param[4]
        tir = (coef1 + (coef0 - coef1) * (1 - np.exp(-(p*360) / coef2)) * (coef2 / (p*360)) + coef3 * ((1 - np.exp(-(p*360) /                        coef2)) * (coef2 / (p*360)) - np.exp(-p*360 / coef2)))
        return tir

    def interpolacion_log_escalarBonos(self, x, XY, n=0, m=0, siExt=True, first=True):
        """Indica la abscica en la ordenada x al realizar interpolación logaritmica con los puntos del arreglo XY

        :param x: float abscica al cual se le busca la ordenada con interpolación
        :param XY: array con puntos x,y en
        :param n: int posicion del punto inicial en el arreglo (se setea automáticamente)
        :param m: int posicion del punto final en el arreglo (se setea automáticamente)
        :param siExt: bool indica si se hace extrapolación en caso de que x esté por sobre el rango del arreglo
        :param first: bool indica si es la primera vez que se llama a la función, para settear n y m.
        :return: float ordenada obtenida al realizar interpolación logaritmica
        """
        if first:
            n = 0
            m = len(XY)-1

        y0 = float(XY[0][1])  # Ordenada del primer punto del arreglo
        x1 = float(XY[n][0])  # Abscisa del punto n del arreglo
        y1 = float(XY[n][1])  # Ordenada del punto n del arreglo
        x2 = float(XY[m][0])  # Abscisa del punto m del arreglo
        y2 = float(XY[m][1])  # Ordenada del punto m del arreglo
        x = float(x)  # Abscisa del punto al cual se le busca la ordenada

        if n == m:
            return y1

        if x == x1:
            return y1

        if x < x1:  # x menor o igual que el menor del intervalo
            "Retornando"
            if siExt:
                return y1**(x/x1)   
            else:
                return y1

        if x2 == x:  # x igual al maximo del intervalo
            return y2

        if x2 < x:  # x mayor que el maximo del intervalo
            if siExt:
                return ((y2/y0)**(x/x2)) * y0
            else:
                return y2

        else:  # x dentro del intervalo
            if m - n == 1:  # Pivote encontrado
                return exp((log(y2)-log(y1))/(x2-x1)*(x-x1) + log(y1))  # Se realiza interpolación logaritmica

        j = round((n+m)/2.0)  # Se busca el pivote en la posición j
        if float(XY[j][0]) >= x:
            return self.analisisCasoBorde(x, XY, n, j, siExt, False)
        else:
            return self.analisisCasoBorde(x, XY, j, m, siExt, False)

    def analisisCasoBorde(self, x, XY, n = 0, m = -1, siExt = True, first = True):
        
        if(m == -1): m = len(XY)-1

        if (float(XY[n][1]) < 0 or float(XY[m][1]) < 0): 

            return interpolacion_escalar(x, XY, n, m, first)

        else:

            return self.interpolacion_log_escalarBonos(x, XY, n, m, siExt, first)

    def curvas_historico(self):

        n = '200'
        cn = self.get_cn()
        moneda = self.get_moneda()
        riesgo = self.get_riesgo()

        if( ((riesgo == 'AAA' or riesgo == 'A')  and moneda == 'CLP') or moneda == 'USD'):

            cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = 'IF#" + moneda + "' ORDER BY Fecha DESC "

        elif(riesgo == 'AA' and moneda == 'CLP'):

            cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Consolidado#Prepagables' ORDER BY Fecha DESC"

        else:

            cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Corporativos#No Prepagables' ORDER BY Fecha DESC "
        
        cb = pd.read_sql(cb, cn)
        curva = cb.values[::-1]

        return pd.DataFrame(curva)

    def castDay(self, strday):

        if(type(strday) != type('hola')): return strday
        else:

            arrayDay = strday.split('-')
            return datetime.date(int(arrayDay[0]), int(arrayDay[1]), int(arrayDay[2]))

    def set_historico(self):

        curvas = self.curvas_historico()
        plazos = self.get_plazos()
        convencion = self.get_convencion()
        fecha_aux = self.castDay(self.get_fecha_valorizacion())

        cant_curvas = np.size(curvas, 0)

        historico = np.zeros([cant_curvas, len(plazos)])
        caso_parametro = self.get_parametroInterpolado()

        # Para cada plazo
        for i in range(len(plazos)):

            # Para cada curva
            for j in range(cant_curvas):
                
                if(caso_parametro):
                    tir = self.TIR(curvas.iloc[j], plazos[i])
                    historico[j][i] = factor_descuento(tir, self.castDay(self.get_fecha_valorizacion()), add_days(self.castDay(self.get_fecha_valorizacion()), plazos[i]* 360), convencion, 0)
                
                else:
                    fecha_ini = curvas[0][j].date()
                    fecha_fin = add_days(fecha_ini, plazos[i] * 360)
                    c = parsear_curva(curvas[2][j], fecha_aux)
                    tir = self.analisisCasoBorde(plazos[i], c)
                    historico[j][i] = factor_descuento(tir/100, fecha_ini, fecha_fin, convencion, 0)

        self.historicos = pd.DataFrame(historico)

    def distribucion_pivotes(self):

        plazos = self.get_plazos()
        fecha_valorizacion = self.get_fecha_valorizacion()
        convencion = self.get_convencion()
        fecha_emision = self.get_fecha_emision()

        cupones = self.get_cupones()
        cupones = StrTabla2ArrTabla(cupones, fecha_emision)



