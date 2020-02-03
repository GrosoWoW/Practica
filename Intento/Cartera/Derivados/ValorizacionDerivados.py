import datetime
import sys
import time
sys.path.append("..")


import numpy as np
import pandas as pd

import pyodbc
from Bonos.Correlaciones import covarianza_pivotes, ewma, ewma_new_new_pivotes
from Bonos.LibreriasUtiles.UtilesValorizacion import diferencia_dias_convencion
from Derivados.DerivadosTipos.DerivadosFWD import *
from Derivados.DerivadosTipos.DerivadosSCC import *
from Derivados.DerivadosTipos.DerivadosSUC import *



# Conexion al servidor de base de datos

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'
cnn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

def creacion_derivado(FechaEfectiva, FechaVenc, AjusteFeriados, NocionalActivo, MonedaActivo,                                                     MonedaBase, TipoTasaActivo, TipoTasaPasivo, TasaActivo,                                                                        TasaPasivo, FrecuenciaActivo, FrecuenciaPasivo,                                                                         ID, Tipo,NocionalPasivo, MonedaPasivo ,ID_Key=None): 

    """
    Funcion encargada de crear el derivado, recibe todos
    los parametros necesarios para su creacion, esta creacion
    depende del tipo de derivado

    """

    info_derivado = dict()
    info_derivado["Tipo"] = str(Tipo)
    info_derivado["ID_Key"] = ""
    info_derivado["Administradora"] = "Admin"
    info_derivado["Fondo"] = "Fondo"
    info_derivado["Contraparte"] = "Contraparte"
    info_derivado["ID"] = int(ID)
    info_derivado["Nemotecnico"] = ""
    info_derivado["Mercado"] = "Local" 

    fecha = datetime.date(2018, 4, 18)
    hora = '1700'

    info_derivado["FechaEfectiva"] = str(FechaEfectiva)
    info_derivado["FechaVenc"] = str(FechaVenc)

    info_derivado["AjusteFeriados"] = str(AjusteFeriados)

    info_derivado["NocionalActivo"] = float(NocionalActivo)
    info_derivado["NocionalPasivo"] = float(NocionalPasivo)

    info_derivado["MonedaActivo"] = str(MonedaActivo)
    info_derivado["MonedaBase"] = str(MonedaBase)
    info_derivado["MonedaPasivo"] = str(MonedaPasivo)

    info_derivado["TipoTasaActivo"] = str(TipoTasaActivo)
    info_derivado["TipoTasaPasivo"] = str(TipoTasaPasivo)

    info_derivado["TasaActivo"] = float(TasaActivo)
    info_derivado["TasaPasivo"] = float(TasaPasivo)

    info_derivado["FrecuenciaActivo"] = str(FrecuenciaActivo)
    info_derivado["FrecuenciaPasivo"] = str(FrecuenciaPasivo)

    info1 = pd.DataFrame([info_derivado])

    if str(Tipo.values[0]) == "SCC":
        derivado = DerivadosSCC(fecha, hora, info1, cnn)
    elif str(Tipo.values[0]) == "FWD":
        derivado = DerivadosFWD(fecha, hora, info1, cnn)
    elif str(Tipo.values[0]) == "SUC":
        derivado = DerivadosSUC(fecha, hora, info1, cnn)


    return derivado

def extraer_crear_derivado(ID_Key):

    """
    Funcion encargada de extraer los datos de un derivado de la base 
    de datos, solamente con su ID_Key y luego crearlo con la funcion
    creacion_derivado. Tambien se encarga de generar y valorizar los
    flujos
    :param ID_Key: Llave unica del derivado
    :return el derivado creado con su respectiva clase

    """

    derivado = ("SELECT * FROM [dbDerivados].[dbo].[TdCarteraDerivados_V2] WHERE ID_Key = '"+str(ID_Key) + "'")
    derivado = pd.read_sql(derivado, cnn)
    
    FechaEfectiva = derivado["FechaEfectiva"][0]
    FechaEfectiva = str(FechaEfectiva).split("-")
    dia = FechaEfectiva[2].split(" ")[0]
    FechaEfectiva = str(dia + "/" + str(FechaEfectiva[1]) +"/"+ str(FechaEfectiva[0]))

    FechaVenc = derivado["FechaVenc"][0]
    FechaVenc = str(FechaVenc).split("-")
    dia = FechaVenc[2].split(" ")[0]

    FechaVenc = str(dia + "/" + str(FechaVenc[1]) +"/"+ str(FechaVenc[0]))

    AjusteFeriados = derivado["AjusteFeriados"][0]
    NocionalActivo = derivado["NocionalActivo"][0]
    NocionalPasivo = derivado["NocionalPasivo"][0]
    MonedaActivo = derivado["MonedaActivo"][0]
    MonedaBase = derivado["MonedaBase"][0]
    MonedaPasivo = derivado["MonedaPasivo"][0]
    TipoTasaActivo = derivado["TipoTasaActivo"][0]
    TipoTasaPasivo = derivado["TipoTasaPasivo"][0]
    TasaActivo = derivado["TasaActivo"][0]
    TasaPasivo = derivado["TasaPasivo"][0]
    FrecuenciaActivo = derivado["FrecuenciaActivo"][0]
    FrecuenciaPasivo = derivado["FrecuenciaPasivo"][0]
    ID = derivado["ID"]
    Tipo = derivado["Tipo"]
    ID_Key = derivado["ID_Key"]

    dev = creacion_derivado(FechaEfectiva, FechaVenc, AjusteFeriados, NocionalActivo, MonedaActivo,                                                     MonedaBase, TipoTasaActivo, TipoTasaPasivo, TasaActivo,                                                                        TasaPasivo, FrecuenciaActivo, FrecuenciaPasivo,                                                                         ID, Tipo, NocionalPasivo, MonedaPasivo, ID_Key=ID_Key)
    dev.genera_flujos()
    dev.valoriza_flujos()

    return dev

def seleccionar_curva_derivados(moneda, n, fecha=datetime.date(2018, 1, 22)):

    """
    Funcion encargada de seleccionar todas las curva de TdCurvasDerivados
    dada su respectiva moneda (La hora sera 1700)
    :param moneda: El tipo de moneda utilizada para seleccionar la curva
    :param n: Cantidad de curvas a pedir.
    :return Pandas con todas las curvas obtenidas

    """

    monedas = moneda
    if moneda == "UF": #Funciona para el error de CLF
        monedas = "CLF"

    curva = ("SELECT TOP(" + str(n) + ")* FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+ str(monedas) +"' AND Hora = '1500' AND Fecha > '" + str(fecha) + "'")
    curva = pd.read_sql(curva, cnn)
    return curva

def seleccionar_curva_fecha(moneda, fecha):

    """
    Funcion que selecciona una curva de la base de datos TdCurvasDerivados
    dado su moneda y fecha (Esta curva sera unica pues se toma la hora 1700)
    :param moneda: El tipo de moneda utilizada para seleccionar la curva
    :param fecha: Fecha a la que se extraera la curva
    :return Pandas con la curva seleccionada

    """

    monedas = moneda
    if moneda == "UF": #Sirve para el error de CLF
        monedas = "CLF"

    curva = ("SELECT * FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+ monedas +"'                                                                                     AND Hora = '1700' AND Fecha = '"+fecha+"' ORDER BY Fecha ASC")
    curva = pd.read_sql(curva, cnn)
    return curva


 
vector_dias = [30, 90, 180, 360, 360*2, 360*3, 360*4, 360*5, 360*7, 360*9, 360*10, 360*15, 360*20, 360*30] #Vector para crear los pivotes


def calculo_historico(pivotes, moneda, n):

    """
    Funcion encargada de calcular el historico de factores
    de descuento con todas las curvas de TdCurvasDerivados
    :param pivotes: Vector con todos los dias que se necesitan los historicos
    :param moneda: Moneda necesaria para extraer las curvas de la base de datos
    :param n: Cantidad de curvas.
    :return DataFrame con el calculo de los historicos

    """
    
    largo = len(pivotes)
    moneda_curva = moneda.split("#")[0]
    curvas = seleccionar_curva_derivados(moneda_curva, n)[::-1]
    valores = []

    df = pd.DataFrame()
    #df["Fechas"] = curvas["Fecha"]

    for i in range(largo):

        for j in range(len(curvas["Curva"])):

            valor_dia = pivotes[i]
            curva = curvas["Curva"][j]
            fecha_curva = curvas["Fecha"][j]
            curva_parseada = parsear_curva(curva, fecha_curva)
            valor = interpolacion_log_escalar(valor_dia, curva_parseada)
            valores.append(valor)
        
        df[str(vector_dias[i]) + "#" + moneda] = valores
        valores = []

    return df

def calcular_retornos(dfHistorico):

    """
    Funcion encargada de calcular los retornos dado un historico para cada pivote
    :param dfHistorico: Pandas con los historicos a los que se les calculara el retorno
    :return DataFrame con todos los retornos ordenados

    """
    numero_filas = len(vector_dias)
    nom_columnas = dfHistorico.columns

    numero_columnas = len(dfHistorico[nom_columnas[0]])
    valores = []
    df = pd.DataFrame()

    for i in range(numero_filas):

        columna = dfHistorico[nom_columnas[i]]

        for j in range(numero_columnas):

            if j == 0:

                valores.append(0)

            else:

                valor = np.log(columna[j] / columna[j-1])
                valores.append(valor)

        df[nom_columnas[i]] = valores
        valores = []

    return df

def volatilidades_derivados(dfRetornos):

    """
    Funcion encargada de calcular las volatilidades de ciertos retornos
    Estas volatilidades estan calculadas con la funcion ewma, lambda 0.94
    :param dfRetornos: DataFrame con los retornos a los que se les calcularan las volatilidades
    :return DataFrame con las volatilidades de cada pivote

    """
    nom_columnas = dfRetornos.columns
    numero_filas = len(vector_dias)
    numero_columnas = len(dfRetornos[nom_columnas[0]])
    df = pd.DataFrame()
    valores = []

    for i in range(numero_filas):

        retornos = dfRetornos[nom_columnas[i]]
        valor = ewma(retornos, 0.94)
        valores.append(valor["Vol c/ajuste"].values[0])
    
    df["Volatilidades"] = valores
    return df

def correlaciones_derivador(dfRetornos, dfVolatilidades):

    """
    Funcion encargada de calcular las correlaciones dado las retornos
    y volatilidades de los pivotes
    :param dfRetornos: DataFrame con los retornos 
    :param dfVolatilidades: Dataframe con las volatilidades de los pivotes
    :return Matriz de correlacion de pivotes (en DataFrame)

    """

    lenght = len(vector_dias)
    volatilidad = dfVolatilidades["Volatilidades"]
    corr = ewma_new_new_pivotes(lenght, dfRetornos, volatilidad)
    return corr

def calcular_correlacion_moneda(moneda, tabla_total):

    """
    Funcion que calcula las correlaciones pero para
    distintos tipos de monedas
    :param moneda: Tipo de moneda para calcular la correlacion
    :param tabla_total: Informacion de factores y volatilidades de los pivotes
    :return Matriz de correlacion (en DataFram)

    """

    historico = calculo_historico(vector_dias, moneda, 1000)
    retornos = calcular_retornos(historico)
    correlacion = correlaciones_derivador(retornos, tabla_total)
    return correlacion


def calcular_diccionario_correlaciones(diccionario_pivotes):

    """
    Funcion encargada de calcular las distintas correlaciones
    para las distintas monedas utilizadas
    :param diccionario_pivotes: Diccionario con todos los pivotes
    :return Diccionario con llaves para cada correlacion

    """

    lenght = len(diccionario_pivotes)
    diccionario = dict()
    for key in diccionario_pivotes:
        correlacion = calcular_correlacion_moneda(key, diccionario_pivotes[key])
        diccionario[key] = correlacion

    return diccionario

def covarianzas_derivador(dfRetornos, dfVolatilidades):

    """
    Funcion encargada de crear la matriz de covarianza para 
    los pivotes, dada su informacion y los retornos
    :param dfRetornos: DataFrame con los retornos
    :param dfVolatilidades: Informacion de los pivotes
    :return Matriz de correlacion en DataFrame

    """

    lenght = len(vector_dias)
    volatilidad = dfVolatilidades["Volatilidades"]
    corr = covarianza_pivotes(lenght, dfRetornos, volatilidad)
    return corr 

def crear_pivotes(fecha_inicial, pivotes):

    """
    Funcion encarga de crear los dias de los pivotes
    :param fecha_inicial: Fecha del dia 0 de donde se crearan los pivotes
    :param pivotes: Vector con la diferencia de dias de los pivotes
    :return vector con los dias de los pivotes
    
    """

    lenght = len(pivotes)
    dias = []
    for i in range(lenght):

        dia = add_days(fecha_inicial, pivotes[i])
        dias.append(dia)

    return dias

def buscar_pivotes(fecha_pivotes, fecha):

    """
    Funcion encargada de buscar los dos pivotes que rodean 
    la fecha de pago del derivado
    :param fecha_pivotes: vector con las fechas de los pivotes
    :param fecha: Fecha que se desea buscar el pago
    :return vector de dos dimensiones con los indices de las fechas

    """

    lenght = len(fecha_pivotes)

    for i in range(lenght):

        fecha_probable = fecha_pivotes[i]
        if (i == 0 and fecha < fecha_probable) or (i == lenght - 1):

            return [i, i]

        elif fecha < fecha_probable:

            return [i-1, i]
        

def factor_desct_pivotes(pivotes, fecha_pivotes, moneda):

    """
    Funcion encargada de calcular los factores de descuento
    de los pivotes
    :param pivotes: vector con la diferencia de dias de los pivotes
    :param fecha_pivotes: Vector con las fechas de los pivotes
    :param monenda: Tipo de moneda que se utilizara para calcular los factore de descuento
    :return DataFrame con la fecha, pivote y factor de descuento de cada pivote

    """

    dia_inical = add_days(fecha_pivotes[0], -pivotes[0])

    monedas = moneda
    if moneda == "UF":  #Sirve para solucionar el error de CLF
        monedas = "CLF"

    curva = ("SELECT * FROM [dbDerivados].[dbo].[TdCurvasDerivados] WHERE Tipo = 'CurvaEfectiva_"+monedas+"' AND Fecha = '"+str(dia_inical)+"'")
    curva = pd.read_sql(curva, cnn)
    curva = parsear_curva(curva["Curva"][0], dia_inical)

    lenght = len(pivotes)
    valor_factor = []
    df = pd.DataFrame()

    for i in range(lenght):
        
        valor = interpolacion_log_escalar(pivotes[i], curva)
        valor_factor.append(valor)

    df["Fecha"] = fecha_pivotes
    df["Pivote"] = pivotes
    df["FactorDescuento"] = valor_factor

    return df

def crear_distrubucion_pivotes(monedas):

    """
    Funcion encargada de crear un diccionario con todos los 
    pivotes para cada moneda
    :param monedas: vector con todas las monedas que se calcularan
    :return Diccionario con los pivotes de cada moneda

    """

    diccionario = dict()
    for i in range(len(monedas)):

        arreglo = np.zeros(len(vector_dias))
        diccionario[monedas[i]] = arreglo

    return diccionario


 
def valor_alfa(fecha_valorizacion, fecha_pivote1, fecha_pivote2, fecha_pago):

    """
    Funcion encargada de calcular el valor de alfa que se necesita en el calculo
    :param fecha_valorizacion: Fecha que se desea valorizar
    :param fecha_pivote1: Fecha del pivote 1
    :param fecha_pivote2: Fecha del pivote 2
    :param fecha_pago: Fecha que se desea calcular
    :return un float con el valor de alfa_0

    """
    D_flujo = diferencia_dias_convencion("ACT360", fecha_valorizacion, fecha_pago)/360
    D_pivote1 = diferencia_dias_convencion("ACT360", fecha_valorizacion, fecha_pivote1)/360
    D_pivote2 = diferencia_dias_convencion("ACT360", fecha_valorizacion, fecha_pivote2)/360
    calculo = (D_flujo - D_pivote1)/(D_pivote2 - D_pivote1)
    return calculo


def interpolar_factorDesct(alfa_0, dfPivotes, fecha_pago):

    """
    Funcion encarga de interpolar el factor de decuentos para
    la fecha de pago
    :param alfa_0: Valor de alfa necesario para el calculo
    :param dfPivotes: DataFrame con la informacion util de los pivotes
    :param fecha_pago: Fecha donde se esta calculando el pago
    :return Valor del factor de descuento correspondiente a la fecha de pago

    """

    factores_descuento = dfPivotes["FactorDescuento"]
    numero_pivotes = buscar_pivotes(dfPivotes["Fecha"], fecha_pago)
    factor_pivote1 = factores_descuento[numero_pivotes[0]]
    factor_pivote2 = factores_descuento[numero_pivotes[1]]
    
    return alfa_0*factor_pivote1 + (1 - alfa_0)*factor_pivote2

def interpolar_volatilidad(alfa_0, dfPivotes, fecha_pago):

    """
    Funcion encargada de interpolar la volatilidad correspondiente
    a la fecha de pago
    :param alfa_0: Valor de alfa necesario para el calculo
    :param dfPivotes: DataFrame con informacion util de los pivotes
    :param fecha_pago: Fecha correspondiente al pago donde se esta calculando
    :return Valor de volatilidad correspondiente a la fecha de pago

    """

    volatilidades = dfPivotes["Volatilidades"]
    numero_pivotes = buscar_pivotes(dfPivotes["Fecha"], fecha_pago)
    volatilidad_pivote1 = volatilidades[numero_pivotes[0]]
    volatilidad_pivote2 = volatilidades[numero_pivotes[1]]

    return alfa_0*volatilidad_pivote1 + (1 - alfa_0)*volatilidad_pivote2


 
def generar_tabla_completa(pivotes, fecha_valorizacion, moneda):

    """
    Funcion encargada de generar la tabla completa de los pivotes
    con toda su informacion util (volatilidades, fecha, factores, etc)
    :param pivotes: Vector con la diferencia de dia de los pivotes
    :param fecha_valorizacion: Fecha que se desea valorizar
    :param moneda: Tipo de moneda que se desea generar los pivotes
    :return DataFrame con toda la informacion de los pivotes

    """ 

    fecha_pivotes = crear_pivotes(fecha_valorizacion, pivotes)
    factores_desct = factor_desct_pivotes(pivotes, fecha_pivotes, moneda)
    historico = calculo_historico(pivotes, moneda, 1000)
    retorno = calcular_retornos(historico)
    volatilidades = volatilidades_derivados(retorno)
    factores_desct["Volatilidades"] = volatilidades["Volatilidades"]
    return factores_desct


def generar_diccionario_table(pivotes, fecha_valorizacion, monedas):

    """
    Funcion encargada de crear el diccionario con las tablas completas
    de cada uno de los pivotes segun el tipo de moneda
    :param pivotes: Vector con la diferencia de dias de los pivotes
    :param fecha_valorizacion: Fecha donde se desea valorizar
    :param monedas: Vector con todas las monedas que se desean calcular pivotes

    """

    lenght = len(monedas)
    diccionario = dict()
    for i in range(lenght):

        tabla = generar_tabla_completa(pivotes, fecha_valorizacion, monedas[i])
        diccionario[monedas[i]] = tabla

    return diccionario


 
def solucion_ecuacion(sigma_flujo, sigma_pivote1, sigma_pivote2, ro):

    """
    Funcion para calcular la solucion de la ecuacion propuesta
    para obtener el valor de alfa necesario para los calculos futuros
    :param sigma_flujo: Corresponde a la volatilidad del flujo
    :param sigma_pivote1: Corresponde a la volatilidad del pivote1
    :param sigma_pivote2: Correponde a la volatilidad del pivote2
    :param ro: Correspode a la correlacion del pivote1 y pivote2

    """

    A = (sigma_pivote1**2 + sigma_pivote2**2 - 2*ro*sigma_pivote1*sigma_pivote2)
    B = (2 * ro * sigma_pivote1* sigma_pivote2 - 2*sigma_pivote2**2)
    C = (sigma_pivote2**2 - sigma_flujo**2)

    x1 = (-B+math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte positiva
    x2 = (-B-math.sqrt(B**2-(4*A*C)))/(2*A)  # Fórmula de Bhaskara parte negativa

    return[x1, x2]


 
def discrimador_sol(soluciones):

    """
    Funcion que sirve para seleccionar valor de las soluciones
    de las ecuaciones que se encuentren entre 0 y 1
    :param soluciones: Vector de dos dimensiones con las dos soluciones
    :return La solucion que cumple con los requisitos

    """

    for i in range(2):
        if 0 <= soluciones[i] and soluciones[i] <= 1:

            return soluciones[i]
    print("Javier, nos fallaste")
    return exit(1) 

def calculo2(fechas_pago, fecha_valorizacion, correlacion_total, tabla_derivado, distribuciones, derivado, tabla_total):

    """
    Funcion que extiende calculo 1, se encarga de calcular todas
    las distribuciones para los pagos de un derivado

    """

    lenght = len(fechas_pago)
    for i in range(lenght):

        moneda_derivado = derivado.flujos_valorizados["Moneda"][i]
        distribucion = distribuciones[moneda_derivado]

        pivote_usado = tabla_total[moneda_derivado]
        fechas_pivotes = pivote_usado["Fecha"]

        fecha_pago_actual = fechas_pago[i]

        indices_pivotes = buscar_pivotes(fechas_pivotes, fecha_pago_actual)
        dia_pivote1 = vector_dias[indices_pivotes[0]]
        dia_pivote2 = vector_dias[indices_pivotes[1]]


        volatilidades_pivotes = pivote_usado["Volatilidades"]

        curva = seleccionar_curva_fecha(moneda_derivado, str(fecha_valorizacion))
        curva_parseada = parsear_curva(curva["Curva"][0], fecha_valorizacion)

        alfa = valor_alfa(fecha_valorizacion, fechas_pivotes[indices_pivotes[0]], fechas_pivotes[indices_pivotes[1]], fecha_pago_actual)

        volatilidad = interpolar_volatilidad(alfa, pivote_usado, fecha_pago_actual)
        factor_desct = interpolar_factorDesct(alfa, pivote_usado, fecha_pago_actual)

        a =solucion_ecuacion(volatilidad, volatilidades_pivotes[indices_pivotes[0]], volatilidades_pivotes[indices_pivotes[1]], correlacion_total[str(dia_pivote1)+ "#" +str(moneda_derivado)][str(dia_pivote2)+ "#" +str(moneda_derivado)] )

        factor = discrimador_sol(a)
        flujo1 = tabla_derivado["Flujo"][i]
        diferencia_dias = diferencia_dias_convencion("ACT360", fecha_valorizacion, fecha_pago_actual)
        factor_descuento = interpolacion_log_escalar(diferencia_dias, curva_parseada)
        VP = factor_descuento*flujo1
    
        distribucion[indices_pivotes[0]] += factor*VP
        distribucion[indices_pivotes[1]] += (1 - factor)*VP

    
   

def calculo1(derivados, tabla_total, correlacion_total, fecha_valorizacion, distribuciones):

    """
    Funcion que extiende a calculo, se encarga de iterar por todos
    los derivados y luego por cada derivado se llama a calculo 2

    """

    resultado = []
    largo_derivados = len(derivados)

    for key in derivados.keys():

        derivado = derivados[key]
        tabla_derivado = derivado.flujos_valorizados[["ID","ActivoPasivo", "Fecha", "FechaFixing","FechaFlujo", "FechaPago", "Flujo", "ValorPresenteMonFlujo", "Moneda", "MonedaBase"]]

        fechas_pago = tabla_derivado["FechaFixing"]
        calculo2(fechas_pago, fecha_valorizacion, correlacion_total, tabla_derivado, distribuciones, derivado, tabla_total)




def calculo_derivado(derivados, fecha_valorizacion, correlacion_total, monedas):

    """
    Funcion principal de calculo

    """

    monedas_utilizadas = monedas
    tabla_total = generar_diccionario_table(vector_dias, fecha_valorizacion, monedas_utilizadas)
    #correlacion_total = calcular_diccionario_correlaciones(tabla_total)
    distribuciones = crear_distrubucion_pivotes(monedas_utilizadas)
    calculo1(derivados, tabla_total, correlacion_total, fecha_valorizacion, distribuciones)
    return distribuciones


