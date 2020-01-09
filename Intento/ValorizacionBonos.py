import pyodbc
import pandas as pd
import UtilesValorizacion
import datetime
import Util
import numpy as np
from math import exp, log
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from time import time

def fecha_str(fecha):  # La funcion sirve como azucar sintactico
    """Entrega la fecha en formato string para consultas SQL
    :param fecha: Fecha para transformar a string
    :return: String con al fecha en formato YYYYMMDD
    """
    return fecha.strftime("'%Y%m%d'")

def siguiente_habil_pais(fecha, pais, cn):
    """Retorna el día hábil siguiente a la fecha en el país indicado

        :param fecha: datetime.date con la fecha que se desea el día hábil siguiente
        :param pais: String con el código de país ("BR","MX","US"...)
        :param cn: pyodbc.connect conexión a base de datos
        :return: datetime.date con el día hábil siguiente
        """
    # Si la fecha es inválida
    if fecha == datetime.date(1900, 1, 1):
        return datetime.date(1900, 1, 1)

    # Países en TdFeriados
    paises = ["BR", "MX", "US", "CO", "UK", "PE", "CR", "RD"]
    if pais in paises:
        # Hábil mínimo y máximo en TdFeriados
        sql = ("SELECT MAX(fecha) AS maxi, MIN(fecha) AS mini "
               "FROM dbAlgebra.dbo.TdFeriados "
               "WHERE Pais='" + pais + "' AND SiHabil=1")

    else:  # elseif pais = 'CL'
        # Hábil mínimo y máximo en TdIndicadores
        sql = ("SELECT MAX(fecha) AS maxi, MIN(fecha) AS mini "
               "FROM dbAlgebra.dbo.TdIndicadores "
               "WHERE Feriado = 0")

    # Se consulta y extrae hábil máximo y mínimo
    fechas = pd.io.sql.read_sql(sql, cn)
    fecha_max = fechas.iloc[0]['maxi'].to_pydatetime().date()
    fecha_min = fechas.iloc[0]['mini'].to_pydatetime().date()
    if fecha_min <= fecha <= fecha_max and pais != "--":
        sql += " AND Fecha > " + fecha_str(fecha)
        fecha = pd.io.sql.read_sql(sql, cn).iloc[0]['mini'].to_pydatetime().date()


    else:
        fecha = add_days(fecha, 1)
    # Si es domingo
    if fecha.weekday() == 6:
        fecha = add_days(fecha, 1)
    # Si es sábado
    elif fecha.weekday() == 5:
        fecha = add_days(fecha, 2)

    return fecha

def cast_convencion(conv):
    """Castea la convención conv a un string estandar para consultas SQL

    :param conv: String con la convención
    :return: String con la convención casteada
    """
    res = {
        "30/360A": "30/360",
        "30/360": "30/360",
        "30/360 US": "30/360",
        "30/360US": "30/360",
        "30U/360": "30/360",
        "Bond basis": "30/360",
        "360/360": "30/360",
        "ISMA-30/360": "30/360",
        "ISMA-30/360 NONEOM": "30/360",
        "30/360 NON-EOM": "30/360",

        "ACT/365": "ACT365",
        "ACT365": "ACT365",
        "NL365": "ACT365",
        "NL/365": "ACT365",

        "ACT/360": "ACT360",
        "ACT360": "ACT360",

        "ACT/ACT": "ACTACT",
        "ACTACT": "ACTACT",
        "ISDA ACT/ACT": "ACTACT",
        "ACT/ACT NON-EOM": "ACTACT",

        "LACT360": "LACT360",
        "LACT/360": "LACT360",

        "LACT30": "LACT30",
        "LACT/30": "LACT30",
        
        "BUS DAYS/252": "ACTACT"  # Provisorio
    }.get(conv.strip(), "")

    return res

def diferencia_dias_convencion(convencion, fechaini, fechafin):
    """Entrega la diferencia de días entre fechaini y fechafin según la convencion.
    Es importante para el caso 30/360, ya que usa 30/360 USA
    :param convencion: Sring indicando la convención
    :param fechaini: datetime.date con fecha inicial
    :param fechafin: datetime.date con fecha final
    :return: int cantidad de días entre fechaini y fechafin con la convención
    """
    y1 = fechaini.year
    y2 = fechafin.year
    m1 = fechaini.month
    m2 = fechafin.month
    d1 = fechaini.day
    d2 = fechafin.day

    conv = cast_convencion(convencion)

    if conv == "30/360":
        if add_days(fechaini, 1).day == 1 and m1 == 2:
            d1 = 30
            if add_days(fechafin, 1).day == 1 and m2 == 2:
                d2 = 30
        if d2 == 31 and 31 >= d1 >= 30:
            d2 = 30
        if d1 == 31:
            d1 = 30
        plazo = (360*(y2-y1) + 30*(m2-m1) + (d2-d1))

    elif conv in ["ACT360", "LACT360", "ACT365", "ACTACT", "LACT30"]:
        plazo = (fechafin - fechaini).days
    else:
        print("ERROR")
        pass  # todo
    return plazo

def plazo_anual_convencion(convencion, fechaini, fechafin):

    dif = diferencia_dias_convencion(convencion, fechaini, fechafin)
    res = {
        "30/360": dif/360,
        "ACT360": dif/360,
        "LACT360": dif/360,
        "LACT30": dif/30,
        "ACT365": dif/365,
        "ACTACT": dif/365
    }.get(cast_convencion(convencion), "")
    if res == "":
        # todo
        pass

    return res

def factor_descuento(tir, fechaini, fechafin, convencion, orden):
    plazo = plazo_anual_convencion(convencion, fechaini, fechafin)

    if convencion == "LACT360" or convencion == "LACT30":
        res = {
            0: 1/(1 + tir*plazo),
            1: -plazo / (1 + tir*plazo)**2,
            2: 2*plazo*plazo / ((1+tir*plazo)**3)
        }.get(orden, "")

        if res == "":
            pass  # ERROR
        return res
    else:
        res = {
            0: 1 / ((1 + tir) ** plazo),
            1: -plazo / (1 + tir) ** (plazo + 1),
            2: plazo * (plazo + 1) / ((1 + tir) ** (plazo + 2))
        }.get(orden, "")

        if str(res) == "":
            pass  # ERROR
        return res

def StrTabla2ArrTabla(strTabla, fechaEmision):
    tabla = "0#"+fechaEmision+"#0#0#100#0|"+strTabla
    arreglo = tabla.split("|")
    Flujos = pd.DataFrame(columns=['flujos'])
    row = Flujos
    row = pd.DataFrame({'flujos':arreglo})
    Flujos = Flujos.append(row)
    Flujos = Flujos["flujos"].str.split("#")
    for i in range(1, len(Flujos)):
        Flujos[i][3] = float(Flujos[i][3].replace(',','.'))
        Flujos[i][4] = float(Flujos[i][4].replace(',','.'))
        Flujos[i][2] = float(Flujos[i][2].replace(',','.'))
        Flujos[i][5] = float(Flujos[i][5].replace(',','.'))
        Flujos[i][1] = datetime.datetime.strptime(Flujos[i][1], '%d-%m-%Y').strftime('%Y-%m-%d')
        Flujos[i][1] = datetime.datetime.strptime(Flujos[i][1], '%Y-%m-%d')
    Flujos[0][3] = float(Flujos[0][3].replace(',','.'))
    Flujos[0][4] = float(Flujos[0][4].replace(',','.'))
    Flujos[0][2] = float(Flujos[0][2].replace(',','.'))
    Flujos[0][5] = float(Flujos[0][5].replace(',','.'))
    Flujos[0][1] = datetime.datetime.strptime(Flujos[0][1], '%Y-%m-%d')
    array = np.insert(Flujos.values[0], 2, fechaEmision)
    for i in range(1,len(Flujos.values)):
        array = np.vstack((array, np.insert(Flujos.values[i], 2, fechaEmision)))

    return array

def add_months(fecha, meses):   # La funcion sirve como azucar sintactico
    """Entrega la fecha con la cantidad de meses agregados
    :param fecha: datetime.date con la fecha que se le desea agregar la cantidad de meses
    :param meses: int cantidad de meses que se desea agregar, puede ser negativo
    :return: datetime.date con la fecha correspondiente
    """
    return fecha + relativedelta(months=meses)

def parsear_curva(curva, fecha):
    """
    Parsea la curva para la fecha indicada y entrega un arreglo con los valores sin header
    :param curva: String con los valores de la curva en el formato 'plazo#valor|plazo1#valor1|..'
    :param fecha: datetime.date con la fecha para la curva
    :return: array de dos columnas con los valores (SIN HEADER)
    """
    res = []
    filas = curva.split('|')
    header = filas[0].split("#")
    if header[0] == 'Plazo':
        for fila in filas[1:]:
            valores_fila = fila.split('#')
            valores_fila[0].replace(",", ".")
            valores_fila[1] = valores_fila[1].replace(",", ".")
            res.append(valores_fila)
    else:
        for fila in filas[1:]:
            valores_fila = fila.split('#')
            if int(valores_fila[0]) >= 30:
                valores_fila[0] = (add_months(fecha, int(int(valores_fila[0]) / 30)) - fecha).days
            valores_fila[1] = valores_fila[1].replace(",", ".")
            res.append(valores_fila)
    return res

def interpolacion_log_escalar(x, XY, n=0, m=0, siExt=True, first=True):
    """Indica la abscica en la ordenada x al realizar interpolación logaritmica con los puntos del arreglo XY

    :param x: float abscica al cual se le busca la ordenada con interpolación
    :param XY: array con puntos x,y en
    :param n: int posicion del punto inicial en el arreglo (se setea automáticamente)
    :param m: int posicion del punto final en el arreglo (se setea automáticamente)
    :param siExt: bool indica si se hace extrapolación en caso de que x esté por sobre el rango del arreglo
    :param first: bool indica si es la primera vez que se llama a la función, para settear n y m.
    :return: float ordenada obtenida al realizar interpolación logaritmica
    """
    if first:
        n = 0
        m = len(XY)-1
    
    y0 = float(XY[0][1])  # Ordenada del primer punto del arreglo
    x1 = float(XY[n][0])  # Abscisa del punto n del arreglo
    y1 = float(XY[n][1])  # Ordenada del punto n del arreglo
    x2 = float(XY[m][0])  # Abscisa del punto m del arreglo
    y2 = float(XY[m][1])  # Ordenada del punto m del arreglo
    x = float(x)  # Abscisa del punto al cual se le busca la ordenada

    if n == m:
        return y1

    if x == x1:
        return y1

    if x < x1:  # x menor o igual que el menor del intervalo
        "Retornando"
        if siExt:
            return y1**(x/x1)
        else:
            return y1

    if x2 == x:  # x igual al maximo del intervalo
        return y2

    if x2 < x:  # x mayor que el maximo del intervalo
        if siExt:
            return ((y2/y0)**(x/x2)) * y0
        else:
            return y2

    else:  # x dentro del intervalo
        if m - n == 1:  # Pivote encontrado
            return exp((log(y2)-log(y1))/(x2-x1)*(x-x1) + log(y1))  # Se realiza interpolación logaritmica

    j = round((n+m)/2.0)  # Se busca el pivote en la posición j

    if float(XY[j][0]) >= x:
        return interpolacion_log_escalar(x, XY, n, j, siExt, False)
    else:
        return interpolacion_log_escalar(x, XY, j, m, siExt, False)

# Calcula la suma total del tir
def TIR(s, ancla, y0, y1, y2):

    """
    Calculo de los valores del TIR con todos los periodos
    de pago (entregados por el parametro s)

    """

    coef = np.zeros(4)
    coef[0] = ancla
    coef[1] = y0
    coef[2] = y1
    coef[3] = y2
    vector = np.zeros(len(s))

    for i in range(1, len(s)):
        vector[i] = coef[1] + (coef[0] - coef[1]) * (1 - np.exp(-s[i] / coef[2])) * (coef[2] / s[i]) + coef[3] * (
            (1 - np.exp(-s[i] / coef[2])) * (coef[2] / s[i]) - np.exp(-s[i] / coef[2]))

    return vector

#Calcula un factor del tir dependiendo la curva y n
def TIR_n(n, ancla, y0, y1, y2):

    """
    Caluclo del TIR para un pago en especifico, el cual
    corresponde al valor de n

    """

    coef = np.zeros(4)
    coef[0] = ancla
    coef[1] = y0
    coef[2] = y1
    coef[3] = y2
    valor = 0
    valor = coef[1] + (coef[0] - coef[1]) * (1 - np.exp(-n / coef[2])) * (coef[2] / n) + coef[3] * (
        (1 - np.exp(-n / coef[2])) * (coef[2] / n) - np.exp(-n / coef[2]))

    return valor

server= "192.168.30.200"
driver = '{SQL Server}'  # Driver you need to connect to the database
username = 'practicantes'
password = 'PBEOh0mEpt'
cnn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

def seleccionar_curva_derivados(fecha):

    curvas = ("SELECT * FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_CLP' AND Fecha = " + "'" + fecha + "'")
    curvas = pd.read_sql(curvas, cnn)
    return curvas

def seleccionar_curva_NS():

    curvas = ("SELECT * FROM dbAlgebra.dbo.TdCurvaNS WHERE Tipo = 'IF#CLP' ORDER BY Fecha  DESC")
    curvas = pd.read_sql(curvas, cnn)
    return curvas

def seleccionar_bono(nemotecnico):

    bono = ("SELECT TOP (10) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = " + "'"+nemotecnico+"'")
    bono = pd.read_sql(bono, cnn)
    return bono

def seleccionar_bonos_moneda(moneda, nemotecnico):

    bonos = ("SELECT TOP (10) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda = " + "'" + moneda +"'" " AND Nemotecnico = " + "'"+nemotecnico+"'")
    bonos = pd.read_sql(bonos, cnn)
    return bonos
    
def curva_desarrollo(curvita):

    tasa = []
    fecha = []
    for i in range(len(curvita)):

        tasa.append(float(curvita[i][1]))
        fecha.append(int(curvita[i][0]))

    return [fecha, tasa]


def curva_bonita(curva):

    finalX = []
    finalY = []
    for i in range(182, 10000):

        finalX.append(i)
        finalY.append(interpolacion_log_escalar(i, curva))
    
    return [finalX, finalY]


# Calculo de valor del bono

def valor_bono_derivados(bono, curva_derivados):

    """
    Calculo de un valor del bono con el tipo de curva
    de derivados, con la utilizacion de la interpolacion
    logaritmica

    """

    tabla_desarrollo = StrTabla2ArrTabla(bono.values[0][1], str(bono.values[0][0]).split(" ")[0])
    dfTabla = pd.DataFrame(tabla_desarrollo, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
    fecha_inicial = datetime.datetime.now()
    largo = dfTabla[["Numero"]].shape[0]
    convencion = "ACT360"

    suma = 0
    historico = []

    for i in range(largo):

        diferencia = diferencia_dias_convencion(convencion, fecha_inicial, dfTabla["Fecha"][i])
        if (diferencia > 0):

            tir = interpolacion_log_escalar(diferencia, curva_derivados)
            valor = (dfTabla["Cupon"][i])*(factor_descuento(tir, fecha_inicial, dfTabla["Fecha"][i], convencion, 0))
            historico.append(valor)
            suma += valor

    return suma
            
#--------------------Historico de precio---------------------

def parsear_convenciones(df_tabla):
    convenciones = []
    for i in range(df_tabla.shape[0]):
        if df_tabla.loc[0].Base1 == -1:
            s = "ACT"
        else:
            s = str(df_tabla.loc[0].Base1) + '/'
        convenciones.append(s+str(df_tabla.loc[0].Base2))
    return convenciones

curva_ns_1 = seleccionar_curva_NS()


def valor_bono(bono, curva):

    """
    Calcula el valor del bono con todos sus cupones
    Recibe el bono a calcular el valor, y la curva 
    que se utilizara para el calculo
    
    """

    tabla = StrTabla2ArrTabla(bono["TablaDesarrollo"][0], str(bono["FechaEmision"][0]).split(" ")[0]) #Se crea la tabla de desarrollo del bono
    dfTabla_bono = pd.DataFrame(tabla, columns=['Numero', 'Fecha', 'Fecha str', 'Interes', 'Amortizacion', 'Remanente', 'Cupon'])
    cantidad_pagos = dfTabla_bono["Cupon"].shape[0]
    convencion = parsear_convenciones(bono)
    suma = 0

    for i in range(cantidad_pagos):

        #Diferencia entre la curva y el pago del bono
        diferencia_dias = diferencia_dias_convencion(convencion[0], curva.Fecha, dfTabla_bono["Fecha"][i]) 

        if (diferencia_dias > 0):

            tir = TIR_n(diferencia_dias, curva.ancla, curva.y0, curva.y1, curva.y2)
            factor = factor_descuento(tir, curva.Fecha, dfTabla_bono["Fecha"][i], convencion[0], 0)
            suma += factor * dfTabla_bono["Cupon"][i]

    return suma

def total_historico(bonos):

    """
    Calcula el valor de un bono con todas las curvas que se encuentran
    en la base de datos, entrega una matriz con el eje x e y correspondiente

    """

    curvas = seleccionar_curva_NS()
    largo = curvas.shape[0]
    valorBono = []
    indices = []
    
    for i in range(largo):

        fecha_curvas = curvas.loc[i].Fecha
        diferencia = bonos["FechaEmision"][0] - fecha_curvas
        
        if(diferencia.days < 0):
            curva = curvas.loc[i]
            calculo_bono = valor_bono(bonos, curva)
            valorBono.append(calculo_bono)
            indices.append(fecha_curvas)
    
    return [valorBono[::-1], indices[::-1]]


def auto_bono(Nemotecnico):

    bono = seleccionar_bono(Nemotecnico)
    bono = total_historico(bono)
    return bono

def plot_bonos(arregloBonos):

    largo = len(arregloBonos)
    for i in range(largo):

        bonos = auto_bono(arregloBonos[i])
        plt.plot(bonos[1], bonos[0])

    tiempo_final = time() - tiempo_inicial
    print("Retornos: {}".format(tiempo_final))

    plt.show()
#-------------------------Calculos-Historico-------------------------
tiempo_inicial = time()
arreglo_bonos = ["BSTDU10618", "BSTDU21118", "BSTDU30618", "BSTDU40117", "BSTDU70518" , "BENTE-L"]
#plot_bonos(arreglo_bonos)


def tiempos(bonos):

    """
    Calcula el tiempo que demora una matriz de bonos en calcular
    el retorno del bono, recibe bonos que corresponde a una matriz
    con todos los bonos que se desea medir el tiempo de ejecucion

    """
    print(len(bonos))
    tiempos = []
    tiempo_i = time()
    for i in range(len(bonos)):
        print(bonos[i])
        auto_bono(bonos[i])
        tiempo = time() - tiempo_i
        tiempos.append(tiempo)
    plt.plot(tiempos, "*")
    plt.show()

bonobon = ["BSTDU10618", "BSTDU21118", "BSTDU30618", "BSTDU40117", "BSTDU70518" , "BENTE-L", "BCORCB0914"\
    ,"BCORCC0914","BCORCD0914","BCORCE0914","BCORCF0914","BCORCG0914","BCORCH0914","BCORCI0914","BCORCJ0914","BCORCK0914", \
        "BCORCL0914","BCORCM0914","BCORCN0914","BCORCO0914","BCCA-C0912","BCCA-D1113","BCCA-E0115","BCCAR-A",\
        "BCCAR-B","BSECX10118","BPLZA-L","BBBVP20714","BFALA-Q","BCOPV-B","BEMCA-Q","BQUIN-T","BRPLC-E","BFORU-BA","BECOP-H",\
        "BESVA-R","BBCI-E1117","BESTW10417","BESTW20717","BESTW30218","BESTW40218","BESTW61117"]

#tiempos(bonobon)

bono_6 = auto_bono("BENTE-L")

#Bono que se utilizara para el calculo
bono_derivados =("SELECT TOP (10) [FechaEmision], [TablaDesarrollo] FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = 'BSTDU10618'")
bono_derivados = pd.read_sql(bono_derivados, cnn)

curva_derivados = seleccionar_curva_derivados(str(bono_derivados["FechaEmision"][0]))
curva_derivados = parsear_curva(curva_derivados["Curva"][0], datetime.datetime.today)

#Calculo del valor de un bono con curva derivados
valor_bono_derivados(bono_derivados, curva_derivados)


#-----------------Calculo de retorno-------------------------

def retorno_bonos(tablaHistorico, fecha):

    """
    Calcula el retorno de los bonos para una tabla de bonos,
    recibe la tabla de bonos y la matriz de fechas

    """ 

    retornos = []

    for i in range(len(tablaHistorico)):

        if i != 0:

            diferencia_valor = np.log(tablaHistorico[i] / tablaHistorico[i-1])
            retornos.append(diferencia_valor)
        else:

            retornos.append(0)

    tabla = pd.DataFrame({"Date": fecha, "Valor": tablaHistorico, "Retorno": retornos})
    return tabla

#----------------Funciones para trabajar en excel---------------------

def dataframe_datetime(tabla):

    """
    Cambia la columna fecha de la tabla de excel a un
    datetime, originalmente se encuentra en string

    """

    Fecha = tabla["Date"]
    nueva_fecha = []
    for i in range(len(Fecha)):

        fecha_drop = Fecha[i].split("-")
        fecha_string = datetime.datetime(int(fecha_drop[0]), int(fecha_drop[1]), int(fecha_drop[2]))
        nueva_fecha.append(fecha_string)
    
    tabla.drop(columns = ["Date"])
    tabla["Date"] = nueva_fecha
    return tabla

def tabla_excel_yahoo_retorno(nombreArchivo):

    """
    Extrae un archivo excel a un dataframe, calculando su valor de retorno
    con la funcion retorno_bonos
    
    """

    archivo = pd.read_csv('C:\\Users\\groso\\Desktop\\Practica\\Intento\\'+ nombreArchivo)
    Tabla = retorno_bonos(archivo["Adj Close"], archivo["Date"])
    Tabla = Tabla.drop(columns="Valor")
    nombre = nombreArchivo.split(".")[0]
    Tabla = Tabla.rename(columns={'Retorno':nombre })
    return Tabla

def tabla_bono_retorno(bono, nombre):

    """
    Calcula la tabla de retorno de un bono, renombrando
    la columna retorno con el nombre del bono para
    mejor entendimiento

    """

    Tabla = retorno_bonos(bono[0], bono[1])
    Tabla = Tabla.drop(columns="Valor")
    Tabla = Tabla.rename(columns={"Retorno":nombre})
    return Tabla

def unir_dataframes(datas):

    """
    Recibe una lista de tablas y las une con un join
    siendo la llave la fecha donde se calculo el retorno

    """

    tabla = []

    for i in range(len(datas)):

        tabla_actual = datas[i]
        if isinstance(tabla_actual["Date"][0], str):

            tabla_actual = dataframe_datetime(tabla_actual)

        if len(tabla) == 0:

            tabla = tabla_actual
        else:

            tabla = pd.merge(tabla, tabla_actual, on="Date")
    return tabla

def graficar_retornos(tablas, nombres):

    """
    Grafica los retornos para una cierta cantidad de tablas,
    recibe un vector de tablas que se quieren graficar
    y los nombre de cada valor

    """

    largo = len(tablas)
    for i in range(largo):

        plt.plot(tablas[i]["Date"][:], tablas[i][nombres[i]][:])
    plt.show()

#------------------Correlacion--------------------------

def formula(lam, r, N, j, k):
    valor = 0
    for i in range(0,N):
        valor += (lam**i)*r[j][N-i-1]*r[k][N-i-1]

    return valor

def ewma_new_new(m_empresas, l, matriz_r):

    cor = np.zeros([m_empresas, m_empresas])
    ro = np.zeros([m_empresas, m_empresas])
    for k in range(0,m_empresas):
        for j in range(0,m_empresas):

            tamanoRetorno = len(matriz_r[:][k])
            ro[k][j] = formula(0.94, matriz_r, tamanoRetorno, j, k)

    return ro

#------------------Calculos-Retorno---------------------

#Bonos
tiempo_inicial = time()
BonoEntel = tabla_bono_retorno(bono_6, "BonoEntel")

#Acciones
Entel = tabla_excel_yahoo_retorno("ENTEL.SN.csv")
Facebook = tabla_excel_yahoo_retorno("FB.csv")  
Santander = tabla_excel_yahoo_retorno("BSANTANDER.SN.csv")
Iansa = tabla_excel_yahoo_retorno("IANSA.SN.csv")
matriz_correlacion = (unir_dataframes([Entel, Facebook, Santander, Iansa, BonoEntel])).corr()
tiempo_final = time()-tiempo_inicial
print("Correlacion: {:.5f}".format(tiempo_final))
graficar_retornos([Entel, Facebook, Santander],["ENTEL", "FB", "BSANTANDER", "IANSA", "BonoEntel"])