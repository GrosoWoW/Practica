# -*- coding: utf-8 -*-
from math import exp, log


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

def interpolacion_escalar(x, XY, n=0, m=0, first=True):
    """Indica la abscica en la ordenada x al realizar interpolación lineal con los puntos del arreglo XY

        :param x: float abscica al cual se le busca la ordenada con interpolación
        :param XY: array con puntos x,y en
        :param n: int posicion del punto inicial en el arreglo (se setea automáticamente)
        :param m: int posicion del punto final en el arreglo (se setea automáticamente)
        :param first: bool indica si es la primera vez que se llama a la función, para settear n y m.
        :return: float ordenada obtenida al realizar interpolación logaritmica
        """
    if first:
        n = 0
        m = len(XY) - 1

    x1 = float(XY[n][0])  # Abscisa del punto n del arreglo
    y1 = float(XY[n][1])  # Ordenada del punto n del arreglo
    x2 = float(XY[m][0])  # Abscisa del punto m del arreglo
    y2 = float(XY[m][1])  # Ordenada del punto m del arreglo
    x = float(x)  # Abscisa del punto al cual se le busca la ordenada

    if n == m:
        return y1

    if x1 >= x:
        return y1

    if x2 <= x:
        return y2

    if m - n == 1:
        return (y2-y1)/(x2-x1)*(x-x1)+y1

    j = round((n + m) / 2.0)

    if float(XY[j][0]) >= x:
        return interpolacion_escalar(x, XY, n, j, False)
    else:
        return interpolacion_escalar(x, XY, j, m, False)