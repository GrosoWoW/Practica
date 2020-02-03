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
def getConversionCLP(monedaBase, n):
    """
    Entrega el valor de conversion en CLP/monedaBase
    """
    if (monedaBase == 'UF'):
        conversion = "SELECT TOP(" + n + ")[Valor] FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = 'CLF' AND Campo = 'PX_LAST' AND Hora = '1700' ORDER BY Fecha DESC "
    else:
        conversion = "SELECT TOP(" + n + ") [Valor] FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = '" + monedaBase + "' AND Campo = 'CLP' AND Hora = 'CIERRE' ORDER BY Fecha DESC"
    conversion = pd.read_sql(conversion, cn)
    print("Sin dar vuelta: ", conversion)
    conversion = conversion.values.reverse()
    conversion = pd.DataFrame(conversion)
    print("AL dar vuelta: ", conversion)
    return conversion

getConversionCLP('USD', 10)



