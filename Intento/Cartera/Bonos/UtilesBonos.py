import sys
sys.path.append("..")
import pyodbc
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from math import exp, log
import datetime
from time import time
from Bonos.LibreriasUtiles.UtilesValorizacion import plazo_anual_convencion, add_days, factor_descuento, StrTabla2ArrTabla, parsear_curva
from Bonos.LibreriasUtiles.UtilesDerivados import siguiente_habil_pais
from Bonos.LibreriasUtiles.Matematica import interpolacion_escalar

server = '172.16.1.38'
username = 'sa'
password = 'qwerty123'
driver = '{ODBC Driver 17 for SQL Server}'

cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';UID=' + username + ';PWD=' + password)

def bonosNemo(nemo):
    '''
    Funcion que entrega la informacion de un bono en base a su nemotecnico.
    :param nemo: String del Nemotecnico del bono.
    :return: dataFrame con la informacion.
    '''
    bonos = pd.DataFrame()
    for i in range(len(nemo)):
        b = "SELECT TOP(1) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Nemotecnico = '" + nemo[i] + "' ORDER BY Fecha DESC"
        b = pd.read_sql(b, cn)
        bonos = bonos.append(b)
    return bonos

def curvaBono(riesgo, moneda, fecha):
    '''
    Funcion que entrega la curva para un bono en base a su riesgo, moneda y la fecha deseada.
    :param riesgo: String del Riesgo del bono.
    :param moneda: String de la moneda del bono.
    :param fecha: String de la fecha que se quiere la curva.
    :return: dataFrame con la informacion.
    '''
    #NO HAY CURVAS PARA RIESGOS QUE NO SEA EN UF.
    if( (riesgo == 'AAA' and moneda == 'CLP') or moneda == 'USD'):
         cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = 'IF#" + moneda + "' AND Fecha = '" + fecha + "'"
    elif(riesgo == 'AA' and moneda == 'CLP'):
        cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Consolidado#No Prepagables' AND Fecha = '" + fecha + "'"
    else:
        cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Corporativos#No Prepagables' AND Fecha = '" + fecha + "'"
    cb = pd.read_sql(cb, cn)
    return cb

def curvaBono2(riesgo, moneda, fecha, n = 1000):
    '''
    Funcion que entrega la curva para un bono en base a su riesgo, moneda, a partir de la fecha deseada.
    :param riesgo: Strign del Riesgo del bono.
    :param moneda: String de la moneda del bono.
    :param fecha: String de la primera fecha que se quieren las curvas.
    :return: dataFrame con la informacion.
    '''
    if( (riesgo == 'AAA' and moneda == 'CLP') or moneda == 'USD'):
         cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = 'IF#" + moneda + "' AND Fecha > '" + fecha + "'"
    elif(riesgo == 'AA' and moneda == 'CLP'):
        cb = "SELECT * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Consolidado#No Prepagables' AND Fecha > '" + fecha + "'"
    else:
        cb = "SELECT TOP(" + str(n) + ") * FROM [dbAlgebra].[dbo].[TdCurvasSector] WHERE TipoCurva LIKE '%" + moneda + "#" + riesgo + "#Corporativos#No Prepagables' AND Fecha > '" + fecha + "'"
    cb = pd.read_sql(cb, cn)
    return cb

def TIR(param, p):
    '''
    Calcula el TIR para el periodo p, en base a los parametros entregados, usando la formula de interpolacion.
    :param param: Dataframe con los parametros de la curva.
    :param p: Plazo donde se evaluará la curva.
    :return: TIR.
    '''
    coef0 = param['ancla']
    coef1 = param['y0']
    coef2 = param['y1']
    coef3 = param['y2']
    tir = np.zeros(len(p))
    for i in range(len(p)):
        tir[i] = (coef1 + (coef0 - coef1) * (1 - np.exp(-(p[i]*360) / coef2)) * (coef2 / (p[i]*360)) + coef3 * ((1 - np.exp(-(p[i]*360) /                        coef2)) * (coef2 / (p[i]*360)) - np.exp(-p[i]*360 / coef2)))
    return tir

def tir_plazos(riesgo, moneda, plazos, p, fecha):
    '''
    Calcula el TIR para dos plazos, en base a la moneda y riesgo asociados.
    :param riesgo: String del riesgo.
    :param moneda: String de la moneda asociada.
    :param plazos: Arreglo de plazos.
    :param p: Arreglo con los indices de los plazos a calcular.
    :param fecha: String de la fecha a usar.
    :return: Arreglo de tamaño 2 con el TIR.
    '''
    curva = curvaBono(riesgo, moneda, fecha)
    tir = np.zeros(2)
    if ((riesgo == 'AAA' and moneda == 'CLP') or moneda == 'USD'):
        tir = TIR(curva, [plazos[p[0]], plazos[p[1]]])
    else:
        for i in range(2):
            c = parsear_curva(curva["StrCurva"][0], add_days(castDay(fecha), int(plazos[p[i]])))
            tir[i] = interpolacion_log_escalarBonos(plazos[p[i]], c)
    return tir

def conversionSYP(riesgo):
    '''
    Funcion que con un diccionario lleva el riesgo de un bono de int al string de la convencion.
    :param riesgo: Int que representa el riesgo de un bono en la base de datos.
    :return: Riesgo en la otra convencion.
    '''
    return {1: 'AAA',2: 'AA',3: 'AA',4: 'AA',5: 'A',6: 'A',7: 'A',8: 'BBB',9: 'BBB',10: 'BBB',\
            11: 'BB+',12: 'BB',13: 'BB-',14: 'B+',15: 'B',16: 'B-',17: 'CCC',18: 'CC+',19: 'CC',20: 'C+',\
            21: 'C',22: 'C-',23: 'D',24: 'E'}.get(riesgo)

def riesgoBono(nemotecnico, fecha):
    '''
    Nos entrega el numero que representa el riesgo de un bono para la fecha indicada.
    :param nemotecnico: String que caracteriza a un bono.
    :param fecha: String de la fecha que se solicita evaluar.
    '''
    riesgo = "SELECT * FROM [dbAlgebra].[dbo].[VwRiesgoRF] WHERE Fecha = '" + fecha + "' AND Nemotecnico = '" + nemotecnico + "'"
    riesgo = pd.read_sql(riesgo, cn)
    return riesgo["Riesgo"].values[0]

def conv(base1, base2):
    if (base1 == -1): base1 = "ACT"
    return str(base1) + "/" + str(base2)

def castDay(strday):
    if(type(strday) != type('hola')): return strday
    else:
        arrayDay = strday.split('-')
        return datetime.date(int(arrayDay[0]), int(arrayDay[1]), int(arrayDay[2]))

def interpolacion_log_escalarBonos(x, XY, n=0, m=0, siExt=True, first=True):
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
        return analisisCasoBorde(x, XY, n, j, siExt, False)
    else:
        return analisisCasoBorde(x, XY, j, m, siExt, False)

def analisisCasoBorde(x, XY, n = 0, m = -1, siExt = True, first = True):
    if(m == -1): m = len(XY)-1
    if (float(XY[n][1]) < 0 or float(XY[m][1]) < 0):
        return interpolacion_escalar(x, XY, n, m, first)
    else:
        return interpolacion_log_escalarBonos(x, XY, n, m, siExt, first)

def historicoPlazos(riesgo, moneda, plazos, p, n=1000):
    # Fecha desde donde tomamos las curvas
    fecha_aux = castDay('2018-01-22')
    # Seleccionamos las curvas
 
    curva = curvaBono2(riesgo,moneda,fecha_aux.strftime("%Y-%m-%d"), n)
    tir = np.zeros([len(curva['Fecha']),len(p)])
    if ((riesgo == 'AAA' and moneda == 'CLP') or moneda == 'USD'):
        # Por cada dia
        for i in range(len(curva['Fecha'])):
            # Por cada periodo
            for j in range(len(p)):
                tir[i][j] = TIR(curva.iloc[[i]], [plazos[p[j]]])
    else:
        # Por cada dia
        for i in range(len(curva['Fecha'])):
            fecha_aux = curva['Fecha'][i].date()    
            # Para cada periodo     
            for j in range(len(p)):
                c = parsear_curva(curva["StrCurva"][i], fecha_aux)
                tir[i][j] = analisisCasoBorde(plazos[p[j]], c)
            
    return tir

def retorno(historico):
    size = len(historico)
    retornos = np.zeros(size-1)
    for i in range(size-1):
        retornos[i] = np.log(historico[i+1]/historico[i])
    return retornos

def retornoPlazos(plazos, historico):
    retornos = pd.DataFrame()
    for i in range(len(plazos)):
        retornos[str(plazos[i]*360)] = retorno(historico[i])
    return retornos

def volatilidad(retornos, l = 0.94):
    n=len(retornos)
    factor = l**np.array(range(n))
    volSinAjuste = sum((1-l)*retornos*retornos*factor[::-1])
    volConAjuste = volSinAjuste/(1-l**(n+1))
    volSinAjuste = np.sqrt(volSinAjuste)
    volConAjuste = np.sqrt(volConAjuste)
    return volConAjuste

def volatilidades(retornos, pivotes):
    vol = np.zeros(len(pivotes))
    for i in range(len(pivotes)):
        vol[i] = volatilidad(retornos[str(pivotes[i]*360)])
    return vol

def volatilidadesPlazo(riesgo, moneda, plazos, p, fecha, hist_plazos):
    # hist_plazos = historicoPlazos(riesgo, moneda, plazos, p)
    if (len(p) == 2):
        ret_plazos = retornoPlazos([plazos[p[0]], plazos[p[1]]], hist_plazos)
        vol_plazos = volatilidades(ret_plazos, [plazos[p[0]], plazos[p[1]]])
    else: 
        ret_plazos = retornoPlazos(plazos, hist_plazos)
        vol_plazos = volatilidades(ret_plazos, plazos)
    return vol_plazos

def pivNear(dia, periodos):
    '''
    Funcion que entrega los indices de los periodos en el arreglo que colindan a la fecha a evaluar
    :param: dia: Plazo correspondiente a la fecha a evaluar
    :param: periodos: Arreglo de plazos
    '''
    pivotes = [-1,-1]
    for i in range(len(periodos)):
        if (dia < periodos[0]):
            pivotes[1] = 0
        elif(dia > periodos[len(periodos)-1]):
            pivotes[0] = len(periodos)-1
        elif(dia > periodos[i]):
            pivotes[1] = i+1
            pivotes[0] = i
        elif (dia == periodos[i]):
            pivotes[0] = pivotes[1] = i
    return pivotes

def sumatoria(lam, r, i, j):
    N = len(r.values[:,0])
    valor = 0
    for k in range(N):
        valor += (lam**k) * r.values[N-k-1,i] * r.values[N-k-1,j]
    return valor

def correlacion(r, pivotes, vol, lam = 0.94):
    size = len(pivotes)
    corr = np.zeros([size, size])
    for i in range(size):
        for j in range(i+1, size):
            corr[i][j] = (1 - lam) * sumatoria(lam, r, i, j) / (vol[i] * vol[j])
    return corr

def resuelve(a,b,c):
    delta = b**2 - 4*a*c
    assert delta > 0 , "Los parámetros generan soluciones complejas"
    x_1 = (-b + delta**(1/2))/ 2*a
    x_2 = (-b - delta**(1/2))/ 2*a
    if (x_1 > 0 and 1 > x_1): return x_1
    else : return x_2

def extraccion(matriz, periodos):
    size = len(periodos)
    correlaciones = np.zeros(size-1)
    for i in range(size-1):
        correlaciones[i] = matriz[i][i+1]
    return correlaciones

def actualizar(alfa, vp, piv, flujo, p):
    if(piv[0] == -1 or p[piv[1]] == p[piv[0]]):
        flujo[0] += vp
    elif (piv[1] == -1):
        flujo[len(flujo)-1] += vp*alfa
    else:
        flujo[piv[0]] += vp*alfa
        flujo[piv[1]] += vp*(1-alfa)
    return flujo

def proyeccionBonos(nemo, plazos, fecha, bonos):
    '''
    Proyecta los bonos en los plazos dependiendo de su moneda
    :param: nemo: Arreglo que contiene los nemotecnicos de los bonos
    :param: plazos: Arreglo con los periodos a usar
    :para: fecha: String con la fecha para traer a valor presente
    :para: bonos: DataFrame con la info de los bonos (Base de datos)
    :return: proyeccion: Diccionario con las proyecciones segun moneda
    '''
    # bonos = bonosNemo(nemo)
    proyeccion = np.zeros(len(plazos))
    flujo_plazos = np.zeros(len(plazos))
    dic = {'USDAAA': np.zeros(len(plazos)),\
           'CLPAAA': np.zeros(len(plazos)), \
           'UFAAA' : np.zeros(len(plazos)),
           'EURAAA' : np.zeros(len(plazos)),
           'USDAA': np.zeros(len(plazos)),\
           'CLPAA': np.zeros(len(plazos)), \
           'UFAA' : np.zeros(len(plazos)),
           'EURAA' : np.zeros(len(plazos)),
           'USDA': np.zeros(len(plazos)),\
           'CLPA': np.zeros(len(plazos)), \
           'UFA' : np.zeros(len(plazos)),
           'EURA' : np.zeros(len(plazos))}

    # riesgos = pd.DataFrame()
    riesgos = []
    for i in range(len(nemo)):
        # riesgos = riesgos.append([conversionSYP(riesgoBono(nemo[i], fecha))])
        riesgos.append(conversionSYP(riesgoBono(nemo[i], fecha)))
    # riesgos.rename(columns={0:'Riesgo'}, inplace=True)
    
    # Bono con su informacion de riesgo 
    bonos["Riesgo"] = riesgos
    br = bonos    
    # Por cada bono
    for i in range(len(br)):
        r = br["Riesgo"][i]
        moneda = br["Moneda"][i]
        convencion = conv(br["Base1"][i], br["Base2"][i])
        cupones = StrTabla2ArrTabla(br["TablaDesarrollo"][i], br["FechaEmision"][i].to_pydatetime().date().strftime("%Y-%m-%d"))
        p = list(range(len(plazos)))
        hist_plazos = historicoPlazos(r, moneda, plazos, p)
        ret_plazos = retornoPlazos(plazos, hist_plazos)
        vol_plazos = volatilidadesPlazo(r, moneda, plazos, p, fecha, hist_plazos) # Se puede entregar volatilidades.
        matriz_corr = correlacion(ret_plazos, plazos, vol_plazos)
        corr = extraccion(matriz_corr, plazos) # Se puede entregar matriz_corr.
      # Por cada cupon
        for j in range(len(cupones)):
            d = plazo_anual_convencion(convencion, castDay(fecha), cupones[j][1].date())
            if (d < 0): continue

            p = pivNear(d, plazos)
            flujo = cupones[j][6]
            tir_p = tir_plazos(r, moneda, plazos, p, fecha)

            if (p[1] == -1): 
                flujo_plazos[p[0]] += flujo / (1 + tir_p[p[0]])**d
                continue
            elif (p[0] == -1): 
                flujo_plazos[p[1]] += flujo / (1 + tir_p[p[1]])**d
                continue

            a_0 = (d - plazos[p[0]]) / (plazos[p[1]] - plazos[p[0]])

            tir_p = tir_plazos(r, moneda, plazos, p, fecha)
            tir = a_0 * tir_p[0] + (1 - a_0) * tir_p[1]

            vol_p = vol_plazos#volatilidadesPlazo(r, moneda, plazos, p, fecha)
            vol = a_0 * vol_p[0] + (1 - a_0) * vol_p[1]

            vp = flujo / (1 + tir)**d

            m = p[1] - 2
            alfa = resuelve(vol_p[0]**2 + vol_p[1]**2 - 2 * corr[m] * vol_p[0] * vol_p[1], 2 * corr[m] *vol_p[0] * vol_p[1] - 2 * vol_p[1]**2, vol_p[1]**2 - vol**2 )

            flujo_plazos = actualizar(alfa, vp, p, flujo_plazos, plazos)
        dic[moneda + r] += flujo_plazos
    return dic

def nombre_columna(moneda, riesgo, pivotes):
    """
    Crea arreglo con nombres de columnas para usar en retornos.
    param: moneda: Str. Moneda.
    param: riesgo: Str. Riesgo.
    param: pivotes: Arreglo 1-dim. Pivotes en días.
    return: Arreglo 1-dim. Arreglo con str.
    """
    arr = []
    for pivote in pivotes:
        arr.append(str(pivote)+riesgo+moneda)
    return arr

def extraccionBono(vec, matriz):
    '''
    Extrae la diagonal superior de la matriz de covarianza.
    param: vec: Arreglo con los indices de la ubicación a extraer.
    param: matriz: Matriz de covarianza.
    return: Arreglo 1-dim con las correlaciones consecutivas entre los pivotes.
    '''
    a = vec[0]
    b = vec[1]
    corr = np.zeros(b-a)
    k = 0
    for i in range(a+1, b+1):
        for j in range(a,b):
            corr[k] = matriz[i][j]
            k += 1
    return corr

