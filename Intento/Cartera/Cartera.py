import datetime
import sys
import time
sys.path.append("..")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import pyodbc
from Acciones.Acciones import *
from Bonos.Correlaciones import covarianza_pivotes, ewma, ewma_new_new_pivotes
from Bonos.LibreriasUtiles.UtilesValorizacion import diferencia_dias_convencion
from Derivados.DerivadosTipos.DerivadosFWD import *
from Derivados.DerivadosTipos.DerivadosSCC import *
from Derivados.DerivadosTipos.DerivadosSUC import *
from Derivados.ValorizacionDerivados import *
from Bonos.UtilesBonos import *

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)


# MEJORA: QUE LAS FUNCIONES QUE CREAN ALGO, PREGUNTEN SI ESTA CREADO.


class Cartera:
    def __init__(self, fecha_val, bonos, derivados, acciones, cn):
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

        self.creaDfDerivados()
        self.crearObjDerivados()  # Creacion de los derivados
        self.creaDfBonos() # Creacion de los bonos

        # Monedas.
        self.monedas = self.optimizar_monedas()
        print(self.monedas)
        #Riesgos.
        self.riesgos = self.optimizar_riesgos()
        print(self.riesgos)
        
        # Pivotes.
        self.pivotes = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

        # Retornos de todos los instrumentos en la cartera.
        self.retornos = self.retornos_totales()

        # Matriz de correlaciones.
        self.corr = self.correlaciones()

        # Volatilidades de cada instrumento en la cartera.
        self.volatilidades = self.volTotales()

        # Diccionario para obtener indice según moneda y riesgo.
        self.indices_matriz = {(j, k) : len(self.acciones) + len(self.derivados) * len(self.monedas) * len(self.pivotes) + j * len(self.riesgos) * len(self.pivotes) 
        + k * len(self.pivotes) for j in range(len(self.monedas)) for k in range(len(self.riesgos)) }


        print(self.riesgos)



    def optimizar_monedas(self):

        """
        Funcion que extrae las monedas de todos los datos y
        los pone en el parametro self.monedas

        """

        monedas = []
        moneda_bono = self.dfBonos["Moneda"]
        for i in range(len(moneda_bono)):

            if moneda_bono[i] not in monedas:

                monedas.append(moneda_bono[i])

        moneda_derivado = self.dfDerivados["MonedaBase"]
        print(self.dfDerivados)
        for i in range(len(moneda_derivado)):

            if moneda_derivado[i] not in monedas:

                monedas.append(moneda_derivado[i])

        return monedas

    def optimizar_riesgos(self):

        """
        Funcion que extrae los riesgos
        de todos los bonos y los pone en self.bonos

        """

        riesgos = []
        nemo_bono = self.dfBonos["Nemotecnico"]
        fechas_bonos = self.dfBonos["Fecha"]
        for i in range(len(fechas_bonos)):


            riesgo = riesgoBono(nemo_bono[i], fechas_bonos[i].strftime("%Y-%m-%d"))
            print(riesgo)
            riesgo = conversionSYP(riesgo)
            if riesgo not in riesgos:

                riesgos.append(riesgo)

        return riesgos


    def creaDfBonos(self):
        """
        Rellena el DataFrame de los bonos en la cartera. Toma el bono más reciente que encuentra en la
        base de datos. El i-ésimo elemento de self.bonos corresponde a la i-ésima fila del DataFrame.
        :return:
        """
        bonos = self.bonos
        cn = self.cn
        for bon in bonos:
            fila = ("SELECT TOP (1) * FROM[dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = '" + bon + "'")
            fila = pd.read_sql(fila, cn)
            self.dfBonos = self.dfBonos.append(fila, ignore_index=True)

    def creaDfDerivados(self):
        """
        Rellena el DataFrame de los derivados en la cartera.
        :return:
        """
        derivados = self.derivados
        cn = self.cn

        for der in derivados:
            fila = ("SELECT TOP (1) * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] WHERE ID_Key = '" + der + "'")
            fila = pd.read_sql(fila, cn)
            self.dfDerivados = self.dfDerivados.append(fila, ignore_index=True)

    def crearObjDerivados(self):
        """
        Llena el diccionario de los derivados como objetos.
        :return:
        """
        for id_key in self.derivados:
            self.objDerivados[id_key] = extraer_crear_derivado(id_key)
    
 
    def get_retAcciones(self):
        """
        Calcula y retorna el retorno.
        :return: pd.DataFrame con los retornos de las acciones en la cartera.
        """
        acciones = self.acciones
        return retorno_varias_acciones(acciones)

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
        for moneda in self.monedas:
            dfHistorico = calculo_historico(vector_dias, moneda, n)
            aux = calcular_retornos(dfHistorico)
            arr.append(aux)

        # Retornos Bonos. 
        for mon in self.monedas:
            for riesgo in self.riesgos:
                col = nombre_columna(mon, riesgo, self.pivotes)
                hist = historicoPlazos(riesgo, mon, np.array(self.pivotes)/360, np.arange(len(self.pivotes)), n)
                hist = pd.DataFrame(hist, columns=col)#uwu
                arr1.append(hist)
                arr.append(calcular_retornos(hist))

        arreglo_lindo = arr[0]
        historicos = arr1[0]
        for i in np.arange(1, len(arr)):
            arreglo_lindo = pd.concat([arreglo_lindo, arr[i]], 1)
        
        for i in np.arange(1, len(arr1)):
            historicos = pd.concat([historicos, arr1[i]], 1)
        
        historicos.to_excel("historicos.xlsx")
        return arreglo_lindo
        

    def get_volCurvas(self, retornoCurvas):
        """
        param retornoCurvas: DataFrame. Retorno de instrumentos que usan curvas. (Derivados y Bonos)
        Retorna volatilidades de los instrumentos que se valorizan con curvas.

        """
        # Agregar calculo de volatilidades de bonos. No me eches we
        a = volatilidades_derivados(retornoCurvas)
        return a#:O

    def volTotales(self):

        vol_bacan = self.volatilidades_cartera(self.retornos)
        df = pd.DataFrame()
        df["Nombres"] = self.retornos.columns
        matriz_final = pd.concat([df, vol_bacan], 1)

        

        return matriz_final

    def get_volatilidades(self):
        
        return self.volatilidades

        
    def retornos_totales(self):
        """
        Retorno de todos los derivados. Orden: acc-der-bon.
        :return pd.DataFrame. Retornos de todos los instrumentos en la cartera.
        """
        ret_curvas = self.get_retCurvas(100)
        ret_acciones = self.get_retAcciones()

        return pd.concat([ret_acciones, ret_curvas], 1)

    def correlaciones(self):

        retornos = self.retornos
        retornos.to_excel("retornos.xlsx")  

        cantidad_columnas = len(retornos.iloc[1])
        corr = ewma_new_new(cantidad_columnas, retornos)
        return corr
        
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
        # Diccionario por moneda.
        dic = self.pivotes_derivados
        # Keys.
        keys = dic.keys()

        return self.pivotes_derivados

    def calculoPivote_derivados(self):
        
        """
        Funcion encargada de calcular la distribucion de los pivotes.
        pivotes_derivados es un diccionario que guarda los vectores con las proyecciones.
        """

        self.pivotes_derivados = calculo_derivado(self.objDerivados, self.fecha_val, self.corr)

    def get_pivotes_bonos(self):
        """
        Retorna un diccionario con los pivotes y su distribucion

        """
        return self.pivotes_bonos

    def calculoPivote_bonos(self):
        """
        Funcion encargada de calcular la distribucion de los pivotes
        pivotes_derivados es un diccionario que guarda los vectores con las proyecciones.
        """
        fecha_val_str = self.fecha_val.strftime("%Y-%m-%d")
        self.pivotes_bonos = proyeccionBonos(self.bonos, np.array(self.pivotes)/360, fecha_val_str, self.getDfBonos(), self.corr)

    
    def volatilidades_cartera(self, dfRetornos):
        
        """
        Funcion encargada de calcular las volatilidades de ciertos retornos
        Estas volatilidades estan calculadas con la funcion ewma, lambda 0.94
        :param dfRetornos: DataFrame con los retornos a los que se les calcularan las volatilidades
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

            retornos = dfRetornos[nom_columnas[i]]
            valor = ewma(retornos, 0.94)
            valores.append(valor["Vol c/ajuste"].values[0])
        
        df["Volatilidades"] = valores
        return df
    def get_covarianza(self, cor, vol):
        """
        Calcula matriz de covarianzas.
        :param cor: DataFrame con la matriz de correlacion.
        :param vol: DataFrame con las volatilidades :3
        """
        cor = cor.values
        vol = vol["Volatilidades"].values
        D = np.diag(vol)
        return pd.DataFrame(np.dot(np.dot(D,cor),D))

    def get_correlaciones(self):

        return self.corr
        

miCartera = Cartera(datetime.date(2018, 4, 18), ["BSTDU10618","BSTDU21118"], ["146854", "146883"], ["BSANTANDER.SN.xlsx", "ENTEL.SN.xlsx"], cn)





# print(miCartera.get_covarianza(miCartera.get_correlaciones() ,miCartera.get_volatilidades()))
"""
cb = "SELECT TOP (1) * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + "UF" + "#" + "AA" + "#Corporativos#No Prepagables' AND Fecha = '2018-02-09'"
cb = pd.read_sql(cb, cn)
print(cb)
parseo = parsear_curva(cb["StrCurva"][0], cb["Fecha"][0].date())
x = []
y = []
for i in np.arange(len(parseo)):
    x.append(parseo[i][0])
    y.append(parseo[i][1])
plt.plot(x,y, '*')
plt.show()
print(parseo)
"""