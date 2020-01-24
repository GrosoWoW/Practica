import pandas as pd
import numpy as np
from Util import fecha_str, add_days, send_msg, sub_arr
from UtilesDerivados import plazo360_a_plazo, cast_frecuencia, cast_convencion, delta_frecuencia, factor_descuento
from Matematica import interpolacion_escalar, interpolacion_log_escalar
from UtilesDerivados import siguiente_habil_paises


def curva_cero_swapUSD(fecha, hora, frecuencia, convencion, si_desinterpolar, cn):
    frecuencia = cast_frecuencia(frecuencia)
    if frecuencia == "3M":
        arr_swap = curva_swap_USD_3M(fecha, hora, cn)
    elif frecuencia == "6M":
        arr_swap = curva_swap_USD_6M(fecha, hora, cn)

    else:
        # send_msg("ERROR: curva_cero_swapUSD: Frecuencia " + frecuencia + " no soportada")
        return #todo error

    fd = bootstrapping(fecha, arr_swap[1:], "", cn)

    return fd


def curva_swap_USD_6M(fecha, hora, cn):
    nombre_curva = "CurvaSwapUSD3M_V2"
    curva_swap = ("SELECT TOP 1 Curva "
                  "From dbDerivados.dbo.TdCurvasDerivados "
                  "WHERE Fecha <= " + fecha_str(fecha) + " AND Hora = '" + hora + "' AND Tipo = '" + nombre_curva + "' "
                  "Order by Fecha desc ")

    curva_swap = pd.io.sql.read_sql(curva_swap, cn).Curva.iloc[0]
    arr_curva_swap = parsear_curva_swap(curva_swap)

    nombre_curva = "CurvaBasisUSD3M6M"
    curva_basis = ("SELECT TOP 1 Curva "
                  "From dbDerivados.dbo.TdCurvasDerivados "
                  "WHERE Fecha <= " + fecha_str(fecha) + " AND Hora = '" + hora + "' AND Tipo = '" + nombre_curva + "' "
                  "Order by Fecha desc ")

    curva_basis = pd.io.sql.read_sql(curva_basis, cn).Curva.iloc[0]
    arr_curva_basis = parsear_curva_swap(curva_basis)

    for i in arr_curva_swap[1:]:
        if i[5] >= 180:
            i[6] = i[6] + interpolacion_escalar(i[5], arr_curva_basis[1:]) / 100
        i[5] = plazo360_a_plazo(i[5], fecha)

    return arr_curva_swap


def curva_swap_USD_3M(fecha, hora, cn):
    nombre_curva = "CurvaSwapUSD3M_V2"
    curva_swap = ("SELECT TOP 1 Curva "
                  "From dbDerivados.dbo.TdCurvasDerivados "
                  "WHERE Fecha <= " + fecha_str(fecha) + " AND Hora = '"+ hora +"' AND Tipo = '" + nombre_curva + "' "
                  "Order by Fecha desc ")
    curva_swap = pd.io.sql.read_sql(curva_swap, cn).Curva.iloc[0]
    arr_curva = parsear_curva_swap(curva_swap)
    for i in arr_curva[1:]:
        i[5] = plazo360_a_plazo(int(i[5]), fecha)

    arr_curva[0][5] = "Plazo"
    return arr_curva


def parsear_curva_swap(curva):
    res = []
    filas = curva.split('|')

    for fila in filas:
        fila_split = fila.split("#")

        for i in range(len(fila_split)):

            if fila_split[i].isdigit():
                fila_split[i] = int(fila_split[i])
                continue

            try:
                fila_split[i] = float(fila_split[i].replace(",", "."))
            except ValueError:
                pass
        res.append(fila_split)
    return res


def bootstrapping(fecha, arr, info, cn):

    arr_fd = np.zeros((len(arr), 2))


    for i in range(len(arr)):
        pago = int(arr[i][3])
        paises_feriados = arr[i][4].split("-")
        fecha_venc = add_days(fecha, arr[i][5])

        fecha_liq = fecha_liquidacion(fecha_venc, pago, paises_feriados, cn)

        arr_fd[i, 0] = (fecha_liq - fecha).days

        frecuencia = cast_frecuencia(arr[i][0])
        convencion = cast_convencion(arr[i][1])

        if frecuencia == "Cero":
            arr_fd[i, 1] = factor_descuento(arr[i][6]/100, fecha, fecha_liq, convencion, 0)


        else:
            arr_swap = np.zeros((arr[i][2], 3))

            for k in range(arr[i][2]):
                fecha_k = delta_frecuencia(fecha, frecuencia, arr[i][2]-k)
                fecha_k = fecha_liquidacion(fecha_k, pago, paises_feriados, cn)

                fecha_k_siguiente = delta_frecuencia(fecha_venc, frecuencia, -(k+1))
                fecha_k_siguiente = max(fecha_k_siguiente, fecha)
                fecha_k_siguiente = fecha_liquidacion(fecha_k_siguiente, pago, paises_feriados, cn)

                arr_swap[k][0] = (fecha_k - fecha).days
                arr_swap[k][1] = (1/factor_descuento(arr[i][6]/100, fecha_k_siguiente, fecha_k, convencion, 0) - 1) * 100
                if k == 0:
                    arr_swap[k][1] = 100 + arr_swap[k][1]
                if i > 0:
                    if arr_swap[k][0] <= arr_fd[i-1][0]:

                        arr_swap[k][2] = interpolacion_log_escalar(arr_swap[k][0], sub_arr(arr_fd, 0, 0, 1, i - 1))



                    else:
                        arr_swap[k][2] = -1000

                else:
                    arr_swap[k][2] = -1000
            arr_fd[i][1] = factor_descuento_interpolacion_bootstrapping(arr_swap)

    arr_fd = np.append([[0, 1]], arr_fd, axis=0)

    return arr_fd


def factor_descuento_interpolacion_bootstrapping(arr_swap):
    # 'La tabla arrSwap es [plazo (p_k), cupon (c_k), descuento (d_k)], donde plazo va en orden desc
    max_iter = 100
    tol = 0.000001

    arr_swap = np.append(arr_swap, [[0, 0, 1]], axis=0)

    T = len(arr_swap)-1

    for k in range(T, -1, -1):
        if arr_swap[k][2] != -1000 and arr_swap[k][2] != 1:
            j = T-k

    # 'La funcion a la cual encontrar el cero es
    # 'f(x)= \sum_{k<=j} c_k * d_k  +  d_j * \sum_{j<k<=T} c_k * x^{p_k-p_j} - 100
    # 'cuya derivada es
    # 'Df(x)=f'(x) = d_j * \sum_
    # {j < k <= T}(p_k - p_j) * c_k * x ^ {(p_k - p_j) - 1}
    # 'y depues retornar el factor de descuento en T, es decir, d_j * x^{p_T-p_j}

    # 'Hacemos primero busqueda binaria
    x1 = 0.1
    x2 = 1
    for i in range(1,101):
        f1 = f_obj_bootstrapping(arr_swap, j, x1)
        f2 = f_obj_bootstrapping(arr_swap, j, x2)
        fm = f_obj_bootstrapping(arr_swap, j, (x1+x2)/2)


        if abs(fm) < tol:
            return arr_swap[T-j][2] * ((x1 + x2) / 2) ** (arr_swap[0][0] - arr_swap[T-j][0])

        elif f1 * fm < 0:
            x2 = (x1 + x2) / 2
        elif f2 * fm < 0:
            x1 = (x1 + x2) / 2
        elif f2 < 0:
            x2 = x2 * (1.000005 ** i)

    x = (x1 + x2)/2

    for i in range(max_iter):
        f = f_obj_bootstrapping(arr_swap, j, x)
        df = df_obj_bootstrapping(arr_swap, j, x)

        if abs(f) < tol and x > 0:
            return arr_swap[T-j][2] * x ^ (arr_swap[0][0] - arr_swap[T-j][0])
        x = x - f/df

    print("FALLAZO")


def df_obj_bootstrapping(arr_swap, j, x):
    T = len(arr_swap) - 1

    df = 0
    for k in range(T-j+1):
        df = df + arr_swap[T - j][2] * (arr_swap[k][0] - arr_swap[T-j][0]) * arr_swap[k][1] * x ** (arr_swap[k][0] - arr_swap[T-j][0] - 1)

    return df


def f_obj_bootstrapping(arr_swap, j, x):
    T = len(arr_swap) - 1
    f = -100

    for k in range(T-j, T+1):
        f = f + arr_swap[k][1] * arr_swap[k][2]

    for k in range(T-j):
        f = f + arr_swap[T-j][2] * arr_swap[k][1] * x ** (arr_swap[k][0] - arr_swap[T-j][0])

    return f


def fecha_liquidacion(fecha_fin, pago, paises_feriados, cn):
    fecha = siguiente_habil_paises(add_days(fecha_fin, -1), paises_feriados, cn)

    for i in range(pago):
        fecha = siguiente_habil_paises(fecha, paises_feriados, cn)

    return fecha

