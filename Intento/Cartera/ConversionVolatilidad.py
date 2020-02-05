import pyodbc
import pandas as pd
import numpy as np

import sys
sys.path.append("..")

from Bonos.LibreriasUtiles.UtilesDerivados import siguiente_habil_pais
from Bonos.UtilesBonos import castDay

# Conexion a base de datos
server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'

cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

# Conversion de USD/UF/EUR a CLP
def getConversionCLP(monedaBase, n = 200):
    """
    Entrega el historico del valor de conversion en CLP/monedaBase por n dias.
    :param monedaBase: String con la moneda que se desea llevar a CLP.
    :param n: String con la cantidad de dias que se quieren.
    :return: Un DataFrame con el historico de conversion.
    """
    if (monedaBase == 'UF'):
        conversion = "SELECT TOP(" + n + ") Valor FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = 'CLF' AND Campo = 'PX_LAST' AND Hora = '1700' ORDER BY Fecha DESC "
    else:
        conversion = "SELECT TOP(" + n + ") Valor FROM [dbAlgebra].[dbo].[TdMonedas] WHERE Ticker = '" + monedaBase + "' AND Campo = 'CLP' AND Hora = 'CIERRE' ORDER BY Fecha DESC"
    conversion = pd.read_sql(conversion, cn)
    conversion = conversion.values[::-1]
    conversion = pd.DataFrame(conversion, columns=['Cambio'])
    return conversion


def retornosMoneda(monedaBase, n):
    """
    Entrega el retorno del valor de conversion en CLP/monedaBase por n dias.
    :param monedaBase: String con la moneda que se desea llevar a CLP.
    :param n: Int con la cantidad de dias que se quieren.
    :return: Un DataFrame con el retorno de conversion.
    """

    historico = getConversionCLP(monedaBase, str(n))
    retorno = np.zeros(n)
    retorno[0] = 0

    if monedaBase == "CLP": return pd.DataFrame(np.zeros(n), columns=["Retorno"])

    for i in range(1,n):

        retorno[i] = np.log(historico['Cambio'][i]/historico['Cambio'][i-1])

    return pd.DataFrame(retorno, columns=['Retorno'])





