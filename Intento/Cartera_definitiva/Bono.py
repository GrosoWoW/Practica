
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

        self.cupones = cupones

        self.convencion = convencion

        self.distribucionPlazos = []

        self.fecha_emision = fechaEmision

        self.cn = cn

        # En la base de datos, los casos enunciados traen la informacion de la curva por parametros, los otros vienen listos
        # para parsear e interpolar el caso requerido.
        self.parametroInterpolado = True if(((riesgo == 'AAA' or riesgo == 'A')  and moneda == 'CLP') or moneda == 'USD') else False

        # Procesos de inicializacion
        self.set_historico()
        self.set_retorno()
        self.corregir_moneda()
        self.set_volatilidad()
        

    def get_fecha_emision(self):
        '''
        Retorna la fecha de emision del bono
        '''

        return self.fecha_emision

   
    def corregir_moneda(self):
        '''
        Lleva la inversion a la moneda de la cartera
        '''

        monedaCartera = self.get_monedaCartera()
        monedaBase = self.get_moneda()
        n = 200
        historico_moneda = self.getConversionCLP(monedaCartera, monedaBase)
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
        '''
        Retorna la distribucion de los cupones en los plazos
        '''

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

    def get_nombres_columnas(self):

        moneda = self.get_moneda()
        riesgo = self.get_riesgo()
        plazo = self.get_plazos()

        nombres = []

        for i in range(len(plazo)):

            nombres.append(moneda + "#" + str(int(plazo[i] * 360)) + "#" + riesgo)

        return nombres

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
        curva = cb[::-1]

        return pd.DataFrame(curva)

    def set_historico(self):
        '''
        Define el historico de un bono en virtud de su moneda y riesgo
        '''

        curvas = self.curvas_historico()
        plazos = self.get_plazos()
        convencion = self.get_convencion()
        fecha_aux = self.cast_day(self.get_fecha_valorizacion())
        nombre_columna = self.get_nombres_columnas()

        cant_curvas = np.size(curvas, 0)

        historico = np.zeros([cant_curvas, len(plazos)])
        caso_parametro = self.get_parametroInterpolado()

        # Para cada plazo
        for i in range(len(plazos)):

            # Para cada curva
            for j in range(cant_curvas):
                
                if(caso_parametro):
                    tir = self.TIR_p(curvas.iloc[j],[plazos[i]])[0]
                    historico[j][i] = factor_descuento(tir, self.cast_day(self.get_fecha_valorizacion()), add_days(self.cast_day(self.get_fecha_valorizacion()), plazos[i]* 360), convencion, 0)
                
                else:
                    fecha_ini = curvas[0][j].date()
                    fecha_fin = add_days(fecha_ini, plazos[i] * 360)
                    c = parsear_curva(curvas[2][j], fecha_aux)
                    tir = self.analisisCasoBorde(plazos[i], c)
                    historico[j][i] = factor_descuento(tir/100, fecha_ini, fecha_fin, convencion, 0)

        self.historicos = pd.DataFrame(historico, columns =  nombre_columna)

    def piv_near(self, dia):
        '''
        Funcion que entrega los indices de los periodos en el arreglo que colindan a la fecha a evaluar
        :param: dia: Plazo correspondiente a la fecha a evaluar
        :param: periodos: Arreglo de plazos
        '''
        periodos = self.get_plazos()
        pivotes = [-1,-1]
        for i in range(len(periodos)):
            if (dia < periodos[0]):
                pivotes[1] = 0
            elif(dia > periodos[len(periodos)-1]):
                pivotes[0] = len(periodos)-1
            elif(dia > periodos[i]):
                pivotes[1] = i+1
                pivotes[0] = i
            elif (dia == periodos[i]):
                pivotes[0] = pivotes[1] = i
        return pivotes

    def cast_day(self,strday):
        if(type(strday) != type('hola')): return strday
        else:
            arrayDay = strday.split('-')
        return datetime.date(int(arrayDay[0]), int(arrayDay[1]), int(arrayDay[2]))

    def curvaBono(self, fecha):
        '''
        Funcion que entrega la curva para un bono en base a su riesgo, moneda y la fecha deseada.
        :param fecha: String de la fecha que se quiere la curva.
        :return: dataFrame con la informacion.
        '''
        riesgo = self.get_riesgo()
        moneda = self.get_moneda()
        cn = self.get_cn()

        # Se usan curvas por parametros para los casos USD de todo riesgo y CLP de riesgo AAA
        if( ((riesgo == 'AAA' or riesgo == 'A') and moneda == 'CLP') or moneda == 'USD'):
            cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = 'IF#" + moneda + "' AND Fecha = '" + fecha + "' ORDER BY Fecha ASC"
        elif(riesgo == 'AA' and moneda == 'CLP'):
            cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Consolidado#Prepagables' AND Fecha = '" + fecha + "' ORDER BY Fecha ASC"
        else:
            cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Corporativos#No Prepagables' AND Fecha = '" + fecha + "' ORDER BY Fecha ASC"
        cb = pd.read_sql(cb, cn)
        return cb

    def TIR_p(self, param, p):
        '''
        Calcula el TIR para el periodo p, en base a los parametros entregados, usando la formula de interpolacion.
        :param param: Dataframe con los parametros de la curva.
        :param p: Plazo donde se evaluará la curva.
        :return: TIR.
        '''
        coef0 = param['ancla']
        coef1 = param['y0']
        coef2 = param['y1']
        coef3 = param['y2']
        tir = np.zeros(len(p))
        for i in range(len(p)):
            tir[i] = (coef1 + (coef0 - coef1) * (1 - np.exp(-(p[i]*360) / coef2)) * (coef2 / (p[i]*360)) + coef3 * ((1 - np.exp(-(p[i]*360) /                        coef2)) * (coef2 / (p[i]*360)) - np.exp(-p[i]*360 / coef2)))
        return tir

    def tir_plazos(self, p):
        '''
        Calcula el TIR para dos plazos, en base a la moneda y riesgo asociados.
        :param p: Arreglo con los indices de los plazos a calcular.
        :return: Arreglo de tamaño 2 con el TIR.
        '''
        riesgo = self.get_riesgo()
        moneda = self.get_moneda()
        plazos = self.get_plazos()
        fecha = self.get_fecha_valorizacion()
        curva = self.curvaBono(fecha)

        tir = np.zeros(2)
        if (((riesgo == 'AAA' or riesgo == 'A')  and moneda == 'CLP') or moneda == 'USD'):
            tir = self.TIR_p(curva, [plazos[p[0]], plazos[p[1]]])
        else:
            for i in range(2):
                c = parsear_curva(curva["StrCurva"][0], add_days(self.cast_day(fecha), int(plazos[p[i]])))
                tir[i] = self.interpolacion_log_escalarBonos(plazos[p[i]], c)
        return tir

    def actualizar(self, alfa, vp, piv, flujo):
         
        p = self.get_plazos()

        if(piv[0] == -1 or p[piv[1]] == p[piv[0]]):
            flujo[0] += vp
        elif (piv[1] == -1):
            flujo[len(flujo)-1] += vp*alfa
        else:
            flujo[piv[0]] += vp*alfa
            flujo[piv[1]] += vp*(1-alfa)
        return flujo

    def set_distribucionPlazos(self):

        plazos = self.get_plazos()
        fecha_valorizacion = self.cast_day(self.get_fecha_valorizacion())
        convencion = self.get_convencion()
        fecha_emision = self.get_fecha_emision()
        volatilidad = self.get_volatilidad()
        correlacion = self.get_correlacion()
        moneda = self.get_moneda()
        riesgo = self.get_riesgo()

        cupones = self.get_cupones()
        cupones = StrTabla2ArrTabla(cupones, fecha_emision)
        
        n_cupones = np.size(cupones,0)

        flujo_plazos = np.zeros(len(plazos))
        # cupon = (nroDelCupon, fechaCupon, fechaEmision, cupon, amortizacion, inversion, flujo )
        # Para cada cupon
        for i in range(n_cupones):
            flujo = cupones[i][6]
            fecha_flujo = cupones[i][1].date()
            plazo_flujo = diferencia_dias_convencion(convencion, fecha_valorizacion, fecha_flujo)/360

            if(plazo_flujo < 0): continue

            plazos_index = self.piv_near(plazo_flujo)

            tir_plazos = self.tir_plazos(plazos_index)

            # Casos borde.
            if (plazos_index[1] == -1): 
                flujo_plazos[plazos_index[0]] += flujo / (1 + tir_plazos[0])**plazo_flujo
                continue
            elif (plazos_index[0] == -1): 
                flujo_plazos[plazos_index[1]] += flujo / (1 + tir_plazos[1])**plazo_flujo
                continue

            a_0 = (plazo_flujo - plazos[plazos_index[0]]) / (plazos[plazos_index[1]] - plazos[plazos_index[0]])

            tir_flujo = a_0 * tir_plazos[0] + (1 - a_0) * tir_plazos[1]

            volatilidad_flujo = a_0 * volatilidad.iloc[plazos_index[0]] + (1 - a_0) * volatilidad.iloc[plazos_index[1]]

            vp_flujo = flujo / ( 1 + tir_flujo ) ** plazo_flujo
            
            llave1 = moneda + '#' + str(int(plazos[plazos_index[0]]*360)) + '#' + riesgo
            llave2 = moneda + '#' + str(int(plazos[plazos_index[1]]*360)) + '#' + riesgo
    
            alfa = self.solucion_ecuacion(volatilidad_flujo[0], volatilidad.iloc[plazos_index[0]][0], volatilidad.iloc[plazos_index[1]][0], \
                        correlacion[llave1][llave2])
            
            solucion = self.discriminador_sol(alfa)

            flujo_plazos = self.actualizar(solucion, vp_flujo, plazos_index, flujo_plazos)

        self.distribucionPlazos = pd.DataFrame(flujo_plazos)
        



            

            




