import pandas as pd
from pathlib import Path
from Utiles.Calculadora import calcular_retornos

class Acciones():

    def __init__(self, nombre_archivo, moneda, n=100):

        # n es al cantidad de datos que se desean extraer 
        # de la accion (ordenado de menor fecha a mayor fecha)

        # Nombre del archivo excel con la accion
        self.nombre_archivo = nombre_archivo
        
        # Moneda que se esta trabajando la accion
        self.moneda = moneda

        # Se encarga de chequear que el nombre del archivo este bien ingresado
        my_file = Path("C:\\Users\\groso\\Desktop\\Practica\\Intento\\Cartera\\ArchivosExcel\\"+ self.nombre_archivo+".xlsx")
        if not my_file.is_file():

            print("ERROR archivo mal ingresado")
            exit(1)

        # DataFrame con los datos de la accion
        archivo = pd.read_excel('C:\\Users\\groso\\Desktop\\Practica\\Intento\\Cartera\\ArchivosExcel\\'+ self.nombre_archivo+".xlsx")
        
        columnas = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        self.archivo = archivo[columnas][:n]

        # Columna Adj Close de archivo de acciones (representa los historicos)
        self.historicos = self.archivo["Adj Close"]

    def get_archivo(self):

        """
        Retorna el nombre del archivo de la accion

        """

        return self.archivo

    def get_historicos(self):

        """
        Retorna el DataFrame con los historicos de la accion

        """

        return self.historicos

    def get_moneda(self):

        """
        Retorna la moneda en que se esta trabajando la accion

        """
        return self.moneda

accion = Acciones("BSANTANDER.SN", "CLP")
print(accion.get_archivo())
print(accion.get_historicos())
