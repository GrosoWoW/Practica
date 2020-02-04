# -*- coding: utf-8 -*-

import sys
sys.path.append("..")

import pandas as pd
import numpy as np
import pyodbc
from Utiles.BonoUtil import *
from Utiles.UtilesValorizacion import StrTabla2ArrTabla

class Bono:
    def __init__(self, nemotecnico, n, cn):
        
        self.nemo = nemotecnico

        self.cn = cn

        self.info = self.set_info()

        self.moneda = self.info['Moneda'].values[0]

        self.riesgo = conversionSYP(self.set_riesgo())

        self.cupones = StrTabla2ArrTabla(self.info['TablaDesarrollo'].values[0], self.info['FechaEmision'][0].to_pydatetime().date().strftime("%Y-%m-%d"))

        self.cupones_plazos = []

        self.n = n

        self.historico = self.set_historico_monedaRiesgo()

    def set_riesgo(self):
        riesgo = "SELECT * FROM [dbAlgebra].[dbo].[VwRiesgoRF] WHERE Nemotecnico = '" + self.nemo + "'"
        riesgo = pd.read_sql(riesgo, self.cn)
        return riesgo["Riesgo"].values[0]
        
    def set_info(self):
        b = "SELECT TOP(1) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = '" + self.nemo + "' ORDER BY Fecha DESC"
        bono = pd.read_sql(b, self.cn)
        return bono

    def set_historico_monedaRiesgo(self):
        '''
        Funcion que entrega la curva para un bono en base a su riesgo, moneda, a partir de la fecha deseada.
        :return: dataFrame con la informacion.
        '''
        n = self.n
        moneda = self.moneda
        riesgo = self.riesgo
        if( ((riesgo == 'AAA' or riesgo == 'A')  and moneda == 'CLP') or moneda == 'USD'):
            cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = 'IF#" + moneda + "' ORDER BY Fecha DESC "
        elif(riesgo == 'AA' and moneda == 'CLP'):
            cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Consolidado#Prepagables' ORDER BY Fecha DESC"
        else:
            cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Corporativos#No Prepagables' ORDER BY Fecha DESC "
        cb = pd.read_sql(cb, cn)
        curva = cb.values[::-1]
        print(curva)
        curva = pd.DataFrame(curva, columns=['Historico'])
        return cb

    def get_riesgo(self):

        return self.riesgo

    def get_info(self):

        return self.info

    def get_historico(self):

        return self.historico

    


server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'

cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

Bono('BACEN-A1', 100, cn)
























print("owo owo")