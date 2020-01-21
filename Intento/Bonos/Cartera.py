# %%
import pyodbc
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math
import datetime
from time import time
from UtilesValorizacion import plazo_anual_convencion, add_days, StrTabla2ArrTabla, factor_descuento

# %%
# Entrada al servidor
driver = '{SQL Server}'
username = 'practicantes'
password = 'PBEOh0mEpt'
cn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + '192.168.30.200' + ';UID=' + username + ';PWD=' + password)

# %%
año = 1
periodos = [1/12 * año, 1/4* año, 1/2 * año, año, 2* año, 3* año, 4*año, 5* año, 7* año, 9* año, 10*año, 15* año, 20* año, 30* año]

# %%
# Parametros de la curva para obtención del TIR
def seleccionar_curva(tipo):
    cte_curva = ("SELECT [Fecha],[ancla],[y0],[y1],[y2],[Tipo]FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = '" + tipo + "' ORDER BY Fecha ASC") # 
    cte_curva = pd.read_sql(cte_curva, cn)
    return cte_curva
def seleccionar_curva2(tipo, fecha):
    cte_curva = ("SELECT [Fecha],[ancla],[y0],[y1],[y2],[Tipo]FROM [dbAlgebra].[dbo].[TdCurvaNS] WHERE Tipo = '" + tipo + "' AND Fecha = '" + fecha + "' ORDER BY Fecha ASC")
    cte_curva = pd.read_sql(cte_curva, cn)
    return cte_curva
# Bonos para valorizar a valor presente
def seleccionar_bonos(moneda, fecha, emisor):
    bonos = ("SELECT TOP (1000) [Fecha],[Emisor],[Nemotecnico],[Moneda],[Monto],[CorteMin],[CorteMax],[Plazo],[FechaEmision],[FechaVenc],[Pago],[nCup],[nAmort],[TablaDesarrollo],[Base1],[Base2] FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda = '" + moneda + "' AND FechaEmision = '" + fecha + "' AND Emisor = '" + emisor + "'")
    bonos = pd.read_sql(bonos, cn)
    return bonos
def seleccionar_bonos2(moneda, emisor):
    bonos = ("SELECT TOP (1000) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda = '" + moneda + "' AND Emisor = '" + emisor + "' ORDER BY FechaEmision DESC")
    bonos = pd.read_sql(bonos, cn)
    return bonos
def seleccionar_bonos3(moneda):
    bonos = ("SELECT TOP (100) * FROM [dbAlgebra].[dbo].[TdNemoRF] WHERE Moneda = '" + moneda + "'")
    bonos = pd.read_sql(bonos, cn)
    return bonos

# %%
# Funcion que lleva un dia en string a formato date
def castDay(strday):
    arrayDay = strday.split('-')
    return datetime.date(int(arrayDay[0]), int(arrayDay[1]), int(arrayDay[2]))

# %%
# Nos entrega el TIR para un periodo segun los parametros de la curva n
def getFact(param, l, n):
    i = l * 360
    fecha = param['Fecha'][n].to_pydatetime().date()
    coef0 = param['ancla'][n]
    coef1 = param['y0'][n]
    coef2 = param['y1'][n]
    coef3 = param['y2'][n]
    tir = coef1 + (coef0 - coef1) * (1 - np.exp(-(i) / coef2)) * (coef2 / (i)) + coef3 * (
            (1 - np.exp(-(i) / coef2)) * (coef2 / (i)) - np.exp(-(i) / coef2))
    fact = factor_descuento(tir, fecha, add_days(fecha,i), "ACT360",0)
    return fact

# %%
def historicoPeriodo(param, periodo):
    n_curvas = len(param['ancla'])
    fact = np.zeros(n_curvas)
    for i in range(n_curvas):
        fact[i] = getFact(param, periodo, i)
    return fact

# %%
param = seleccionar_curva("IF#CLP")

for i in range(len(periodos)):
    plt.plot(historicoPeriodo(param, periodos[i]), label = str(periodos[i]))
plt.gca().legend(periodos)
plt.show()

# %%
# Sacamos retornos de los historicos
#historico360 = historicoPeriodo(param, 1)

def retorno(historico):
    size = len(historico)
    retornos = np.zeros(size-1)
    for i in range(size-1):
        retornos[i] = np.log(historico[i+1]/historico[i])
    return retornos

#retorno360 = retorno(historico360)
#print(retorno360)

# %%
# Volatilidad aplicando el metodo EWMA
def volatilidad(retornos, l = 0.94):
    n=len(retornos)
    factor = l**np.array(range(n))
    volSinAjuste = sum((1-l)*retornos*retornos*factor[::-1])
    volConAjuste = volSinAjuste/(1-l**(n+1))
    volSinAjuste = np.sqrt(volSinAjuste)
    volConAjuste = np.sqrt(volConAjuste)
    return volConAjuste

#volatilidad360 = volatilidad(retorno360)
#print(volatilidad360)

# %%
def sumatoria(lam, r, i, j):
    N = len(r.values[:,0])
    valor = 0
    for k in range(N):
        valor += (lam**k) * r.values[N-k-1,i] * r.values[N-k-1,j]
    return valor

def correlacion(r, pivotes, volatilidad, lam = 0.94):
    size = len(pivotes)
    corr = np.zeros([size, size])
    for i in range(size):
        for j in range(i+1, size):
            corr[i][j] = (1 - lam) * sumatoria(lam, r, i, j) / (volatilidad[i] * volatilidad[j])
    return corr
   

# %%
def historicos(pivotes, param):
    M = len(pivotes)
    historico = pd.DataFrame()
    for i in range(M):
        historico[str(pivotes[i]*360)] = historicoPeriodo(param, pivotes[i])
    return historico

param = seleccionar_curva("IF#CLP")
historico = historicos(periodos, param)

def retornos(historico, pivotes):
    retornos = pd.DataFrame()
    for i in range(len(pivotes)):
        retornos[str(pivotes[i]*360)] = retorno(historico[str(pivotes[i]*360)])
    return retornos

retornos = retornos(historico, periodos)

def volatilidades(retornos, pivotes):
    vol = np.zeros(len(pivotes))
    for i in range(len(pivotes)):
        vol[i] = volatilidad(retornos[str(pivotes[i]*360)])
    return vol

volatilidadess = volatilidades(retornos, periodos)

matriz_corr = correlacion(retornos, periodos, volatilidadess)
#print(pd.DataFrame(matriz_corr))

# %%
def extraccion(matriz, periodos):
    size = len(periodos)
    correlaciones = np.zeros(size-1)
    for i in range(size-1):
        correlaciones[i] = matriz[i][i+1]
    return correlaciones

#corrAB = extraccion(matriz_corr, periodos)
#print(corrAB)

# %%
def pivNear(dia, periodos):
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

# Entrega el ponderador inicial para la extrapolación lineal
def getAlfa(piv, f_d, p):
    if(piv[0] == -1):
        return 0
    elif (piv[1] == -1):
        return (f_d - p[piv[0]])/(40 - p[piv[0]])
    elif(p[piv[1]] == p[piv[0]]):
        return 1 ########
    else : 
        return (f_d - p[piv[0]])/(p[piv[1]] - p[piv[0]])
    
# Resuelve la ecuacion cuadratica para el ponderador final
def resuelve(a,b,c):
    delta = b**2 - 4*a*c
    assert delta > 0 , "Los parámetros generan soluciones complejas"
    x_1 = (-b + delta**(1/2))/ 2*a
    x_2 = (-b - delta**(1/2))/ 2*a
    print("Las soluciones fueron: ", x_1, x_2)
    return min(x_1,x_2)

# Acualiza el valor de los pivotes
def actualizar(alfa, vp, piv, flujo, p):
    if(piv[0] == -1 or p[piv[1]] == p[piv[0]]):
        flujo[0] += vp
    elif (piv[1] == -1):
        flujo[len(flujo)-1] += vp*alfa
    else:
        flujo[piv[0]] += vp*alfa
        flujo[piv[1]] += vp*(1-alfa)
    return flujo

def TIR(param, p):
    coef0 = param['ancla']
    coef1 = param['y0']
    coef2 = param['y1']
    coef3 = param['y2']
    tir = np.zeros(len(p))
    for i in range(len(p)):
        tir[i] = coef1 + (coef0 - coef1) * (1 - np.exp(-(p[i]*360) / coef2)) * (coef2 / (p[i]*360)) + coef3 * (
            (1 - np.exp(-(p[i]*360) / coef2)) * (coef2 / (p[i]*360)) - np.exp(-p[i]*360 / coef2))
    return tir

# %%
def distribucion(pivotes, bonos, n_bono, tir_piv, vol_piv, corr,convencion):
    fecha = bonos["FechaEmision"][n_bono].to_pydatetime().date()
    flujo_piv = np.zeros(len(pivotes))
    print("El flujo inicial es: ", flujo_piv)
    cupon = StrTabla2ArrTabla(bonos["TablaDesarrollo"][n_bono], bonos["FechaEmision"][n_bono].to_pydatetime().date().strftime("%Y-%m-%d"))
    print("La cantidad de cupones es: ", len(cupon))
    # Para cada cupon
    for i in range(len(cupon)):
        D_flujo = plazo_anual_convencion(convencion, fecha, cupon[i][1].date())
        if(D_flujo < 0): continue
        p = pivNear(D_flujo, pivotes)
        if (p[1] == -1): 
            flujo_piv[p[0]] += flujo / (1 + tir_piv[p[0]])**D_flujo
            continue
        alfa_0 = getAlfa(p, D_flujo, pivotes)
        tir_f = alfa_0 * tir_piv[p[0]] + (1 - alfa_0) * tir_piv[p[1]]
        sigma_f = alfa_0 * vol_piv[p[0]] + (1 - alfa_0) * vol_piv[p[1]]
        flujo = cupon[i][3]
        vp = flujo / (1 + tir_f)**D_flujo
        print("El cupon es: ", flujo, "| El valor presente es: ", vp)
        m = p[1] - 2
        final_alfa = resuelve(vol_piv[p[0]]**2 + vol_piv[p[1]]**2 - 2* corr[m] * vol_piv[p[1]]* vol_piv[p[0]],- 2*vol_piv[p[1]]**2 + 2* corr[m] * vol_piv[p[1]]* vol_piv[p[0]], vol_piv[p[1]]**2 - sigma_f**2)
        flujo_piv = actualizar(final_alfa, vp, p, flujo_piv, pivotes)
    return flujo_piv

# %%
bonos = seleccionar_bonos3("CLP")
curva = param[param.Fecha == str(bonos["FechaEmision"][0])]
print(curva)
tir_piv = TIR(curva,periodos)
vol_piv = volatilidades(retornos, periodos)
corr = extraccion(matriz_corr, periodos)
convencion = "ACT360"

flujo = distribucion(periodos, bonos, 0, tir_piv, vol_piv, corr,convencion)
print(flujo)

# %%

