def conversionSYP(riesgo):
    '''
    Funcion que con un diccionario lleva el riesgo de un bono de int al string de la convencion.
    :param riesgo: Int que representa el riesgo de un bono en la base de datos.
    :return: Riesgo en la otra convencion.
    '''
    return {-1: 'AAA', 1: 'AAA',2: 'AA',3: 'AA',4: 'AA',5: 'A',6: 'A',7: 'A',8: 'BBB',9: 'BBB',10: 'BBB',\
            11: 'BB+',12: 'BB',13: 'BB-',14: 'B+',15: 'B',16: 'B-',17: 'CCC',18: 'CC+',19: 'CC',20: 'C+',\
            21: 'C',22: 'C-',23: 'D',24: 'E'}.get(riesgo)