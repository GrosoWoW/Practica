import datetime
import sys
import time
sys.path.append("..")

import numpy as np
import pandas as pd

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

        # Monedas.
        self.monedas = ["CLP", "USD", "UF"]
        
        #Riesgos.
        self.riesgos = ["AAA", "AA", "A"]#,"AA+" "AA-", "A+", "A", "A-", "BBB+", "BBB"]
        
        # Pivotes.
        self.pivotes = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30]

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
    
    #def get_volCurvas()
    
    def get_retCurvas(self, n):
        """
        Calcula y retorna el retorno de curvas de bonos y derivados.
        :param n: Cantidad de curvas.
        :return: pd.DataFrame con los retornos de las curvas de bonos y derivados. Orden: derivados-bonos.
        """
        arr = []
        # Retornos derivados.
        for moneda in self.monedas:
            dfHistorico = calculo_historico(vector_dias, moneda, n)
            aux = calcular_retornos(dfHistorico)
            arr.append(aux)

        # Retornos Bonos
        for mon in self.monedas:
            for riesgo in self.riesgos:
                col = nombre_columna(mon, riesgo, self.pivotes)
                hist = historicoPlazos(riesgo, mon, np.array(self.pivotes)/360, np.arange(len(self.pivotes)), n)
                hist = pd.DataFrame(hist, columns=col)#uwu
                arr.append(calcular_retornos(hist))

        return pd.concat(arr, 1)


    def get_volCurvas(self, retornoCurvas):
        """
        param retornoCurvas: DataFrame. Retorno no todas
        Retorna volatilidades de los instrumentos que se valorizan con curvas.

        """
        # Agregar calculo de volatilidades de bonos.
        return volatilidades_derivados(retornoCurvas)

    def get_retornosTotales(self, retAcciones, retCurvas):
        """
        param retAcciones: DataFrame. Retornos de las acciones en la cartera.
        param retCurvas: DataFrame. Retornos de instrumentos de curvas. Orden: derivados-bonos.
        Retorna DataFrame con los retornos de todos los instrumentos en la cartera. Orden: acciones-der-bon.

        """

        return pd.concat([retAcciones, retCurvas])

    #def get_volTotales(self):


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

    def calculoPivote_derivados(self):
        
        """
        Funcion encargada de calcular la distribucion de los pivotes

        """

        self.pivotes_derivados = calculo_derivado(self.objDerivados, self.fecha_val)
    def get_pivotes_bonos(self):
        """
        Retorna un diccionario con los pivotes y su distribucion

        """
        fecha_val_str = self.fecha_val.strftime("%Y-%m-%d")
        print(fecha_val_str)
        return proyeccionBonos(self.bonos, np.array(self.pivotes)/360, fecha_val_str, self.getDfBonos())


miCartera = Cartera(datetime.date(2018, 4, 18), ["BSTDU10618", "BENTE-M"], ["146854"], ["BSANTANDER.SN.xlsx", "ENTEL.SN.xlsx"], cn)
miCartera.crearObjDerivados()
miCartera.creaDfBonos()
# print(miCartera.getObjDerivados())
tiempo = time()
#miCartera.calculoPivote_derivados()
tiempo1 = time()
print("Tiempo de calculo pivotes: "+str(tiempo1-tiempo))
"""print(miCartera.get_pivotes_derivados())
print(miCartera.get_retAcciones())
print(miCartera.get_retAcciones())"""
print("-----------------------------------------")
#print(miCartera.get_volCurvas(1000))
tiempo2 = time()
print("Tiempo de calculo volatilidad: "+str(tiempo2-tiempo1))
#print(miCartera.get_retCurvas(1000))
tiempo3 = time()
print("Tiempo de retornos de todo: "+str(tiempo3-tiempo2))
print(miCartera.get_pivotes_bonos())