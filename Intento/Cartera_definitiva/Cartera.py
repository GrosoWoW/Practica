import pyodbc

from Activo import *
from Accion import *
from Bono import *
from Derivado import *
from DerivadosTipos.DerivadosSCC import *

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

        self.bonos = []

        for j in range(np.size(bonos,0)):

            bono = bonos.iloc[j]
            obj_bono = Bono(bono['Riesgo'], bono['Moneda'], bono['TablaDesarrollo'], bono['Convencion'], moneda, fecha, cn)
            self.bonos.append(obj_bono)

        self.derivados = []

        for k in range(np.size(derivados,0)):
            derivado = derivados.iloc[k]
            obj_derivado = Derivado(derivado['Derivado'], moneda, fecha, cn)
            self.derivados.append(obj_derivado)
        
    def get_acciones(self):

        return self.acciones

    def get_bonos(self):

        return self.bonos

    def get_derivados(self):

        return self.derivados

# Conexion
server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)
# Acciones
accion = pd.DataFrame()
accion['Moneda'] = ['USD', 'UF']
accion['Historico'] = ['1,2,3,4,5,6,7,8,9,10', '1,2,3,4,5,6,7,8,9,10']
# Bonos
bono = pd.DataFrame()
bono['Riesgo'] = ['AAA']  
bono['Moneda'] = ["CLP"]
bono['TablaDesarrollo'] = ["1#25-09-2018#2,2252#0#100#2,2252|2#25-03-2019#2,2252#0#100#2,2252|3#25-09-2019#2,2252#0#100#2,2252|4#25-03-2020#2,2252#0#100#2,2252|5#25-09-2020#2,2252#0#100#2,2252|6#25-03-2021#2,2252#100#0#102,2252"]
bono['Convencion'] = ["ACT360"]
# Derivado
info_derivado = dict()
info_derivado["Tipo"] = 'SCC'
info_derivado["ID_Key"] = ""
info_derivado["Administradora"] = "Admin"
info_derivado["Fondo"] = "Fondo"
info_derivado["Contraparte"] = "Contraparte"
info_derivado["ID"] = 3
info_derivado["Nemotecnico"] = ""
info_derivado["Mercado"] = "Local"
fecha = datetime.date(2019, 12, 20)
hora = '1700'
info_derivado["FechaEfectiva"] = '12/11/2019'
info_derivado["FechaVenc"] = '12/11/2021'
info_derivado["AjusteFeriados"] = "CL"
info_derivado["NocionalActivo"] = 10*(10**9)
info_derivado["MonedaActivo"] = 'CLP'
info_derivado["MonedaBase"] = 'CLP'
info_derivado["TipoTasaActivo"] = 'Fija'
info_derivado["TipoTasaPasivo"] = 'Flotante'
info_derivado["TasaActivo"] = 1.45
info_derivado["TasaPasivo"] = -1000
info_derivado["FrecuenciaActivo"] = "Semi annual"
info_derivado["FrecuenciaPasivo"] = info_derivado["FrecuenciaActivo"]

info1 = pd.DataFrame([info_derivado])
derivado_info = DerivadosSCC(fecha, hora, info1, cn)
derivado = pd.DataFrame()
derivado['Derivado'] = [derivado_info]




cartera = Cartera(accion, bono, derivado, 'CLP', datetime.date(2018,5,5), cn)
print(cartera.get_acciones())
print(cartera.get_bonos())
print(cartera.get_derivados())