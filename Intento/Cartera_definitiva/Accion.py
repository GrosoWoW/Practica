
class Accion(Activo):


    def __init__(self, moneda, historico):

        self.moneda = moneda
        
        self.historico = historico

    
    def get_moneda(self):

        return self.moneda

    def get_historico(self):

        return self.historico

    def set_historico(self):

        pass

    

