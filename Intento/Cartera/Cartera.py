import pyodbc
import matplotlib.pyplot as plt
import seaborn as sb
from sklearn.cluster import KMeans

from Activo import *
from Accion import *
from Bono import *
from Derivado import *
from DerivadosTipos.DerivadosSCC import *
from UtilesValorizacion import StrTabla2ArrTabla, diferencia_dias_convencion
from Correlaciones import ewma_matriz

import numpy as np
import pandas as pd
import datetime

import time

class Cartera:
    def __init__(self, acciones, bonos, derivados, moneda, fecha, cn, n = 60):

        # Acciones: DataFrame con todas las acciones de la cartera (debe contener 60 datos) 
        # Las columnas del dataframe necesarias son ["Moneda", "Nombre", "Nemotecnico", "Inversion", "Historico"]
        # Es importante señalar que este historico corresponde al de retornos

        # Bono: DataFrame con los bonos de la cartera 
        # Las columnas del dataframe necesarias son ["Moneda", "TablaDesarrollo", "FechaEmision", "Nemotecnico", "Convencion", "Riesgo"]

       
        # Derivados: DataFrame con todos los derivados de la cartera
        # Las columnas necesarias del dataframe son ["ObjetoDerivado", "Nemotecnico"], las clases de derivados
        # Se encuentran en la carpeta DerivadosTipos y fueron creadas por Matias Villega
        

        moneda_cartera = moneda

        # Esta variable define la cantidad de datos que se toma para historicos
        self.n = n

        # Aqui se guarda una referencia a cada obj Accion
        self.acciones = []

        # Diccionarios donde se incluiran todos los calculos
        self.historico_dict = dict()
        self.retorno_dict = dict()
        self.volatilidad_dict = dict()
        self.correlacion_dict = dict()
        self.covarianza_dict = dict()

        # Moneda a la que se desea trabajar y valorizar la cartera
        self.moneda = moneda

        # Conexion a base de datos
        self.cn = cn

        # Fecha a la que se desea valorizar
        self.fecha = fecha

        # Plazos para la creacion de los pivotes
        self.plazos = []


        # Por cada Accion en el dataFrame, se crea con la clase accion
        for i in range(np.size(acciones,0)):

            # Se obtiene la fila i del dataframe de las acciones
            accion = acciones.iloc[i]

            # Se crea objeto accion con la clase Accion 
            obj_accion = Accion(accion["Nombre"], accion['Moneda'], pd.DataFrame(accion['Historico'][0]), accion['Inversion'], moneda, fecha, cn, n, "A", accion['Nemotecnico'])
            
            # Se agrega al arreglo de acciones en la cartera
            self.acciones.append(obj_accion)

        self.bonos = []

        # Por cada bono en el dataframe se crea un objeto bono
        for j in range(np.size(bonos,0)):

            # Se obtiene la fila i del dataframe de bonos
            bono = bonos.iloc[j]

            # Se crea el objeto bono con la clase Bono
            obj_bono = Bono(bono['Riesgo'], bono['Moneda'], bono['TablaDesarrollo'], bono['Convencion'], bono['FechaEmision'], moneda, fecha, cn, n, bono['Nemotecnico'])
            
            # Se agrega al arreglo de bonos en la cartera
            self.bonos.append(obj_bono)

        self.derivados = []

        # Por cada derivado en el dataframe, se crea un objeto derivado
        for k in range(np.size(derivados,0)):

            # Se obtiene la fila i del dataframe de derivados
            derivado = derivados.iloc[k]

            # Se crea el objeto derivado con la clase Derivado
            obj_derivado = Derivado(derivado['Derivado'], moneda_cartera, fecha, cn, n, derivado['Derivado'].get_fecha_efectiva(), derivado['Nemotecnico'])
            
            # Se agrega al arreglo de derivados de la cartera
            self.derivados.append(obj_derivado)

        if len(bonos) != 0 or len(derivados) != 0:
            self.plazos = self.definir_plazos(self.bonos, self.derivados)

        self.diccionario_niveles = dict()
        self.lista_nivel1 = self.set_lista_niveln(1)

        arreglo_bonos = self.bonos
        arreglo_bonos_nuevo = []

        # Por cada objeto bono, se calculan sus datos (historicos, retornos, etc)
        for l in range(np.size(bonos,0)):

            arreglo_bonos[l].set_plazos(self.plazos)
            moneda = arreglo_bonos[l].get_moneda()
            riesgo = arreglo_bonos[l].get_riesgo()
            bonos_act = self.funcion_optimizacion(arreglo_bonos[l], moneda, riesgo) # Optimiza el calculo
            arreglo_bonos_nuevo.append(bonos_act)

        self.bonos = arreglo_bonos_nuevo # Reemplazamos los bonos, listos con todos sus calculos

        arreglo_derivados = self.derivados
        arreglo_derivados_nuevo = []

        # Por cada objeto derivado, se calculan sus datos (historicos, retornos, etc)
        for h in range(np.size(derivados,0)):

            arreglo_derivados[h].set_plazos(self.plazos)
            moneda = arreglo_derivados[h].get_moneda()
            derivado_act = self.funcion_optimizacion(arreglo_derivados[h], moneda) # Se optimiza el calculo
            arreglo_derivados_nuevo.append(derivado_act)

        self.derivados = arreglo_derivados_nuevo # Reemplazamos los derivos, listos con sus calculos

        # Historico de todos los activos
        self.historicos_totales = pd.DataFrame()

        # Retornos de todos los activos
        self.retornos_totales = pd.DataFrame()

        # Volatilidades de todos los activos
        self.volatilidades_totales = pd.DataFrame()

        # Correlacion de la cartera
        self.correlacion = pd.DataFrame()

        # Une todos los historicos, retornos y volatilidades de los activos de la cartera
        self.set_hist_ret_vol_totales()

        # Setea la correlacion de la cartera
        self.set_correlacion_total()

        # Covarianza de la cartera
        self.covarianza = pd.DataFrame()

        # Vector con valor presente de las acciones
        self.vector_acciones = []

        # Setea el vector con todas las inversiones de las acciones
        self.set_vector_acciones()

        # Vector con el valor presente de los bonos
        self.vector_bonos = []

        # Setea el vector con la suma de todas las distribuciones de los bonos
        self.set_vector_bonos()

        # Vector con el valor presente de los derivados
        self.vector_derivados = []

        # Setea el vector con la suma de todas las distribuciones de los pivotes
        self.set_vector_derivados()

        # Vector con todas las distribuciones de los bonos, derivados y la inversion de las acciones
        self.vector_supremo = []

        # Setea el calculo del vector supremo
        self.set_vector_supremo()

        # Covarianza de la cartera
        self.set_covarianza()

        # Volatilidad de la cartera
        self.volatilidad_cartera = 0

        # Diccionario de volatilidades por niveles
        self.diccionario_vol_niveles = dict()

        # Setea las volatilidades por niveles
        self.set_volatilidad_niveles()

        # -------------------- TRABAJO POR NIVELES ---------------------

    def get_volatilidad_niveles(self):

        """
        Retorna un diccionario con las volatilidades por volumen y tipo de activo

        """

        return self.diccionario_vol_niveles

    def get_diccionario_niveles(self):

        """
        Retorna el diccionario con el calculo de valor presente de los niveles
        de los activos

        """

        return self.diccionario_niveles
        
    def get_n(self):

        """
        Retorna el parametro self.n correpondiente a la cantidad
        de datos que se desean obtener de historicos

        """

        return self.n

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

    def dict_fechas(self, tabla):

        fecha_valorizacion = self.get_fecha()

        fechas = dict()
        for i in range(len(tabla)):
            if tabla[i].date() >= fecha_valorizacion:
                if (tabla[i].date() not in fechas.keys()) :
                    fechas[tabla[i].date()] = 1
                else:
                    fechas[tabla[i].date()] += 1
        return fechas

    def dict_to_df(self, dict):

        fecha_valorizacion = self.get_fecha()

        df = pd.DataFrame()
        df['Fechas'] = dict.keys()
        df['Frecuencia'] = dict.values()
        df['Fechas'] = df['Fechas'].apply(lambda x: diferencia_dias_convencion('ACT/360', fecha_valorizacion, x))
        
        return df

    def limpieza_datos(self, df):

        n = np.size(df,0)
        plazos = []
        for i in range(n):
            if df[0][i] == 0 : df[0][i] = 10
            fecha = (df[0][i] + 1)/365
            plazos.extend([fecha])
        return plazos

    def definir_plazos(self, bonos, derivados):

        n_bonos = len(bonos)
        n_derivados = len(derivados)

        tabla_fechas = np.array([])

        # Extraemos la data de los bonos
        for i in range(n_bonos):
            bono = bonos[i]
            tabla = StrTabla2ArrTabla(bono.get_cupones(), bono.get_fecha_emision())
            fechas = tabla[:,1]
            tabla_fechas = np.append(tabla_fechas,fechas)

        # Extraemos la data de los derivados
        for j in range(n_derivados):
            derivado = derivados[j]
            flujos = derivado.get_derivado_generico().flujos_valorizados[["ID","ActivoPasivo", "Fecha"\
            , "FechaFixing", "FechaFlujo", "FechaPago", "Flujo", "ValorPresenteMonFlujo", "Moneda", "MonedaBase"]]
            for l in range(np.size(flujos,0)):
                fecha = flujos.iloc[l]['FechaFixing']
                fecha = datetime.datetime.combine(fecha, datetime.datetime.min.time())
                tabla_fechas = np.append(tabla_fechas,fecha)
        
        fechas = self.dict_fechas(tabla_fechas)
        
        df = self.dict_to_df(fechas)
        
        n = int(np.size(df,0)*(3/4))
        
        if np.size(df,0) != 1:
            kmeans = KMeans(n_clusters=n).fit(df)

            centroids = pd.DataFrame(kmeans.cluster_centers_).sort_values(0,ascending=True).reset_index(drop=True)
            centroids.plot.scatter(x=0, y=1)
            plazos = self.limpieza_datos(centroids)
            
            return plazos
        else:
            return [int(df['Fechas']/2), int(df['Fechas'])]

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

    def funcion_optimizacion(self, activo, moneda, riesgo=""):

        """
        Funcion encargada de optimizar el calculo de historicos, retornos,
        volatilidades, correlacion y covarianzas, para esto utiliza un diccionario
        donde incluye los calculos que no se encuentran realizados para su futura
        utilizacion
        :param activo: Activo al que se desea optimizar su calculo
        :param moneda: Moneda del activo
        :param riesgo: Riesgo del activo
        :return: Activo con todos los datos necesarios

        """

        nombre = moneda+riesgo

        # Si el calculo de datos ya se hizo para esa moneda+riesgo, se extrae del diccionario
        if nombre in self.historico_dict:

            activo.set_historico(self.historico_dict[nombre])
            activo.set_retorno(self.retorno_dict[nombre])
            activo.set_volatilidad(self.volatilidad_dict[nombre])
            activo.set_correlacion(self.correlacion_dict[nombre])
            activo.set_covarianza(self.covarianza_dict[nombre])

        # Si el calculo de datos no se ha realizado, se calcula y se introduce en el activo y diccionario
        else:

            historico_calculado = activo.calcular_historico()
            self.historico_dict[nombre] = historico_calculado

            retorno_calculado = activo.calcular_retorno(moneda)
            self.retorno_dict[nombre] = retorno_calculado

            volatilidad_calculada = activo.calcular_volatilidad()
            self.volatilidad_dict[nombre] = volatilidad_calculada

            correlacion_calculada = activo.calcular_correlacion()
            self.correlacion_dict[nombre] = correlacion_calculada

            covarianza_calculada = activo.calcular_covarianza()
            self.covarianza_dict[nombre] = covarianza_calculada

        # Se realiza el calculo de distribuciones para los activos
        activo.set_distribucion_pivotes(self.get_diccionario_niveles())

        # Se calcula la volatilidad del activo
        activo.set_volatilidad_general()
        return activo


    def set_lista_niveln(self, n):

        """
        Funcion encargada de crear y organizar los niveles de los activos
        Para esto existe diccionario_tipos_nivel, diccionario que clasifica los tipos 
        de niveles segun sus activos y diccionario_niveles que sera un diccionario 
        que contiene los arreglos con los calculos de valor presente que se
        utilizaran luego en el calculo de volatilidades por nivel

        """

        acciones = self.get_acciones()
        bonos = self.get_bonos()
        derivados = self.get_derivados()

        cantidad_acciones = len(acciones)
        cantidad_bonos = len(bonos)
        cantidad_derivados = len(derivados)

        diccionario_tipos_nivel = dict()
        diccionario_niveles = {1:dict(), 2: dict()}

        # Por cada accion en la cartera
        for i in range(cantidad_acciones):

            # Se clasifica en diccionario_tipos_nivel, para organizarlo
            if acciones[i].get_niveln(n) not in diccionario_tipos_nivel.keys():
                diccionario_tipos_nivel[acciones[i].get_niveln(n)] = [acciones[i]]
                
            else:
                diccionario_tipos_nivel[acciones[i].get_niveln(n)].append(acciones[i])
            
            # Se crea la llave de la accion en el diccionario que contendra las inversiones de cada nivel
            # Las llaves son [nombre_nivel, "Accion"] donde "Accion corresponde al tipo de activo"
            for a in range(1,3):
                diccionario_niveles[a][acciones[i].get_niveln(a), "Accion"] = np.zeros(cantidad_acciones)
                diccionario_niveles[a][acciones[i].get_niveln(a), "Accion"][i] += acciones[i].get_inversion()

        # Por cada bono en la cartera
        for j in range(cantidad_bonos):

            # Si su nivel no se encuentra en el diccionario, se crea y se introduce el activo
            if bonos[j].get_niveln(n) not in diccionario_tipos_nivel.keys():
                diccionario_tipos_nivel[bonos[j].get_niveln(n)] = [bonos[j]]

            # Si el nivel esta en el diccionario, solo se introduce el activo
            else:
                diccionario_tipos_nivel[bonos[j].get_niveln(n)].append(bonos[j])

            # Para cada nivel del activo, se crea una llave con los datos del nivel y en el se pone un arreglo de distribuciones
            # La llave para el bono sera [nombre_nivel, "Bono", nombre_riesgo] donde "Bono" corresponde al tipo de activo
            for a in range(1,3):
                diccionario_niveles[a][bonos[j].get_niveln(a), "Bono", bonos[j].get_riesgo()] = np.zeros(len(self.get_plazos()))

            
        # Se realiza el mismo proceso para el derivado pero en este caso, las llaves de diccionario_niveles sera
        # [nombre_nivel, "Derivado"], donde "Derivado" corresponde al nombre del activo
        for k in range(cantidad_derivados):

            if derivados[k].get_niveln(n) not in diccionario_tipos_nivel.keys():
                diccionario_tipos_nivel[derivados[k].get_niveln(n)] = [derivados[k]]
            else:
                diccionario_tipos_nivel[derivados[k].get_niveln(n)].append(derivados[k])

            for a in range(1,3):
                diccionario_niveles[a][derivados[k].get_niveln(a), "Derivado"] = np.zeros(len(self.get_plazos()))

        self.diccionario_niveles = diccionario_niveles
        return diccionario_tipos_nivel

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

    def set_volatilidad_cartera(self):

        """
        Define la volatilidad de la cartera

        """

        vector = self.get_vector_supremo()
        suma = sum(vector)

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
        if(n_derivados == 0): distribucion = pd.DataFrame()
        
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
       
        if (not derivados.empty):
            vector_supremo.extend(derivados.iloc[:,0])

        self.vector_supremo = np.array(vector_supremo)

    def set_volatilidad_niveles(self):
        
        vol_niveles = {1:dict(), 2:dict()}

        niveles = self.get_diccionario_niveles()

        covarianza = self.get_covarianza()

        size = np.size(covarianza,1)
        n_acciones = len(self.get_acciones())
        n_derivados = len(self.get_plazos())

        vector = np.zeros(size)

        # Recordemos que la estructura del vector es bajo el siguiente orden
        # [Bonos/plazos/riesgo][Derivados/plazos][Acciones]
        # Bonos: np.size(covarianza,1) - Derivados - Acciones
        # Derivados : len(self.get_plazos())
        # Acciones : len(self.get_acciones())
        
        
        # Por cada nivel
        for a in range(1,3):
            # Para cada tipo de activo
            for keys in niveles[a]:

                if keys[1] == 'Accion':

                    vector[(size - n_acciones):] = niveles[a][keys[0], keys[1]]
                    
                elif keys[1] == 'Bono':
                    
                    vector[:(size - n_derivados - n_acciones)] = niveles[a][keys[0], keys[1], keys[2]]

                elif keys[1] == 'Derivado':
                    
                    vector[(size - n_derivados - n_acciones):(size - n_acciones)] = niveles[a][keys[0], keys[1]]

                
                vector = vector / sum(vector)
                
                vol_niveles[a][keys] = np.sqrt(np.dot(np.dot(vector,covarianza),vector))
       

        self.diccionario_vol_niveles = vol_niveles