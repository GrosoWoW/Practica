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

import numpy as np
import pandas as pd
import datetime

import time
# (..., monedaCartera, fecha_valorizacion, cn)


class Cartera:
    def __init__(self, acciones, bonos, derivados, moneda, fecha, cn, n = 60):
        # Acciones: DataFrame con historico de precios (debe contener 200 datos) ['Moneda', 'Historico']
        # Bono: DataFrame con ['Moneda', 'Riesgo', 'TablaDesarrollo', 'Convencion', 'Nemotecnico', 'FechaEmision]
        # Derivados: Objeto Derivado

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

        self.plazos = []

        # Por cada Accion en el dataFrame
        for i in range(np.size(acciones,0)):

            accion = acciones.iloc[i]
            obj_accion = Accion(accion["Nombre"], accion['Moneda'], pd.DataFrame(accion['Historico'][i]), accion['Inversion'], moneda, fecha, cn, n, "A")
            self.acciones.append(obj_accion)


        self.bonos = []

        for j in range(np.size(bonos,0)):

            bono = bonos.iloc[j]
            obj_bono = Bono(bono['Riesgo'], bono['Moneda'], bono['TablaDesarrollo'], bono['Convencion'], bono['FechaEmision'], moneda, fecha, cn, n)
            
            moneda = obj_bono.get_moneda() 
            riesgo = obj_bono.get_riesgo()
            #bon_act = self.funcion_optimizacion(obj_bono, moneda, riesgo)

            self.bonos.append(obj_bono)

        self.derivados = []

        
        for k in range(np.size(derivados,0)):

            derivado = derivados.iloc[k]
            obj_derivado = Derivado(derivado['Derivado'], moneda_cartera, fecha, cn, n, derivado['Derivado'].get_fecha_efectiva())
            moneda = obj_derivado.get_moneda()
            #derivado_act = self.funcion_optimizacion(obj_derivado, moneda)

            self.derivados.append(obj_derivado)

        if len(bonos) != 0 or len(derivados) != 0:
            self.plazos = self.definir_plazos(self.bonos, self.derivados)

        arreglo_bonos = self.bonos
        arreglo_bonos_nuevo = []

        for l in range(np.size(bonos,0)):

            arreglo_bonos[l].set_plazos(self.plazos)
            moneda = arreglo_bonos[l].get_moneda()
            riesgo = arreglo_bonos[l].get_riesgo()
            bonos_act = self.funcion_optimizacion(arreglo_bonos[l], moneda, riesgo)
            arreglo_bonos_nuevo.append(bonos_act)

        self.bonos = arreglo_bonos_nuevo

        arreglo_derivados = self.derivados
        arreglo_derivados_nuevo = []

        for h in range(np.size(derivados,0)):

            arreglo_derivados[h].set_plazos(self.plazos)
            moneda = arreglo_derivados[h].get_moneda()
            derivado_act = self.funcion_optimizacion(arreglo_derivados[h], moneda)
            arreglo_derivados_nuevo.append(derivado_act)

        self.derivados = arreglo_derivados_nuevo

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

        # Distribuciones de los flujos de los activos
        self.distribuciones_activos()

        self.vector_acciones = []

        self.set_vector_acciones()

        self.vector_bonos = []

        self.set_vector_bonos()

        self.vector_derivados = []

        self.set_vector_derivados()

        self.vector_supremo = []

        self.set_vector_supremo()

        # Covarianza de la cartera
        self.set_covarianza()

        # Volatilidad de la cartera
        self.volatilidad_cartera = 0

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
        print(sum(dict.values()))
        return df

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
            fecha = derivado.get_fecha_efectiva()['FechaFixing'][0]
            fecha = datetime.datetime.combine(fecha, datetime.datetime.min.time())
            tabla_fechas = np.append(tabla_fechas,fecha)
        
        fechas = self.dict_fechas(tabla_fechas)
        
        df = self.dict_to_df(fechas)
        
        n = int(np.size(df,0)*(2/3))
        
        print(df)
        if np.size(df,0) != 1:
            kmeans = KMeans(n_clusters=n).fit(df)

            centroids = pd.DataFrame(kmeans.cluster_centers_).sort_values(0,ascending=True)
            centroids.plot.scatter(x=0, y=1)
            print(centroids[0])

            return centroids[0]
        else:
            print( [int(df['Fechas']/2), int(df['Fechas'])])
            return [int(df['Fechas']/2), int(df['Fechas'])]
        


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

        if nombre in self.historico_dict:

            activo.set_historico(self.historico_dict[nombre])
            activo.set_retorno(self.retorno_dict[nombre])
            activo.set_volatilidad(self.volatilidad_dict[nombre])
            activo.set_correlacion(self.correlacion_dict[nombre])
            activo.set_covarianza(self.covarianza_dict[nombre])

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

        activo.set_distribucion_pivotes()
        activo.set_volatilidad_general()
        return activo


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
            
            bonos[i].set_distribucion_pivotes()

        for i in range(len(derivados)):

            derivados[i].set_distribucion_pivotes()

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