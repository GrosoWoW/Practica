import importlib

class holi:
    def __init__(self, uno,dos):
        self.uno = uno
        self.dos = dos

    def cambio_uno(self, uno):
        self.uno = uno

    def cambio_dos(self, dos):
        self.dos = dos

    def print(self):
        print(self.uno, self.dos)

    def holiwi(self, n):
        #module = importlib.import_module(holi)
        function = getattr(holi, 'cambio_' + str(n))
        
        return self.function('c cambio')


a = holi('uno_a', 'dos_a')
b = holi('uno_b', 'dos_b')

x = [a,b]
x[0].print()
a.cambio_uno('mimir')
x[0].print()

a.holiwi(1)
a.print()



