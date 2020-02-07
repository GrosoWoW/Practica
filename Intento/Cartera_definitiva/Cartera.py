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
        # Bono: DataFrame con ['Moneda', 'Riesgo', 'TablaDesarrollo', 'Convencion', 'Nemotecnico', 'FechaEmision]
        # Derivados: Objeto Derivado

        # Aqui se guarda una referencia a cada obj Accion
        self.acciones = []

        # Por cada Accion en el dataFrame
        for i in range(np.size(acciones,0)):

            accion = acciones.iloc[i]
            obj_accion = Accion(accion['Moneda'], pd.DataFrame(accion['Historico'][0]), moneda, fecha, cn)
            self.acciones.append(obj_accion)

        self.bonos = []

        for j in range(np.size(bonos,0)):

            bono = bonos.iloc[j]
            obj_bono = Bono(bono['Riesgo'], bono['Moneda'], bono['TablaDesarrollo'], bono['Convencion'], bono['FechaEmision'], moneda, fecha, cn)
            self.bonos.append(obj_bono)

        self.derivados = []

        for k in range(np.size(derivados,0)):
            derivado = derivados.iloc[k]
            obj_derivado = Derivado(derivado['Derivado'], moneda, fecha, cn)
            self.derivados.append(obj_derivado)

        self.moneda = moneda

        self.cn = cn

        self.fecha = fecha

        self.historicos_totales = pd.DataFrame()

        self.retornos_totales = pd.DataFrame()

        self.volatilidades_totales = pd.DataFrame()

        self.anio = 360 

        self.plazos = [30/self.anio, 90/self.anio, 180/self.anio, 360/self.anio, 2, 3, 4, 5, 7,\
            9, 10, 15, 20, 30]

        self.correlacion = pd.DataFrame()


    def get_moneda(self):

        return self.moneda

    def get_cn(self):

        return self.cn

    def get_fecha(self):

        return self.fecha
        
    def get_acciones(self):

        return self.acciones

    def get_bonos(self):

        return self.bonos

    def get_derivados(self):

        return self.derivados

    def get_historicos_totales(self):

        return self.historicos_totales

    def get_retornos_totales(self):

        return self.retornos_totales

    def get_volatilidades_totales(self):

        return self.volatilidades_totales

    def get_plazos(self):

        return self.plazos

    def get_correlacion(self):

        return self.correlacion
    
    def set_hist_ret_vol_totales(self):

        bonos = self.get_bonos()
        largo_bonos = len(bonos)
        
        derivados = self.get_derivados()
        largo_derivados = len(derivados)

        acciones = self.get_acciones()
        largo_acciones = len(acciones)

        dfHistorico = pd.DataFrame()
        dfRetornos = pd.DataFrame()
        dfVolatilidades = pd.DataFrame()

        for i in range(largo_bonos):

            bono = bonos[i]
            historico_bono = bono.get_historicos()
            retorno_bono = bono.get_retornos()
            volatilidad_bono = bono.get_volatilidad()
        
            dfHistorico = pd.concat([dfHistorico, historico_bono], 1)
            dfRetornos = pd.concat([dfRetornos, retorno_bono], 1)
            dfVolatilidades = pd.concat([dfVolatilidades, volatilidad_bono], 0)

        for i in range(largo_derivados):

            derivado = derivados[i]
            historico_derivado = derivado.get_historicos()
            retorno_derivado = derivado.get_retornos()
            volatilidad_derivado = derivado.get_volatilidad()
        
            dfHistorico = pd.concat([dfHistorico, historico_derivado], 1)
            dfRetornos = pd.concat([dfRetornos, retorno_derivado], 1)
            dfVolatilidades = pd.concat([dfVolatilidades, volatilidad_derivado], 0)
    
        for i in range(largo_acciones):

            accion = acciones[i]
            historico_accion = accion.get_historicos()
            retorno_accion = accion.get_retornos()
            volatilidad_accion = accion.get_volatilidad()
        
            dfHistorico = pd.concat([dfHistorico, historico_accion], 1)
            dfRetornos = pd.concat([dfRetornos, retorno_accion], 1)
            dfVolatilidades = pd.concat([dfVolatilidades, volatilidad_accion], 0)

        self.historicos_totales = dfHistorico
        self.retornos_totales = dfRetornos
        self.volatilidades_totales = dfVolatilidades

    def set_correlacion(self):

        largo_pivotes = len(self.get_plazos())
        lenght = largo_pivotes*(len(self.get_bonos()) + len(self.get_derivados())) + len(self.get_acciones())
        volatilidad = self.get_volatilidades_totales()
        retornos = self.get_retornos_totales()
        corr = ewma_matriz(lenght, retornos, volatilidad)
        self.correlacion = corr


# Conexion
server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

# Acciones
archivo = pd.read_excel('C:\\Users\\groso\\Desktop\\Practica\\Intento\\Cartera_definitiva\\AMZN.xlsx')    
#archivo = pd.read_excel('C:\\Users\\Lenovo\\Documents\\Universidad\\Practica\\Cartera_V2\\Practica\\Intento\\Cartera_definitiva\\AMZN.xlsx')
columnas = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
archivo = archivo[columnas][:200]
accion = pd.DataFrame()
accion['Moneda'] = ['USD']
accion['Historico'] = [[archivo["Adj Close"]]]
print(accion)
# Bonos
bono = pd.DataFrame()
bono['Riesgo'] = ['AAA']  
bono['Moneda'] = ["CLP"]
bono['TablaDesarrollo'] = ["1#25-09-2018#2,2252#0#100#2,2252|2#25-03-2019#2,2252#0#100#2,2252|3#25-09-2019#2,2252#0#100#2,2252|4#25-03-2020#2,2252#0#100#2,2252|5#25-09-2020#2,2252#0#100#2,2252|6#25-03-2021#2,2252#100#0#102,2252"]
bono['Convencion'] = ["ACT360"]
bono['FechaEmision'] = ['2018-02-20']
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




cartera = Cartera(accion, bono, derivado, 'CLP', datetime.date(2019,2,1), cn)
#print(cartera.get_acciones())
#print(cartera.get_bonos())
#print(cartera.get_derivados())
cartera.set_hist_ret_vol_totales()
print(cartera.get_historicos_totales())
print(cartera.get_retornos_totales())
print(cartera.get_volatilidades_totales())

cartera.set_correlacion()

print(cartera.get_correlacion())


'''bonos = cartera.get_bonos()
#print(bonos)
bono = bonos[0]
#print(bono)
bono.set_historico()
#print(bono.get_historicos())
bono.set_retorno()
#print('Hola')
bono.corregir_moneda()
#print(bono.get_retornos())
bono.set_volatilidad()
#print(bono.get_volatilidad())
bono.set_correlacion()
#print(bono.get_correlacion())
bono.distribucion_pivotes()'''