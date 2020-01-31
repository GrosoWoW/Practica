import pyodbc
import pandas as pd

import sys
sys.path.append("..")

from Bonos.LibreriasUtiles.UtilesDerivados import siguiente_habil_pais
from Bonos.LibreriasUtiles.UtilesBonos import castDay

# Conexion a base de datos
server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'

cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

# Conversion de USD/UF/EUR a CLP
def getConversionCLP(monedaBase, fecha):
    """
    Entrega el valor de conversion en CLP/monedaBase
    """
    if (monedaBase == 'UF'):
        conversion = "SELECT [Valor] FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = 'CLF' AND Campo = 'PX_LAST' AND Fecha = '" + fecha + "' AND Hora = '1700'"
    else:
        conversion = "SELECT [Valor] FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = '" + monedaBase + "' AND Campo = 'CLP' AND Fecha = '" + fecha + "' AND Hora = 'CIERRE'"
    conversion = pd.read_sql(conversion, cn)
    return conversion

"""
USDaCLP = getConversionCLP('USD', '2020-01-30').values
UFaCLP  = getConversionCLP('UF', '2020-01-30').values
EURaCLP = getConversionCLP('EUR', '2020-01-30').values
print(USDaCLP)
print(UFaCLP)
print(EURaCLP)
"""

def getHistorico(moneda, n = 100, fecha):
    fecha = castDay(fecha)
    historico = np.zeros(n)
    for i in range(n):
        historico[i] = getConversionCLP(moneda, fechaIni)
        fechaIni = siguiente_habil_pais(fechaIni, 'CL', cn)


