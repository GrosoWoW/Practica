
class Derivado(Activo):

    def __init__(self, derivado_generico):

        self.derivado_generico = derivado_generico
        self.derivado_generico.genera_flujos()
        self.valoriza_flujos()

    def get_derivado_generico(self):

        return self.derivado_generico

    def get_flujos(self):

        return self.get_derivado_generico().get_flujos_valorizados()


    def set_historico(self):

        n = 200
        moneda = self.get_monedaActivo()
        curvas = seleccionar_curva_derivados(moneda, n)[::-1]

        largo = len(self.get_plazos())
        cantidad_curvas = len(curvas["Curva"])

        matriz = np.zeros(largo, cantidad_curvas)

        for i in range(largo):

            for j in range(cantidad_curvas):

                valor_dia = pivotes[i]
                curva = curvas["Curva"][j]
                fecha_curva = curvas["Fecha"][j]
                curva_parseada = parsear_curva(curva, fecha_curva)
                matriz[i][j] = interpolacion_log_escalar(valor_dia, curva_parseada)
                
        self.historicos = pd.DataFrame(matriz)


