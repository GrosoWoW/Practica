import pyodbc

from Activo import *
from Accion import *
from Bono import *
from Derivado import *
from DerivadosTipos.DerivadosSCC import *

# (..., monedaCartera, fecha_valorizacion, cn)


class Cartera:
    def __init__(self, acciones, bonos, derivados, moneda, fecha, cn):
        # Acciones: DataFrame con historico de precios (debe contener 200 datos) ['Moneda', 'Historico']
        # Bono: DataFrame con ['Moneda', 'Riesgo', 'TablaDesarrollo', 'Convencion', 'Nemotecnico', 'FechaEmision]
        # Derivados: Objeto Derivado

        # Aqui se guarda una referencia a cada obj Accion
        self.acciones = []

        # Por cada Accion en el dataFrame
        for i in range(np.size(acciones,0)):

            accion = acciones.iloc[i]
            obj_accion = Accion(accion["Nombre"], accion['Moneda'], pd.DataFrame(accion['Historico'][0]), accion['Inversion'], moneda, fecha, cn)
            self.acciones.append(obj_accion)

        self.bonos = []

        for j in range(np.size(bonos,0)):

            bono = bonos.iloc[j]
            obj_bono = Bono(bono['Riesgo'], bono['Moneda'], bono['TablaDesarrollo'], bono['Convencion'], bono['FechaEmision'], moneda, fecha, cn)
            self.bonos.append(obj_bono)

        self.derivados = []

        for k in range(np.size(derivados,0)):
            derivado = derivados.iloc[k]
            obj_derivado = Derivado(derivado['Derivado'], moneda, fecha, cn)
            self.derivados.append(obj_derivado)

        # Moneda a la que se desea trabajar y valorizar la cartera
        self.moneda = moneda

        # Conexion a base de datos
        self.cn = cn

        # Fecha a la que se desea valorizar
        self.fecha = fecha

        # Historico de todos los activos
        self.historicos_totales = pd.DataFrame()

        # Retornos de todos los activos
        self.retornos_totales = pd.DataFrame()

        # Volatilidades de todos los activos
        self.volatilidades_totales = pd.DataFrame()

        # Convecion para la cantidad de dias en un anio
        self.anio = 360 

        # Plazos a los que se trabajaran los pivotes
        self.plazos = [30/self.anio, 90/self.anio, 180/self.anio, 360/self.anio, 2, 3, 4, 5, 7,\
            9, 10, 15, 20, 30]

        # Correlacion de la cartera
        self.correlacion = pd.DataFrame()

        # Une todos los historicos, retornos y volatilidades de los activos de la cartera
        self.set_hist_ret_vol_totales()

        # Setea la correlacion de la cartera
        self.set_correlacion_total()

        # Covarianza de la cartera
        self.covarianza = pd.DataFrame()

        self.distribuciones_activos()

        self.vector_acciones = []

        self.set_vector_acciones()

        self.vector_bonos = []

        self.set_vector_bonos()

        self.vector_derivados = []

        self.set_vector_derivados()

        self.vector_supremo = []

        self.set_vector_supremo()

        self.set_covarianza()

        self.volatilidad_cartera = 0


    def get_vector_acciones(self):

        """
        Retorna el vector con las acciones.

        """

        return self.vector_acciones
        
    def get_vector_bonos(self):

        """
        Retorna el vector con los bonos.

        """
        
        return self.vector_bonos

    def get_vector_derivados(self):

        """
        Retorna el vector con los derivados.

        """

        return self.vector_derivados
        
    def get_vector_supremo(self):

        """
        Retorna el vector con el retorno de todos los activos.

        """

        return self.vector_supremo

    def get_moneda(self):

        """
        Retorna la moneda en la que se esta trabajando la cartera
        :return: String con la moneda correspondiente

        """

        return self.moneda

    def get_cn(self):

        """
        Retorna la conexion a base de datos de la cartera
        :return: Conexion a db

        """

        return self.cn

    def get_fecha(self):

        """
        Retorna la fecha de valorizacion de la cartera
        :return: date con la fecha de valorizacion

        """

        return self.fecha
        
    def get_acciones(self):

        """
        Retorna todas las acciones de la cartera
        :return: Arreglo con todas las acciones de la cartera
        
        """

        return self.acciones

    def get_bonos(self):

        """
        Retorna todos los bonos de la cartera
        :return: Arreglo con todos los bonos de la cartera

        """

        return self.bonos

    def get_derivados(self):

        """
        Retorna todos los derivados de la cartera
        :return: Arreglo con todos los derivados de la cartera
        
        """

        return self.derivados

    def get_historicos_totales(self):

        """
        Retorna la matriz con todos los historicos de los activos
        :return: DataFrame con los historicos de los activos

        """

        return self.historicos_totales

    def get_retornos_totales(self):

        """
        Retorna la matriz con todos los retornos de los activos
        :return: DataFrame con los retornos de los activos

        """

        return self.retornos_totales

    def get_volatilidades_totales(self):

        """
        Retorna la matriz con todas las volatilidades de los activos
        :return: DataFrame con todas las volatilidades de la cartera

        """

        return self.volatilidades_totales

    def get_plazos(self):

        """
        Retorna los plazos de los pivotes
        :return: Vector con los plazos de los pivotes

        """

        return self.plazos

    def get_correlacion(self):

        """
        Retorna correlacion de la cartera
        :return: DataFrame con la correlacion de la cartera
        
        """

        return self.correlacion
    
    def get_covarianza(self):

        """
        Retorna la covarianza de la cartera
        :return: DataFrame con la covarianza total de la cartera

        """
        return self.covarianza

    def get_volatilidad_cartera(self):

        """
        Retorna la volatilidad total de la cartera
        :return: float con la volatilidad de la cartera

        """

        return self.volatilidad_cartera

    def unir_activos(self, activos):

        """
        Funcion que se encarga de unir los dataframes de historicos,
        retornos y volatilidades de todos los activos que se encuentran
        en la cartera
        :param activos: Arreglo con todos los activos de la cartera
        :return: Arreglo con los tres DataFrame solicitados

        """
        dfHistorico = pd.DataFrame()
        dfRetornos = pd.DataFrame()
        dfVolatilidades = pd.DataFrame()
        largo_activos = len(activos)
        arreglo_nombres = []

        for j in range(largo_activos):

            tipo_activo = activos[j]
            largo_activo = len(tipo_activo)

            for i in range(largo_activo):

                activo_actual = tipo_activo[i]
                historico_activo = activo_actual.get_historicos()
                retorno_activo = activo_actual.get_retornos()
                volatilidad_activo = activo_actual.get_volatilidad()

                nombre_columnas = list(historico_activo)

                if nombre_columnas in arreglo_nombres: continue

                arreglo_nombres.append(nombre_columnas)
        
                dfHistorico = pd.concat([dfHistorico, historico_activo], 1)
                dfRetornos = pd.concat([dfRetornos, retorno_activo], 1)
                dfVolatilidades = pd.concat([dfVolatilidades, volatilidad_activo], 0)

        return [dfHistorico, dfRetornos, dfVolatilidades]

    def set_hist_ret_vol_totales(self):

        """
        Funcion encargada de unir en tres DataFrames 
        los historicos, retornos y volatilidades de los activos
        de la cartera
        
        """

        bonos = self.get_bonos()
        derivados = self.get_derivados()
        acciones = self.get_acciones()
        arreglo_activos = [bonos, derivados, acciones]

        df = self.unir_activos(arreglo_activos)
        
        self.historicos_totales = df[0]
        self.retornos_totales = df[1]
        self.volatilidades_totales = df[2]

    def set_correlacion_total(self):

        """
        Funcion que calcula la correlacion de
        toda la cartera

        """

        largo_pivotes = len(self.get_plazos())
        lenght = len(list(self.get_historicos_totales()))
        volatilidad = self.get_volatilidades_totales()
        retornos = self.get_retornos_totales()
        corr = ewma_matriz(lenght, retornos, volatilidad)
        self.correlacion = corr


            
    def set_covarianza(self):

        """
        Esta funcion se encarga de carcular la matriz de
        covarianza para todos los activos que se encuentran
        en la cartera, la setea en self.covarianza

        """

        corr = self.get_correlacion()
        cor = corr.values
        vol = self.get_volatilidades_totales().iloc[:, 0]
        D = np.diag(vol)
        self.covarianza = pd.DataFrame(np.dot(np.dot(D,cor),D))

    def distribuciones_activos(self):
        
        """
        Calcula la distribucion de todos
        los activos que se encuentran en la cartera
        
        """

        bonos = self.get_bonos()
        derivados = self.get_derivados()

        for i in range(len(bonos)):
            
            bonos[i].set_distribucionPlazos()

        for i in range(len(derivados)):

            derivados[i].set_distribucion_pivotes()

    def set_volatilidad_cartera(self):

        """
        Define la volatilidad de la cartera

        """

        vector = self.get_vector_supremo()
        suma = sum(vector)
        print(vector)

        vector = vector/suma
        covarianza = self.get_covarianza()

        self.volatilidad_cartera = np.sqrt(np.dot(np.dot(vector, covarianza), vector))
        
    def set_vector_acciones(self):

        """
        Concatena el monto de inversion de todas las acciones

        """

        acciones = self.get_acciones()
        n_acciones = len(acciones)
        inversiones = np.zeros(n_acciones)

        for i in range(n_acciones):

            inversiones[i] = acciones[i].get_inversion()
            
        self.vector_acciones = inversiones

    def set_vector_bonos(self):

        """
        Concatena y suma todas las distribuciones de los bonos en sus plazos en virtud del riesgo y la moneda.

        """

        bonos = self.get_bonos()
        n_bonos = len(bonos)
        monedas_riesgos = []
        
        # Extraemos las monedas y riesgos

        for i in range(n_bonos):
            bono = bonos[i]
            llave = bono.get_riesgo()
            if (llave not in monedas_riesgos):
                monedas_riesgos.append(llave)
        
        # Creamos el diccionario para guardar las distribuciones

        distribuciones = {}
        for j in range(len(monedas_riesgos)):
            distribuciones[monedas_riesgos[j]] = pd.DataFrame(np.zeros(len(self.get_plazos())))

        # Para cada bono, identificamos su moneda y riesgo
        
        for k in range(n_bonos):
            bono = bonos[k]
            llave = bono.get_riesgo()
            bono_plazos = bono.get_distribucionPlazos()
            distribuciones[llave] += bono_plazos

        self.vector_bonos = distribuciones

    def set_vector_derivados(self):

        """
        Concatena y suma todas las distribuciones de los derivados en sus plazos en virtud de su moneda.

        """

        derivados = self.get_derivados()
        n_derivados = len(derivados)
        distribucion = pd.DataFrame(np.zeros(len(self.get_plazos())))
        
        for i in range(n_derivados):

            derivado = derivados[i]
            distribucion_plazos = pd.DataFrame(derivado.get_distribucion_pivotes())
            distribucion += distribucion_plazos
        
        self.vector_derivados = distribucion

    def set_vector_supremo(self):
        
        """
        Concatena todos los montos de inversion y vectores de distribución de los activos.

        """
        
        acciones = self.get_vector_acciones()
        bonos = self.get_vector_bonos()
        derivados = self.get_vector_derivados()
        
        vector_supremo = []

        vector_supremo.extend(acciones)
        
        for key in bonos:
            vector_supremo.extend(bonos[key].iloc[:,0])
       

        vector_supremo.extend(derivados.iloc[:,0])

        self.vector_supremo = np.array(vector_supremo)

