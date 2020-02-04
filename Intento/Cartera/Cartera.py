import datetime
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pyodbc
from Acciones.Acciones import *
from Bonos.Correlaciones import covarianza_pivotes, ewma, ewma_matriz
from Bonos.LibreriasUtiles.UtilesValorizacion import diferencia_dias_convencion
from Bonos.UtilesBonos import *
from Derivados.DerivadosTipos.DerivadosFWD import *
from Derivados.DerivadosTipos.DerivadosSCC import *
from Derivados.DerivadosTipos.DerivadosSUC import *
from Derivados.ValorizacionDerivados import *
from ConversionVolatilidad import retornosMoneda

sys.path.append("..")

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)


# MEJORA: QUE LAS FUNCIONES QUE CREAN ALGO, PREGUNTEN SI ESTA CREADO.


class Cartera:
    def __init__(self, fecha_val, bonos, derivados, acciones, cn, n = 10000):
        """
        Constructor Cartera. Crea DataFrames de derivados y bonos.
        :param fehca_val: Fecha de valorización. Debe coincidir con los datos de instrumentos.
        :param bonos: Arreglo 1-dim. Guarda los nemotecnicos de bonos en str.
        :param derivados: Arreglo 1-dim.. Guarda los ID_keys de derivados en str.
        :param acciones: Arreglo 1-dim. Guarda los nombres de los archivos con las acciones.
        """
        # Fecha valorización.
        self.fecha_val = fecha_val
        
        # Arreglo con nemotecnicos.
        self.bonos = bonos
        
        # Arreglo con ID_Keys.
        self.derivados = derivados
        
        # Arreglo con nombre de archivos acciones.
        self.acciones = acciones
        
        # Inicializar DataFrame con derivados.
        self.dfDerivados = pd.DataFrame(columns=['ID_Key', 'Fecha', 'Administradora', 'Fondo', 'Contraparte', 'Tipo',
                                                 'ID', 'FechaTransaccion', 'FechaFixing', 'TenorFixing',
                                                 'FechaEfectiva',
                                                 'FechaVenc', 'AjusteFeriados', 'Mercado', 'Nemotecnico', 'Referencia',
                                                 'NocionalActivo', 'MonedaActivo', 'FrecuenciaActivo', 'TipoTasaActivo',
                                                 'TasaActivo', 'SpreadActivo', 'NocionalPasivo', 'MonedaPasivo',
                                                 'FrecuenciaPasivo', 'TipoTasaPasivo', 'TasaPasivo', 'SpreadPasivo',
                                                 'MonedaBase'])
        # Inicializar DataFrame con bonos.
        self.dfBonos = pd.DataFrame(columns=['Fecha', 'Familia', 'Nemotecnico', 'Emisor', 'TipoInstr', 'TasaEmision',
                                             'Tera', 'Moneda', 'Monto', 'CorteMin', 'CorteMax', 'Plazo',
                                             'FechaEmision', 'FechaVenc', 'FechaPrepago', 'PorcentajePrepagado',
                                             'Pago', 'nCup', 'nAmort', 'TablaDesarrollo', 'PrimeraTransa',
                                             'MontoPrimeraTransa', 'CodBancario', 'Cusip', 'Isin', 'Bloomberg',
                                             'TipoLva', 'FechaColocacion', 'Base1', 'Base2', 'Estructura',
                                             'MontoColocado'])
        # Conexión a base de datos.
        self.cn = cn
        
        # Dictionario con derivados como objetos. Llaves son los ID_Key. El orden calza con el arreglo derivados.
        self.objDerivados = {key: None for key in derivados}

        self.creaDfDerivados() # Creacion del DataFrame de los derivados
        self.crearObjDerivados()  # Creacion de los derivados
        self.creaDfBonos() # Creacion de los bonos

        # Cantidad de dias para analizar historico
        self.n = n

        # Monedas.
        self.monedas_bonos = self.optimizar_monedas_bonos()
        self.monedas_derivados = self.optimizar_monedas_derivados()
    
        # Pivotes.
        self.pivotes = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]


        # Retornos de todos los instrumentos en la cartera.
        self.retornos = self.retornos_totales()

        # Volatilidades de cada instrumento en la cartera.
        self.volatilidades = self.vol_totales()

        # Matriz de correlaciones.
        self.corr = self.correlaciones_totales()

        # Matriz de covarianza
        self.cov = self.covarianza_total(self.corr, self.volatilidades)

        # Pivotes de derivados
        self.pivotes_derivados = dict()

        # Pivotes de bonos
        self.pivotes_bonos = dict()


    def optimizar_monedas_bonos(self):

        """
        Funcion que extrae las monedas de todos los datos relacionados
        a bonos con su respectivo riesgo y los incluye en la clase

        """

        monedas_bonos = []
        moneda_bono = self.dfBonos["Moneda"]

        for i in range(len(moneda_bono)):

                nemotecnico_bono = self.dfBonos["Nemotecnico"][i]
                fecha_bono = str(self.dfBonos["Fecha"][i])
                riesgo_num = riesgoBono(nemotecnico_bono, fecha_bono)
                riesgo_valor = conversionSYP(riesgo_num)
                str_final = moneda_bono[i] + "#" + riesgo_valor
                if str_final not in monedas_bonos:
                    monedas_bonos.append(str_final)
    
        return monedas_bonos

    def optimizar_monedas_derivados(self):

        """
        Funcion que extrae las monedas de todos los datos relacionados
        a derivados

        """

        moneda_derivado_activo = self.dfDerivados["MonedaActivo"]
        moneda_derivado_pasivo = self.dfDerivados["MonedaPasivo"]
        monedas_derivados = []
        for i in range(len(moneda_derivado_activo)):

            if moneda_derivado_activo[i] not in monedas_derivados:

                monedas_derivados.append(moneda_derivado_activo[i])

            if moneda_derivado_pasivo[i] not in monedas_derivados:

                monedas_derivados.append(moneda_derivado_pasivo[i])
        
        return monedas_derivados

    def creaDfBonos(self):
        """
        Rellena el DataFrame de los bonos en la cartera. Toma el bono más reciente que encuentra en la
        base de datos. El i-ésimo elemento de self.bonos corresponde a la i-ésima fila del DataFrame.
        :return:
        """
        for bon in self.bonos:
            fila = ("SELECT TOP (1) * FROM[dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = '" + bon + "'")
            fila = pd.read_sql(fila, self.cn)
            self.dfBonos = self.dfBonos.append(fila, ignore_index=True)

    def creaDfDerivados(self):
        """
        Rellena el DataFrame de los derivados en la cartera.
        :return:
        """

        for der in self.derivados:
            fila = ("SELECT TOP (1) * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] WHERE ID_Key = '" + der + "'")
            fila = pd.read_sql(fila, self.cn)
            self.dfDerivados = self.dfDerivados.append(fila, ignore_index=True)

    def crearObjDerivados(self):
        """
        Llena el diccionario de los derivados como objetos.
        :return:
        """

        for id_key in self.derivados:
            self.objDerivados[id_key] = extraer_crear_derivado(id_key)

    def dict_to_vector(self):

        """
        Funcion encargada de generar el diccionario que
        se utilizara para la distribucion de pivotes
        este se hace dependiendo las monedas que se hayan
        extraido de los derivados e bonos

        """

        diccionario_bonos = self.get_pivotes_bonos()
        diccionario_derivados = self.get_pivotes_derivados()

        vector_vectores = []
        dic_pivote = []

        for key in diccionario_bonos:
    
            dic_pivote.append(diccionario_bonos[key])

        vector_vectores.append(dic_pivote)
        dic_pivote = []

        for key in diccionario_derivados:

            dic_pivote.append(diccionario_derivados[key])

        vector_vectores.append(dic_pivote)
        return vector_vectores
    
    def get_retAcciones(self):
        """
        Calcula y retorna el retorno.
        :return: pd.DataFrame con los retornos de las acciones en la cartera.
        """
        return retorno_varias_acciones(self.acciones)

    def get_volAcciones(self, df_retornos):
        """
        Calcula y retorna las volatilidades.
        :param: df_retornos: pd.DataFrame con los retornos de las acciones en la cartera.
        :return: pd.DataFrame con las volatilidades de las acciones en la cartera.
        """
        return calculo_volatilidades_acciones(df_retornos)
    
    
    def get_retCurvas(self, n):
        """
        Calcula y retorna el retorno de curvas de bonos y derivados.
        :param n: Cantidad de curvas.
        :return: pd.DataFrame con los retornos de las curvas de bonos y derivados. Orden: derivados-bonos.
        """
        arr = []
        arr1 = []
        # Retornos derivados.
        for moneda in self.monedas_derivados:

            dfHistorico = calculo_historico(vector_dias, moneda, n)
            print(retornosMoneda(moneda, n))
            retorno_moneda = retornosMoneda(moneda, n)["Retorno"].values
            
            aux = calcular_retornos(dfHistorico, retorno_moneda)
            arr.append(aux)

        # Retornos Bonos. 
        for mon in self.monedas_bonos:
            if mon == "EUR": continue
    
            riesgo = mon.split("#")[1]
            moneda = mon.split("#")[0]

            col = nombre_columna(moneda, self.pivotes, riesgo)
            dfHistorico = historicoPlazos(riesgo, moneda, np.array(self.pivotes)/360, np.arange(len(self.pivotes)), n)
            dfHistorico = pd.DataFrame(dfHistorico, columns= col)#uwu

            retorno_moneda = retornosMoneda(moneda, n)["Retorno"].values

            aux = calcular_retornos(dfHistorico, retorno_moneda)
 
            arr1.append(dfHistorico)
            arr.append(aux)

        arreglo_final = arr[0]
        historicos = arr1[0]
        for i in np.arange(1, len(arr)):
            arreglo_final = pd.concat([arreglo_final, arr[i]], 1)
        
        for i in np.arange(1, len(arr1)):
            historicos = pd.concat([historicos, arr1[i]], 1)
        
        return arreglo_final
        
    def get_volCurvas(self, retornoCurvas):
        """
        param retornoCurvas: DataFrame. Retorno de instrumentos que usan curvas. (Derivados y Bonos)
        Retorna volatilidades de los instrumentos que se valorizan con curvas.

        """
        return volatilidades_derivados(retornoCurvas)

    def get_volatilidades(self):
        
        return self.volatilidades
    
    def getDfBonos(self):

        """
        Retorna un DataFrame con los bonos

        """
        return self.dfBonos

    def getDfDerivados(self):

        """
        Retorna un DataFrame con los derivados
        
        """
        return self.dfDerivados

    def getObjDerivados(self):

        """
        Retorna un diccionario con los derivados, la key es su id_key

        """
        return self.objDerivados

    def get_pivotes_derivados(self):

        """
        Retorna un diccionario con los pivotes y su distribucion

        """
        return self.pivotes_derivados

    def get_pivotes_bonos(self):
        """
        Retorna un diccionario con los pivotes y su distribucion

        """
        return self.pivotes_bonos


    def get_correlaciones(self):

        """
        Retorna las correlaciones de la cartera

        """

        return self.corr

    def get_retornos(self):

        """
        Retorna los retornos de la cartera

        """

        return self.retornos

    def get_covarianza(self):

        """
        Retorna la covarianza de la cartera

        """
        return self.cov

    def volatilidades_cartera(self, dfRetornos):
        
        """
        Funcion encargada de calcular las volatilidades de ciertos retornos
        Estas volatilidades estan calculadas con la funcion ewma, lambda 0.94
        :param dfRetornos: DataFrame con los retornos a los que se les calcularan las volatilidades (pasado-->futuro)
        :return DataFrame con las volatilidades de cada pivote

        """
        # Numero de columnas.
        M = np.size(dfRetornos, 1)
        # Nombre de las columnas.
        nom_columnas = dfRetornos.columns
        # DataFrame con volatilidades.
        df = pd.DataFrame()
        valores = []

        for i in range(M):
            # Toma columna i.
            retornos = dfRetornos[nom_columnas[i]]
            valor = ewma(retornos, 0.94)
            valores.append(valor["Vol c/ajuste"].values[0])
        
        df["Volatilidades"] = valores
        return df

    def vol_totales(self):

        """
        Retorna un DataFrame con las volatilidades
        totales de todo el conjunto de acciones, derivados y bonos

        """

        vol_total = self.volatilidades_cartera(self.retornos)
        df = pd.DataFrame()
        df["Nombres"] = self.retornos.columns  # Para identificar con nombre a cual corresponde
        df_final = pd.concat([df, vol_total], 1)

        return df_final

    def calculoPivote_derivados(self):
        
        """
        Funcion encargada de calcular la distribucion de los pivotes.
        pivotes_derivados es un diccionario que guarda los vectores con las proyecciones.
        """

        self.pivotes_derivados = calculo_derivado(self.objDerivados, self.fecha_val, self.corr, self.monedas_derivados)

    def calculoPivote_bonos(self):
        """
        Funcion encargada de calcular la distribucion de los pivotes
        pivotes_derivados es un diccionario que guarda los vectores con las proyecciones.
        """
        fecha_val_str = self.fecha_val.strftime("%Y-%m-%d")
        self.pivotes_bonos = proyeccionBonos(self.bonos, np.array(self.pivotes)/360, fecha_val_str, self.getDfBonos(), self.corr, self.volatilidades, self.monedas_bonos)

    def retornos_totales(self):
        """
        Retorno de todos los derivados. Orden: acc-der-bon.
        :return pd.DataFrame. Retornos de todos los instrumentos en la cartera.
        """
        
        ret_acciones = self.get_retAcciones()
        self.n = min(self.n, np.size(ret_acciones, 0))

        ret_curvas = self.get_retCurvas(self.n)
        
        return pd.concat([ret_acciones, ret_curvas], 1)

    def correlaciones_totales(self):

        """
        Calcula la correlacion de todos los conjuntos de bonos
        derivados y acciones

        """

        retornos = self.retornos
        cantidad_columnas = len(retornos.iloc[1])
        corr = ewma_matriz(cantidad_columnas, retornos, self.volatilidades)
        return corr

    def covarianza_total(self, cor, vol):
        """
        Calcula matriz de covarianzas.
        :param cor: DataFrame con la matriz de correlacion.
        :param vol: DataFrame con las volatilidades :3
        """
        cor = cor.values
        vol = vol["Volatilidades"].values
        D = np.diag(vol)
        return pd.DataFrame(np.dot(np.dot(D,cor),D))
        
miCartera = Cartera(datetime.date(2018, 4, 18), ["BSTDU10618"], ["147951", "147949"], ["BSANTANDER.SN.xlsx"], cn)
ret = miCartera.get_retornos()
pd.get_option("display.max_rows")
pd.get_option("display.max_columns")

miCartera.calculoPivote_bonos()
miCartera.calculoPivote_derivados()
