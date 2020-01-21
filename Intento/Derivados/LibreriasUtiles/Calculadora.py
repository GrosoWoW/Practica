
from UtilesValorizacion import factor_descuento, diferencia_dias_convencion, plazo_anual_convencion
from UtilesDerivados import ultimo_habil_pais
from Util import add_days

def duracion_modificada_bono_tasa_variable(fecha, nemo, convencion, flujos, tasa, tera, cn):
    fecha_emision = flujos[0][1]
    fecha_venc = flujos[len(flujos)-1][1]

    if fecha > ultimo_habil_pais(add_days(fecha_emision, -1), "CL", cn):
        return 0
    elif fecha >= fecha_venc:
        return 0

    flujos_aux = []

    for i in range(len(flujos), 0, -1):
        if ultimo_habil_pais(flujos[i][1], "CL", cn) <= fecha:
            flujos_aux.append(flujos[i])
    return calculadora_general(fecha, nemo+"_Modificado", convencion, flujos, tasa, tera, 0, ["DURMODS"])


def meta_calculadora_CO(fecha, nemo, convencion, flujos, tasa, peticiones, cn):
    return calculadora_general(fecha, nemo, convencion, flujos, tasa, 0, 6, peticiones, cn)


def meta_calculadora_CL(familia, nemo, fecha, flujos, base1, base2, tasa, tera, peticiones, cn):
    if (base1 == -1 and base2 == 365) or familia == "BT":
        convencion = 'ACT365'
    elif base1 == -1 and base2 == 360:
        convencion = 'ACT360'
    elif (base1 == 30 and base2 == 360) or familia == "LH":
        convencion = '30/360'
    if (familia == "BT" and nemo[0:4] == "CERO") or tera == -1000:
        return calculadora_general(fecha, nemo, convencion, flujos, tasa, -1000, -1000, peticiones, cn)
    else:
        return calculadora_general(fecha, nemo, convencion, flujos, tasa, tera, 4, peticiones, cn)


def calculadora_general(fecha, nemo, convencion, flujos, tasa, tera, decimales, peticiones, cn):
    posicion = flujos[0][5]
    dur_mod_suc_xvp = 0
    dur_mac_suc_xvp = 0
    convexidad_xvp = 0
    vp = 0
    saldo_remanente = 0
    durest_xflujo = 0
    flujo_total = 0
    vp_limpio = 0
    interes = 0
    amortizacion = 0
    flujo = 0
    v_par_sucio = 0
    intdev = 0
    saldo_rem = 0

    for i in range(1, len(flujos)):
        plazo = (flujos[i][1] - fecha).days
        if type(tasa) == int or type(tasa) == float:
            if tasa == -1000:
                tir = -1000
            else:
                tir = tasa/100
        else:
            plazo_e = min(len(tasa), max(0, round(plazo)))
            if plazo_e == tasa[plazo_e][0]:
                tir = tasa[plazo_e][1]/100
            else:
                tir = "" # todo

        if flujos[i][1] > fecha and flujos[i-1][1] <= fecha:
            intdev = (flujos[i-1][1]-fecha).days / (flujos[i-1][1]-flujos[i][1]).days
            intdev = flujos[i][3] * min(1, abs(intdev))
            saldo_rem = flujos[i-1][5]

            if tera != -1000:
                v_par_sucio = flujos[i-1][5] / factor_descuento(tera/100, flujos[i-1][1], fecha, convencion, 0)

            else:
                factor_par = (flujos[i-1][3] + flujos[i][4] + flujos[i][5]) / (flujos[i][4] + flujos[i][5])
                v_par_sucio = 1 - diferencia_dias_convencion(convencion, fecha, flujos[i][1]) / diferencia_dias_convencion(convencion, flujos[i-1][1], flujos[i][1])
                v_par_sucio = flujos[i-1][5] * (factor_par**(v_par_sucio))

        if flujos[i][1] > fecha:
            if tir != -1000:
                factor0 = factor_descuento(tir, fecha, flujos[i][1], convencion, 0)
                factor1 = factor_descuento(tir, fecha, flujos[i][1], convencion, 1)
                factor2 = factor_descuento(tir, fecha, flujos[i][1], convencion, 2)

                vp += flujos[i][6] * factor0
                if flujos[i][1] > fecha >= flujos[i-1][1]:
                    vp_limpio += (flujos[i][6] - intdev) * factor0
                else:
                    vp_limpio += flujos[i][6] * factor0

                dur_mod_suc_xvp -= flujos[i][6] * factor1
                dur_mac_suc_xvp += flujos[i][6] * factor0 * plazo_anual_convencion(convencion, fecha, flujos[i][1])
                convexidad_xvp += flujos[i][6] * factor2

            durest_xflujo += flujos[i][6] * (plazo/365)
            flujo_total += flujos[i][6]

        if flujos[i][1] >= fecha:
            saldo_remanente += flujos[i][4]

        if flujos[i][1] == fecha:
            interes = flujos[i][3]
            amortizacion = flujos[i][4]
            flujo = flujos[i][6]

    aux = []

    for peticion in peticiones:
        if peticion == "VPRESS":
            if tir == -1000:
                i = -1000
            elif decimales == -1000:
                i = vp/posicion
            elif tera != -1000 and v_par_sucio != 0:
                i = round(vp/v_par_sucio, decimales) * v_par_sucio/posicion
            else:
                i = round(vp/posicion, decimales)

        elif peticion == "VPRESL":
            if tir == -1000:
                i = -1000
            elif decimales == -1000:
                i = vp_limpio /posicion
            else:
                i = round(vp_limpio/posicion,decimales)

        elif peticion == "DURMODS":
            if tir == -1000 or vp == 0:
                i = -1000

            else:
                nemos_tasa_variable = ['BSANTFLOT','BCAPS-F','BCOLB-H','BLAND-IA','BLAND-IB','BLAND-IC','BSAES-G',
                                       'BARAU-D','BCAPS-A2','BRITA-B1','BRITA-B2','BTRIC-A','BCAPS-A1','BSTDS-AD',
                                       'BSTDS-BD','BMASI-K','BRAB-D0911']

                nemos_tasa_variable_al_dia = ["BSANTFLOT"]

                if nemo in nemos_tasa_variable:
                    if nemo in nemos_tasa_variable_al_dia:
                        i = 0
                    else:
                        i =duracion_modificada_bono_tasa_variable(fecha, nemo, convencion, flujos, tasa, tera, cn)[0]
                else:
                    i = dur_mod_suc_xvp / vp

        elif peticion == "DURMODS_F" or peticion == "DURMACS":
            if tir == -1000 or vp == 0:
                i = -1000
            else:
                i = dur_mod_suc_xvp/vp

        elif peticion == "CVXS":
            if tir == -1000 or vp == 0:
                i = -1000
            else:
                i = convexidad_xvp/vp

        elif peticion == "PXS":
            if tir == -1000 or v_par_sucio == 0:
                i = -1000
            else:
                i = vp/v_par_sucio * 100

        elif peticion == "PXL":
            if tir == -1000 or saldo_rem == 0:
                i = -1000
            else:
                i = vp_limpio/saldo_rem*100

        elif peticion == "VPARS":
            i = v_par_sucio/posicion

        elif peticion == "INTDEV":
            i = intdev /posicion

        elif peticion == "FLUJO":
            i = flujo/posicion

        elif peticion == "INTERES":
            i = interes/posicion

        elif peticion == "AMORT":
            i = amortizacion/posicion

        elif peticion == "DURESTRS":
            if flujo_total == 0:
                i = -1000
            else:
                i = durest_xflujo / flujo_total

        elif peticion == "SALDOREM":
            i = saldo_remanente/posicion
        else:
            i = -1000

        aux.append(i)
    return aux


