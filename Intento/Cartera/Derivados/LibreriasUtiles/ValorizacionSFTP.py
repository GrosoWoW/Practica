# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 10:59:18 2019

@author: Victor Carmi
@edited: Matías Villegas
"""

import pyodbc
import pandas as pd
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
import numpy as np
import datetime
from Util import fecha_str
from Derivados.Empresa import Empresa
from UtilesDerivados import ultimo_habil_pais, ultimo_habil_paises, siguiente_habil_paises
from UtilesSftp import get_files, move_file, put_file
import os
import os.path

# Credenciales para la base de datos
import ConfiguracionConexiones
conexiones = ConfiguracionConexiones.Conexiones_produccion()
#myHostname = "ftp.lvaindices.com" 
#myUsername = "lva-derivados"
#myPassword = "1JC8cP"


def ValorizarCartera(fecha, hostname, username, password, conexiones, raiz='/Cartera'):
    """
    Función para realizar la valorización de cartera a un SFTP
    Se asume existencia del directorio Cartera y sus subcarpetas
    :param fecha: datetime.date con fecha para valorizacion
    :param hora: string con hora para valorizacion ('1500' o '1700')
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param conexiones: objeto Conexiones_produccion para obtener conexiones
    :param origen: string con carpeta origen
    :return: None
    """

    # Revisamos carpeta Cartera para valorizar:
    archivos = get_files(hostname, username, password, raiz+"/Cartera/")
    
    # Si no hay archivos para valorizar
    if len(archivos) == 0:
        print("No hay archivos para valorizar")
        return

    print("Valorizando Cartera en",hostname,"-",username)
    print("Hay",len(archivos),"archivo(s) para valorizar\n")

    ini = datetime.datetime.now()

    # Contador de archivos leidos
    leidos = 0
    total = len(archivos)

    # Por cada archivo
    for nombre_archivo in archivos:
        leidos += 1

        # Se intenta procesar
        try:
            print("\nLeyendo archivo (" + str(leidos) + " de " + str(total) + "): ", nombre_archivo)
            # Obtenemos la data de derivados
            info = pd.read_csv(nombre_archivo, sep=',')

            print("Revisando input")
            # Se revisa que el input sea válido
            errores = revisar_input(info, fecha)

            # Si hay errores de input, se dejan en la carpeta de error
            if len(errores)>0:
                print("Se encontraron problemas de input:")
                
                archivo_error = nombre_archivo.split(".")[0] + "_log_errores.txt"

                f = open(archivo_error, "w")
                for error in errores:
                    print(error)
                    f.write(error + "\n")
                f.close()

                put_file(hostname, username, password, "./", raiz+"/ERROR/" + fecha.strftime("%Y-%m-%d/"), archivo_error, archivo_error)

                raise("ERROR: problemas con el archivo")

            # Si no se encuentran errores
            else:
                # Creamos el objeto empresa para valorizar todos los derivados en la variable info
                empresa = Empresa(fecha, info, conexiones.get_input(), nombre_archivo)

                #Valorizacion
                print("Valorizando archivo...")
                empresa.procesar_todo()
                flujos = empresa.get_flujos_valorizados(False)
                flujos = flujos.sort_values(by="ID").reset_index(drop=True)


                
                print("Generando archivos CSV")
                # Se generan los archivos([0] -> flujos, [1] -> derivado)
                archivos_valorizados = flujos_csv(flujos, nombre_archivo, empresa.estado_valorizacion)
                
                # Se cargan los flujos al SFTP
                print("Cargando archivo valorizado a SFTP")

                # Se suben las valorizaciones
                put_file(hostname, username, password, "./", raiz+"/Output/"+ fecha.strftime("%Y-%m-%d/"), archivos_valorizados[0])
                put_file(hostname, username, password, "./", raiz+"/Output/"+ fecha.strftime("%Y-%m-%d/"), archivos_valorizados[1])

                # Se borran los archivos locales
                os.remove(nombre_archivo)
                os.remove(archivos_valorizados[0])
                os.remove(archivos_valorizados[1])



        # Si no se pudo procesar, se pasa el archivo a la carpeta de error
        except Exception as e:
            print("Error con el archivo: ",nombre_archivo)
            # Se borran los archivos locales
            os.remove(nombre_archivo)
            
            # Se mueve a carpeta de error
            move_file(hostname, username, password, raiz + '/Cartera/', raiz+'/ERROR/' + fecha.strftime("%Y-%m-%d/"), nombre_archivo, new_filename=None)

            raise(e)
    print("\nProceso terminado en", (datetime.datetime.now()-ini).seconds/60, "minutos")




def AgregarNuevosCartera(fecha, hostname, username, password, raiz='/Cartera'):
    """
    Función para agregar nuevos archivos a la cartera
    Se asume existencia del directorio Cartera y sus subcarpetas
    :param fecha: datetime.date con fecha para valorizacion
    :param hora: string con hora para valorizacion ('1500' o '1700')
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param conexiones: objeto Conexiones_produccion para obtener conexiones
    :param origen: string con carpeta origen
    :return: int con la cantidad de archivos fallidos
    """

    total_fallidos = 0

    # Revisamos carpeta nuevos para agregar a cartera:
    archivos = get_files(hostname, username, password, raiz+"/Nuevos/")
    
    # Si no hay archivos para agregar
    if len(archivos) == 0:
        print("No hay archivos para agregar a cartera")
        # no se agregaron
        return total_fallidos

    print("Agregando nuevos en",hostname,"-",username)
    print("Hay",len(archivos),"archivo(s) para agregar\n")

    ini = datetime.datetime.now()

    # Contador de archivos leidos
    leidos = 0
    total = len(archivos)

    # Por cada archivo
    for nombre_archivo in archivos:
        leidos += 1

        # Se intenta procesar
        try:
            print("\nLeyendo archivo (" + str(leidos) + " de " + str(total) + "): ", nombre_archivo)
            # Obtenemos la data de derivados
            info = pd.read_csv(nombre_archivo, sep=',')

            print("Revisando input")
            # Se revisa que el input sea válido
            errores = revisar_input(info, fecha)

            # Si hay errores de input, se dejan en la carpeta de error
            if len(errores)>0:
                print("Se encontraron problemas de input:")
                
                archivo_error = nombre_archivo.split(".")[0] + "_log_errores.txt"

                f = open(archivo_error, "w")
                for error in errores:
                    print(error)
                    f.write(error + "\n")
                f.close()

                put_file(hostname, username, password, "./", raiz+"/ERROR/" + fecha.strftime("%Y-%m-%d/"), archivo_error, archivo_error)

                raise("ERROR: problemas con el archivo")

            # Si no se encuentran errores
            else:
                
                move_file(hostname, username, password, raiz+'/Nuevos/', raiz+'/Cartera/', nombre_archivo)
                print("Agregado",nombre_archivo,"a la cartera")


        # Si no se pudo procesar, se pasa el archivo a la carpeta de error
        except:
            print("Error con el archivo: ",nombre_archivo)
            total_fallidos += 1
            # Se borran los archivos locales
            os.remove(nombre_archivo)
            
            # Se mueve a carpeta de error
            move_file(hostname, username, password, raiz + '/En_proceso/', raiz+'/Error_nuevo/' + fecha.strftime("%Y-%m-%d/"), nombre_archivo, new_filename=None)

    if total_fallidos>0:
        raise("ERROR: Hay derivados nuevos con error")
    print("\nProceso terminado en", (datetime.datetime.now()-ini).seconds/60, "minutos")




def ValorizarRequest(fecha, hostname, username, password, conexiones, raiz='/Request'):
    """
    Función para realizar la valorización por request a un SFTP
    Se asume existencia del directorio Request y sus subcarpetas
    :param fecha: datetime.date con fecha para valorizacion
    :param hora: string con hora para valorizacion ('1500' o '1700')
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param conexiones: objeto Conexiones_produccion para obtener conexiones
    :param origen: string con carpeta origen
    :return: None
    """

    # Revisamos carpeta input para Requests:
    archivos = get_files(hostname, username, password, raiz+"/Input/")
    
    # Si no hay archivos para valorizar
    if len(archivos) == 0:
        print("No hay archivos para valorizar")
        return

    print("Valorizando Request en",hostname,"-",username)
    print("Hay",len(archivos),"archivo(s) para valorizar\n")

    ini = datetime.datetime.now()

    # Contador de archivos leidos
    leidos = 0
    total = len(archivos)

    # Por cada archivo
    for nombre_archivo in archivos:
        leidos += 1

        # Se mueve el archivo a carpeta de En_proceso
        move_file(hostname, username, password, raiz + '/Input/', raiz + '/En_proceso/', nombre_archivo)

        # Se intenta procesar
        try:
            print("\nLeyendo archivo (" + str(leidos) + " de " + str(total) + "): ", nombre_archivo)
            # Obtenemos la data de derivados
            info = pd.read_csv(nombre_archivo, sep=',')

            print("Revisando input")
            # Se revisa que el input sea válido
            errores = revisar_input(info, fecha)

            # Si hay errores de input, se dejan en la carpeta de error
            if len(errores)>0:
                print("Se encontraron problemas de input:")
                
                archivo_error = nombre_archivo.split(".")[0] + "_log_errores.txt"

                f = open(archivo_error, "w")
                for error in errores:
                    print(error)
                    f.write(error + "\n")
                f.close()

                put_file(hostname, username, password, "./", raiz+"/ERROR/" + fecha.strftime("%Y-%m-%d/"), archivo_error, archivo_error)

                raise("ERROR: problemas con el archivo")

            # Si no se encuentran errores
            else:
                # Creamos el objeto empresa para valorizar todos los derivados en la variable info
                empresa = Empresa(fecha, info, conexiones.get_input(), nombre_archivo)

                #Valorizacion
                print("Valorizando archivo...")
                empresa.procesar_todo()
                flujos = empresa.get_flujos_valorizados(False)
                flujos = flujos.sort_values(by="ID").reset_index(drop=True)


                # Se cargan los flujos al SFTP
                print("Cargando archivo valorizado a SFTP")
                
                # Se generan los archivos([0] -> flujos, [1] -> derivado)
                archivos_valorizados = flujos_csv(flujos, nombre_archivo, empresa.estado_valorizacion)
                
                # Se suben las valorizaciones
                put_file(hostname, username, password, "./", raiz+"/Output/"+ fecha.strftime("%Y-%m-%d/"), archivos_valorizados[0])
                put_file(hostname, username, password, "./", raiz+"/Output/"+ fecha.strftime("%Y-%m-%d/"), archivos_valorizados[1])

                # Se mueve de proceso a historico
                move_file(hostname, username, password, raiz+'/En_proceso', raiz+'/Historico/'+fecha.strftime("%Y-%m-%d/"), nombre_archivo)

                # Se borran los archivos locales
                os.remove(nombre_archivo)
                os.remove(archivos_valorizados[0])
                os.remove(archivos_valorizados[1])



        # Si no se pudo procesar, se pasa el archivo a la carpeta de error
        except Exception as e:
            print("Error con el archivo: ",nombre_archivo)
            # Se borran los archivos locales
            os.remove(nombre_archivo)
            
            # Se mueve a carpeta de error
            move_file(hostname, username, password, raiz + '/En_proceso/', raiz+'/ERROR/' + fecha.strftime("%Y-%m-%d/"), nombre_archivo, new_filename=None)

            raise(e)
    print("\nProceso terminado en", (datetime.datetime.now()-ini).seconds/60, "minutos")


def flujos_csv(flujos, filename, estado_valorizacion):
    """
    Genera archivos csv con los flujos entregados y su valorización correspondiente
    :param flujos: pandas dataframe con los flujos
    :param filename: nombre para crear archivos csv (flujos+filename y derivados+filename)
    :return: lista con los nombres de los archivos [flujos, derivados]
    """

    flujos["TipoValorizacion"] = estado_valorizacion

    # Elimino la columna index que no se usa
    flujos=flujos.drop(['index'], axis=1)
    valorizacion_flujos_csv = 'flujos_'+filename
    flujos.to_csv(r''+valorizacion_flujos_csv,index=False)


    # Se genera un dataframe con la valorización
    valorizacion_derivado = pd.DataFrame({'TipoValorizacion':flujos['TipoValorizacion'],'Fecha':flujos['Fecha'],'ID':flujos['ID'],'Fondo':flujos['Fondo'],'Tipo':flujos['Tipo'],
                             'ValorPresenteCLP':flujos['ValorPresenteCLP']*flujos['ActivoPasivo'],'ValorPresensteUSD':flujos['ValorPresenteUSD']*flujos['ActivoPasivo'],
                             'MonedaBase':flujos['MonedaBase'],'ValorPresenteMonBase':flujos['ValorPresenteMonBase']*flujos['ActivoPasivo']})
                             
    # Se suman los valor-presente
    valorizacion_derivado = valorizacion_derivado.groupby(['TipoValorizacion','Fecha','ID','Fondo','Tipo','MonedaBase']).sum()
    valorizacion_derivado = valorizacion_derivado.reset_index()

    valorizacion_derivado_csv = 'derivados_'+filename
    valorizacion_derivado.to_csv(r''+valorizacion_derivado_csv,index=False)
    
    # Se retornan los nombres de los archivos
    return [valorizacion_flujos_csv, valorizacion_derivado_csv]


def revisar_input(info, fecha):
    """
    Se revisa la info para verificar de que los derivados sean validos para valorizar
    :param info: pandas dataframe con la información de los derivados
    :parma fecha: fecha en la que se desea valorizar
    :return: lista con mensajes de error. Si la lista va vacía no hubo errores.
    """

    if len(info) == 0:
        return ["ERROR: Archivo sin informacion"]

    tipos_soportados = ["FWD", "SUC", "SCC", "XCCY"]
    monedas_soportadas = ["CLP","UF","USD","COP","MXN","PEN","EUR"]


    error = []

    columnas = info.columns

    if "Tipo" not in columnas:
        error.append("ERROR: Falta ingresar columna Tipo")

    elif not info.equals(info.loc[info.Tipo.isin(tipos_soportados)]):
        error.append("ERROR: Hay un Tipo de derivado no soportado")
    
    if "Fondo" not in columnas:
        error.append("ERROR: Falta ingresar columna Fondo")

    elif not is_string_dtype(info.Fondo):
        error.append("ERROR: Fondo debe ser texto")

    if "ID" not in columnas:
        error.append("ERROR: Falta ingresar columna ID")
    
    
    if "NocionalActivo" not in columnas:
        error.append("ERROR: Falta ingresar columna NocionalActivo")
    elif not is_numeric_dtype(info.NocionalActivo):
        error.append("ERROR: NocionalActivo debe ser número")


    if not("MonedaBase" not in info.columns or info.equals(info.loc[info.MonedaBase.isin(monedas_soportadas)])):
        error.append("ERROR: Hay una moneda no soportada en MonedaBase")

    if "MonedaActivo" not in info.columns :
        error.append("ERROR: Falta ingresar columna MonedaActivo")

    elif not info.equals(info.loc[info.MonedaActivo.isin(monedas_soportadas)]):
        error.append("ERROR: Hay una moneda no soportada en MonedaActivo")

    try:

        if "FechaVenc" not in columnas:
            error.append("ERROR: Falta ingresar columna FechaVenc")

        elif  len(info.loc[info["FechaVenc"].apply(lambda x : datetime.datetime.strptime(x, "%d/%m/%Y").date()) < fecha]) > 0:
            error.append("ERROR: Fecha vencimiento anterior a la fecha de valorizacion.")

    except ValueError:

        error.append("ERROR: Fecha vencimiento debe estar en formato dd/mm/aaaa.")


    info_fwd = info.loc[info.Tipo=="FWD"]
    info_suc = info.loc[info.Tipo=="SUC"]
    info_scc = info.loc[info.Tipo=="SCC"]
    info_xccy = info.loc[info.Tipo=="XCCY"]

    error += revisar_input_FWD(info_fwd, monedas_soportadas, fecha)
    error += revisar_input_SCC(info_scc, fecha)
    error += revisar_input_SUC(info_suc, fecha)
    error += revisar_input_XCCY(info_xccy, fecha)

    return error


def revisar_input_FWD(info, monedas_soportadas, fecha):
    error = []
    if len(info) == 0:
        return error

    columnas = info.columns

    if "NocionalPasivo" not in columnas:
        error.append("ERROR: [FWD]Falta ingresar columna NocionalPasivo")
    elif not info.equals(info.loc[info.NocionalPasivo.apply(lambda x: type(x)!=str)]):
            error.append("ERROR: [FWD]NocionalPasivo debe ser número")
    
    
    if "MonedaPasivo" not in info.columns :
        error.append("ERROR: [FWD]Falta ingresar columna MonedaPasivo")

    elif not info.equals(info.loc[info.MonedaPasivo.isin(monedas_soportadas)]):
        error.append("ERROR: [FWD]Hay una moneda no soportada en MonedaPasivo")

    return error


def revisar_input_SCC(info, fecha):
    error = []

    columnas = info.columns

    try:
        if "FechaEfectiva" not in columnas:
            error.append("ERROR: Falta ingresar columna FechaEfectiva")
        else:
            info["FechaEfectiva"].apply(lambda x : datetime.datetime.strptime(x, "%d/%m/%Y").date())
    except ValueError:
        error.append("ERROR: FechaEfectiva debe estar en formato dd/mm/aaaa.")

    if "TipoTasaActivo" not in info.columns:
        error.append("ERROR: Falta ingresar columna TipoTasaActivo")

    elif not info.equals(info.loc[info.TipoTasaActivo.apply(lambda x: type(x)==str)]):
        error.append("ERROR: TipoTasaActivo debe ser texto")

    elif not info.equals(info.loc[info.TipoTasaActivo.apply(lambda x: x=="Fija" or x=="Flotante")]):
        error.append("ERROR: TipoTasaActivo no soportada")

    else:
        fijos = info.loc[info.TipoTasaActivo=="Fija"]
        flotantes = info.loc[info.TipoTasaActivo=="Flotante"]

    return error

def revisar_input_SUC(info, fecha):
    error = []


    return error

def revisar_input_XCCY(info, fecha):
    error = []
    return error





    
    
    
