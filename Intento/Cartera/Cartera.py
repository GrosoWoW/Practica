import sys
sys.path.append("..")
#%%
import numpy as np
import pyodbc
import time
from Derivados.DerivadosTipos.DerivadosSCC import *
from Derivados.DerivadosTipos.DerivadosFWD import *
from Derivados.DerivadosTipos.DerivadosSUC import *
#from Derivados.MiDerivados import *
from Derivados.ValorizacionDerivados import *
from Acciones.Acciones import *


import datetime
import pandas as pd
from Bonos.Correlaciones import ewma, ewma_new_new_pivotes, covarianza_pivotes
from Bonos.LibreriasUtiles.UtilesValorizacion import diferencia_dias_convencion

#%%
server = "192.168.30.200"
driver = '{SQL Server}'  # Driver you need to connect to the database
username = 'practicantes'
password = 'PBEOh0mEpt'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)


# MEJORA: QUE LAS FUNCIONES QUE CREAN ALGO, PREGUNTEN SI ESTA CREADO.


class Cartera:
    def __init__(self, bonos, derivados, acciones, cn):
        """
        Constructor Cartera. Crea DataFrames de derivados y bonos.
        :param bonos: Arreglo 1-dim. Guarda los nemotecnicos de bonos en str.
        :param derivados: Arreglo 1-dim.. Guarda los ID_keys de derivados en str.
        :param acciones: Arreglo 1-dim. Guarda los nombres de los archivos con las acciones.
        """
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
        self.ObjDerivados = {key: None for key in derivados}

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
        # df = self.dfDerivados
        for der in derivados:
            fila = ("SELECT TOP (1) * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] WHERE ID_Key = '" + der + "'")
            fila = pd.read_sql(fila, cn)
            self.dfDerivados = self.dfDerivados.append(fila, ignore_index=True)

    def crearObjDerivados(self, fecha_val, hora):
        """
        Llena el diccionario de los derivados como objetos.
        :param fecha_val: datetime.date. Fecha de valorización.
        :param hora: Str. Hora de valorización. (EJ: '1500', '1700')
        :return:
        """
        # Conexión a base de datos.
        cn = self.cn
        # Crear el DataFrame de los derivados.
        self.creaDfDerivados()
        # Get del DataFrame y su tamaño.
        df = self.getDfDerivados()
        N = np.size(df, 0)
        for i in np.arange(N):
            # Tomar fila de df como DataFrame y setea su indice de fila a 0.
            derivado = df.iloc[[i]].reset_index(drop=True)
            # Cambios de formato para crear DerivadosAbstracto.
            FechaVenc = reformat_fecha(derivado.loc[0, "FechaVenc"])
            FechaEfectiva = reformat_fecha(derivado.loc[0, "FechaEfectiva"])
            derivado.loc[0, "FechaVenc"] = FechaVenc
            derivado.loc[0, "FechaEfectiva"] = FechaEfectiva
            derivado.loc[0, "ID"] = int(derivado["ID"])
            # Creación de derivados.
            if derivado.loc[0, "Tipo"] == "SCC":
                self.ObjDerivados[self.derivados[i]] = DerivadosSCC(fecha_val, hora, derivado, cn)
            elif derivado.loc[0, "Tipo"] == "SUC":
                self.ObjDerivados[self.derivados[i]] = DerivadosSUC(fecha_val, hora, derivado, cn)
            elif derivado.loc[0, "Tipo"] == "FWD":
                self.ObjDerivados[self.derivados[i]] = DerivadosFWD(fecha_val, hora, derivado, cn)
        return
 
    def retAcciones(self):
        """
        Calcula y retorna el retorno.
        :return: pd.DataFrame con los retornos de las acciones en la cartera.
        """
        print(self.acciones)
        acciones = self.acciones
        return retorno_varias_acciones(acciones)

    def volAcciones(self, df_retornos):
        """
        Calcula y retorna las volatilidades.
        :param: df_retornos: pd.DataFrame con los retornos de las acciones en la cartera.
        :return: pd.DataFrame con las volatilidades de las acciones en la cartera.
        """
        return calculo_volatilidades_acciones(df_retornos)
    
    
      def retDerivados(self):
        """
        Calcula y retorna el retorno.
        :return: pd.DataFrame con los retornos de las acciones en la cartera.
        """
        print(self.acciones)
        acciones = self.acciones
        return retorno_varias_acciones(acciones)

    def volDerivados(self, df_retornos):
        """
        Calcula y retorna las volatilidades.
        :param: df_retornos: pd.DataFrame con los retornos de las acciones en la cartera.
        :return: pd.DataFrame con las volatilidades de las acciones en la cartera.
        """
        return calculo_volatilidades_acciones(df_retornos)

    def getDfBonos(self):
        return self.dfBonos

    def getDfDerivados(self):
        return self.dfDerivados

    def getObjDerivados(self):
        return self.ObjDerivados


miCartera = Cartera(["BENTE-M"], ["146854"], ["BSANTANDER.SN.xlsx"], cn)
miCartera.crearObjDerivados(datetime.date(2018, 4, 18), "1700")
derivados = miCartera.derivados
print("Hola")
print(miCartera)
#a = calculo_derivado(derivados, datetime.date(2018, 4, 18))
#print(a)
df_retornos = miCartera.retAcciones()
print(miCartera.volAcciones(df_retornos))




# df_proyeccion = proyectar_der(frame[['FechaPago', 'Flujo']], miDerivado.fechaActual, "ACT360", df_curva, cor, vol)


# %%
