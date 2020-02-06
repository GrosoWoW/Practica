import pyodbc

from Activo import *
from Accion import *
from Bono import *
from Derivado import *

# (..., monedaCartera, fecha_valorizacion, cn)


class Cartera:
    def __init__(self, acciones, bonos, derivados, moneda, fecha, cn):
        # Acciones: DataFrame con historico de precios (debe contener 200 datos) ['Moneda', 'Historico']
        # Bono: DataFrame con ['Moneda', 'Riesgo', 'TablaDesarrollo', 'Convencion', 'Nemotecnico']
        # Derivados: Objeto Derivado

        # Aqui se guarda una referencia a cada obj Accion
        self.acciones = []

        # Por cada Accion en el dataFrame
        for i in range(np.size(acciones,0)):

            accion = acciones.iloc[i]
            obj_accion = Accion(accion['Moneda'], accion['Historico'].split(','), moneda, fecha, cn)
            self.acciones.append(obj_accion)
        
    def get_acciones(self):

        return self.acciones

accion = pd.DataFrame()
accion['Moneda'] = ['USD']
accion['Historico'] = ['1,2,3,4,5,6,7,8,9,10']

acciones = pd.DataFrame()
acciones['Acciones'] = [accion, accion, accion]

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'

cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

print(acciones)
cartera = Cartera(acciones, None, None, 'CLP', '2020-02-06', cn)
print(cartera.get_acciones())