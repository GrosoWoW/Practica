# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
import calendar
import numpy as np


def es_bisiesto(fecha):  # La función sirve como azucar sintactico
    """Retorna un booleano indicando si el año de la fecha ingresada corresponde a un año bisiesto

    :param fecha: datetime.date con una fecha
    :return: bool indicando si el año de la fecha es bisiesto
    """
    return calendar.isleap(fecha.year)


def fecha_str(fecha):  # La funcion sirve como azucar sintactico
    """Entrega la fecha en formato string para consultas SQL
    :param fecha: Fecha para transformar a string
    :return: String con al fecha en formato YYYYMMDD
    """
    return fecha.strftime("'%Y%m%d'")


def add_days(fecha, dias):   # La funcion sirve como azucar sintactico
    """Entrega la fecha con la cantidad de dias agregados
    :param fecha: datetime.date con la fecha que se le desea agregar la cantidad de dias
    :param dias: int cantidad de dias que se desea agregar, puede ser negativo.
    :return: datetime.date con la fecha correspondiente
    """
    return fecha + relativedelta(days=dias)


def add_months(fecha, meses):   # La funcion sirve como azucar sintactico
    """Entrega la fecha con la cantidad de meses agregados
    :param fecha: datetime.date con la fecha que se le desea agregar la cantidad de meses
    :param meses: int cantidad de meses que se desea agregar, puede ser negativo
    :return: datetime.date con la fecha correspondiente
    """
    return fecha + relativedelta(months=meses)


def add_years(fecha, anhos):   # La funcion sirve como azucar sintactico
    """Entrega la fecha con la cantidad de años agregados
        :param fecha: datetime.date con la fecha que se le desea agregar la cantidad de años
        :param anhos: int cantidad de años que se desea agregar, puede ser negativo
        :return: datetime.date con la fecha correspondiente
        """
    return fecha + relativedelta(years=anhos)


def remove_col(arr, col):
    """Remueve la columna col del arr y lo retorna.
    NO muta el arr original

    :param arr: pandas dataframe que se le desea eliminar una columna
    :param col: Columna que se desea eliminar (indexado desde 0)
    """
    return arr.iloc[:, [j for j, c in enumerate(arr.columns) if j != col]]
    # return arr.drop(arr.columns[col], axis=1) Esta forma elimina las columnas con nombres repetidos


def sub_arr(arr, xi, yi, xf, yf, filename="placeholder"):
    """Retorna un sub-arreglo del arreglo arr desde la posición xi,yi hasta xf, yf.
    xi y xf son posición vertical de arriba hacia abajo indexado desde 0
    yi e yf son posición horizontal de izquierda a derecha indexado desde 0
    :param arr: numpy.array
    :param xi: int Posición vertical inicial
    :param xf: int Posición vertical final
    :param yi: int Posición horizontal inicial
    :param yf: int Posición horizontal final
    :return: numpy.array
    """
    if type(arr) != np.ndarray:
        send_msg("Se esperaba array de numpy, se recibió " + str(type(arr)), filename)
        return None
    return arr[yi:yf+1, xi:xf+1]


def send_msg(mensaje, filename):
    """Envia el mensaje de error al archivo filename.txt
    :param mensaje: String de mensaje de error
    :param filename: Ruta del archivo sin extension
    """
    file = open(filename + ".txt", "a")  # todo Cambiar para la salida real
    file.write(mensaje + "\n")
    raise Exception(mensaje)