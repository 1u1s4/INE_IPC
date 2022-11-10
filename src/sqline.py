from typing import List
import warnings
warnings.filterwarnings("ignore")
import pyodbc 
import pandas as pd
import numpy as np
from funcionesjo import mes_by_ordinal

class sqlINE:
    def __init__(self, anio: int, mes: int) -> None:
        self.anio = anio
        self.mes = mes
        # datos servidor
        DATABASE = 'IPC2010_RN'
        SERVER = '10.0.3.185'
        USERNAME = 'laalvarado'
        PASSWORD = 'Abc$2022'
        self.__conexion = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server}'
            + f';SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        )
        # nombre de divisiones
        abr_diviciones = {
        'Alimentos Y Bebidas No Alcohólicas': 'Alimentos',
        'Bebidas Alcohólicas Y Tabaco':'Bebidas Alcohólicas',
        'Prendas De Vestir Y Calzado':'Vestuario',
        'Vivienda, Agua, Electricidad, Gas Y Otros Combustibles':'Vivienda',
        'Muebles, Artículos Para El Hogar Y Para La Conservación  Del Hogar':'Muebles',
        'Salud':'Salud',
        'Transporte':'Transporte',
        'Comunicaciones':'Comunicaciones',
        'Recreación Y Cultura':'Recreación',
        'Educación':'Educación',
        'Restaurantes Y Hoteles':'Restaurantes',
        'Bienes Y Servicios Diversos':'Bienes diversos'
        }
        sql_query = pd.read_sql(
            'SELECT DivCod, DivNom FROM IPCM01',
            self.__conexion
        ).to_dict()
        self.NOMBRE_DIV = dict(zip(
            [int(i) for i in sql_query['DivCod'].values()],
            [abr_diviciones[nombre.strip().title()] for nombre in sql_query['DivNom'].values()]
        ))
        # ponderaciones de las divisiones
        self.df_DivPon = pd.read_sql(
            f'SELECT RegCod, DivCod, DivPon FROM IPCP01',
            self.__conexion
        )
        self.df_DivPon['RegCod'] = self.df_DivPon['RegCod'].astype('int64')
        self.df_DivPon['DivCod'] = self.df_DivPon['DivCod'].astype('int64')
        # ponderaciones de los gastos basicos
        self.df_GbaPon = pd.read_sql(
            f'SELECT RegCod, DivCod, GbaCod, GbaPon FROM IPCP05',
            self.__conexion
        )
        self.df_GbaPon['RegCod'] = self.df_GbaPon['RegCod'].astype('int64')
        self.df_GbaPon['DivCod'] = self.df_GbaPon['DivCod'].astype('int64')
        self.df_GbaPon['GbaCod'] = self.df_GbaPon['GbaCod'].astype('int64')
        # informacion gastos basicos
        self.df_GbaInfo = pd.read_sql(
            'SELECT DivCod, AgrCod, GruCod, SubCod, GbaCod, GbaNom FROM IPCM05',
            self.__conexion
        )
        columnas = ('DivCod', 'AgrCod', 'GruCod', 'SubCod', 'GbaCod')
        for columna in columnas:
            self.df_GbaInfo[columna] = self.df_GbaInfo[columna].astype('int64')
        # indices por divicion
        self.df_DivInd = pd.read_sql(
            f'SELECT RegCod, PerAno, PerMes, DivCod, DivInd FROM IPCPH1 WHERE PerAno>={self.anio - 2} AND PerSem=3',
            self.__conexion
        )
        self.df_DivInd['RegCod'] = self.df_DivInd['RegCod'].astype('int64')
        self.df_DivInd['DivCod'] = self.df_DivInd['DivCod'].astype('int64')
        # indices por gasto basico
        self.df_GbaInd = pd.read_sql(
            f'SELECT RegCod, PerAno, PerMes, PerSem, DivCod, AgrCod, GruCod, SubCod, GbaCod, GbaInd FROM IPCPH5 WHERE PerAno>={self.anio - 2}',
            self.__conexion
        )
        columnas = ('RegCod', 'PerAno', 'PerMes', 'PerSem', 'DivCod', 'AgrCod', 'GruCod', 'SubCod', 'GbaCod')
        for columna in columnas:
            self.df_GbaInd[columna] = self.df_GbaInd[columna].astype('int64')
        # fuentes
        conexion_auxiliar = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server}'
            + f';SERVER=INEVSQL01\A;DATABASE=master;UID=lmdelgado;PWD=Del/*2022'
        )
        for rg in range(1, 9):
            df_Fnt = pd.read_sql(
                f"""SELECT a.RegCod, a.PerAno, a.PerMes, b.TfnCod,b.BolNart 
                    FROM IPC2010_0{rg}_RN.dbo.IPC104 a 
                    INNER JOIN (SELECT a.FntCod, a.FntNom, a.TfnCod, b.BolNum, b.RegCod, b.BolNart
                    FROM IPC2010_0{rg}_RN.dbo.IPC010 a 
                    INNER JOIN IPC2010_0{rg}_RN.dbo.IPC103 b 
                    ON (a.FntCod = b.FntCod AND a.DepCod = b.DepCod AND a.MunCod =b.MunCod) 
                    WHERE b.PerAno >= {self.anio - 1}) b 
                    ON a.BolNum = b.BolNum 
                    INNER JOIN IPC2010_0{rg}_RN.dbo.IPC007 c ON 
                    a.ArtCod = c.ArtCod
                    INNER JOIN IPC2010_0{rg}_RN.dbo.IPC008 d ON
                    b.TfnCod = d.TfnCod
                    WHERE PerAno >= {self.anio - 1} AND b.TfnCod != '  '""",
                conexion_auxiliar
            )
            if rg == 1:
                self.df_Fnt = df_Fnt
            else:
                self.df_Fnt = pd.merge(self.df_Fnt, df_Fnt, how='outer')
        columnas = ('RegCod','TfnCod')
        for columna in columnas:
            self.df_Fnt[columna] = self.df_Fnt[columna].astype('int64')
        # diccionario tipo de fuentes
        self.nombre_fuentes = {
            0: 'Sin tipo',#SIN TIPO DE FUENTE ASIGNADO
            1: 'Carnicerias',#CARNICERIAS, MARRANERIAS, POLLERIAS, ETC.
            2: 'Supermercados',#SUPERMERCADOS, DESPENSAS Y ALMACENES EN CADENA
            3: 'Hipermercados',#HIPERMERCADOS
            4: 'Depositos',#DEPOSITOS Y ABARROTERIAS
            5: 'Tiendas no Especializadas',#TIENDAS NO ESPECIALIZADAS (INCLUYE MISCELANEAS Y TIENDAS DE
            6: 'Almacenes',#ALMACENES O TIENDAS ESPECIALIZADAS
            7: 'Restaurantes',#RESTAURANTES  O EXPENDIOS DE COMIDAS PREPARADAS EN CADENA
            8: 'Empresas',#EMPRESAS ESPECIALIZADAS EN PRESTACION DE SERVICIOS
            9: 'Expendios de Gas',#EXPENDIOS DE GAS PROPANO
            10: 'Farmacias',#FARMACIAS, DROGUERIAS Y PERFUMERIAS
            11: 'Centros de Salud',#HOSPITALES, CLINICAS, CENTROS Y PUESTOS DE SALUD, LABORATORI
            12: 'Hoteles',#HOTELES, MOTELES, HOSPEDAJES, PENSIONES Y ALOJAMIENTOS
            13: 'Centros Educativos',#COLEGIOS, ACADEMIAS,  INSTITUTOS, UNIVERSIDADES Y OTROS
            14: 'Otros Establecimientos Especializados',#OTROS ESTABLECIMIENTOS ESPECIALIZADOS EN PREPARACION DE SERV
            15: 'Servicio Domeestico',#SERVICIO DOMESTICO
            16: 'Otros Establecimientos No Especializados',#OTROS ESTABLECIMIENTOS NO ESPECIALIZADOS EN OTRO CODIGO
            20: 'Cuarto de Alquiler',#VIVIENDA TIPO CUARTO DE ALQUILER
            21: 'Apartamento de Alquiler',#VIVIENDA TIPO APARTAMENTO DE ALQUILER
            22: 'Casa de Alquiler',#VIVIENDA TIPO CASA DE ALQUILER
            23: 'Mercados',#MERCADOS CANTONALES Y MUNICIPALES ( COMPRA DE ALIMENTOS )
        }

    def get_nombre_Gba(self, GbaCod: int) -> str:
        nombre = self.df_GbaInfo[self.df_GbaInfo['GbaCod'] == GbaCod]['GbaNom'].iloc[0]
        return nombre.strip().title()

    def calcular_IPC(self, anio: int, mes: int, RegCod: int) -> float:
        PONDERACIONES_REG = self.df_DivPon[self.df_DivPon['RegCod'] == RegCod]['DivPon']
        Qanio = self.df_DivInd['PerAno'] == anio
        Qmes = self.df_DivInd['PerMes'] == mes
        Qreg = self.df_DivInd['RegCod'] == RegCod
        indices = self.df_DivInd[Qanio & Qmes & Qreg]['DivInd']
        return np.average(a=indices, weights=PONDERACIONES_REG)

    def inflacion_mensual(self, anio: int, mes: int, RegCod: int) -> float:
        actual = self.calcular_IPC(anio, mes, RegCod)
        if mes == 1:
            anterior = self.calcular_IPC(anio - 1, 12, RegCod)
        else:
            anterior = self.calcular_IPC(anio, mes - 1, RegCod)
        return 100*(actual/anterior - 1)

    def inflacion_interanual(self, anio: int, mes: int, RegCod: int) -> float:
        actual = self.calcular_IPC(anio, mes, RegCod)
        anterior = self.calcular_IPC(anio - 1, mes, RegCod)
        return 100*(actual/anterior - 1)
    
    def inflacion_acumulada(self, anio: int, mes: int, RegCod: int) -> float:
        actual = self.calcular_IPC(anio, mes, RegCod)
        anterior = self.calcular_IPC(anio - 1, 12, RegCod)
        return 100*(actual/anterior - 1)
    
    def poder_adquisitivo(self, anio: int, mes: int, RegCod: int) -> float:
        return (1 / self.calcular_IPC(anio, mes, RegCod)) * 100

    def incidencia_divisiones(self, RegCod: int) -> List[float]:
        incidencias = []
        for DivCod in range(1, 13):
            ponderacion = self.df_DivPon[(self.df_DivPon['RegCod'] == RegCod) & (self.df_DivPon['DivCod'] == DivCod)]['DivPon'].iloc[0]
            Qanio = self.df_DivInd['PerAno'] == self.anio
            Qmes = self.df_DivInd['PerMes'] == self.mes
            Qreg = self.df_DivInd['RegCod'] == RegCod
            Qdiv = self.df_DivInd['DivCod'] == DivCod
            indice_actual = self.df_DivInd[Qanio & Qmes & Qreg & Qdiv]['DivInd'].iloc[0]
            if self.mes == 1:
                Qanio = self.df_DivInd['PerAno'] == self.anio - 1
                Qmes = self.df_DivInd['PerMes'] == 12
                ipc_anterior = self.calcular_IPC(self.anio - 1, 12, RegCod)
            else:
                Qmes = self.df_DivInd['PerMes'] == self.mes - 1
                ipc_anterior = self.calcular_IPC(self.anio, self.mes - 1, RegCod)
            indice_anterior = self.df_DivInd[Qanio & Qmes & Qreg & Qdiv]['DivInd'].iloc[0]
            variacion = ((indice_actual - indice_anterior) / ipc_anterior) * ponderacion
            incidencias.append((variacion, self.NOMBRE_DIV[DivCod]))
        return incidencias

    def incidencia_gasto_basico(self, RegCod: int):
        incidencias = []
        for GbaCod in self.df_GbaInfo['GbaCod'].to_list():
            ponderacion = self.df_GbaPon[(self.df_GbaPon['RegCod'] == RegCod) & (self.df_GbaPon['GbaCod'] == GbaCod)]['GbaPon'].iloc[0]
            Qanio = self.df_GbaInd['PerAno'] == self.anio
            Qmes = self.df_GbaInd['PerMes'] == self.mes
            Qreg = self.df_GbaInd['RegCod'] == RegCod
            Qgba = self.df_GbaInd['GbaCod'] == GbaCod
            indice_actual = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba]['GbaInd'].iloc[0]
            if self.mes == 1:
                Qanio = self.df_GbaInd['PerAno'] == self.anio - 1
                Qmes = self.df_GbaInd['PerMes'] == 12
                ipc_anterior = self.calcular_IPC(self.anio - 1, 12, RegCod)
            else:
                Qmes = self.df_GbaInd['PerMes'] == self.mes - 1
                ipc_anterior = self.calcular_IPC(self.anio, self.mes - 1, RegCod)
            indice_anterior = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba]['GbaInd'].iloc[0]
            variacion = ((indice_actual - indice_anterior) / ipc_anterior) * ponderacion
            nombre_gba = self.get_nombre_Gba(GbaCod)
            incidencias.append((variacion, nombre_gba))
        return incidencias

    def series_historicas_Gbas(self, RegCod: int):
        series = []
        for GbaCod in self.df_GbaInfo['GbaCod'].to_list():
            if self.mes != 12:
                Qanio = self.df_GbaInd['PerAno'] == self.anio
                Qmes = self.df_GbaInd['PerMes'] <= self.mes
                Qreg = self.df_GbaInd['RegCod'] == RegCod
                Qgba = self.df_GbaInd['GbaCod'] == GbaCod
                Qsem = self.df_GbaInd['PerSem'] == 3
                indices1 = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba & Qsem][['PerAno','PerMes','GbaInd']]
                Qanio = self.df_GbaInd['PerAno'] == self.anio - 1
                Qmes = self.df_GbaInd['PerMes'] >= self.mes
                indices2 = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba & Qsem][['PerAno','PerMes','GbaInd']]
                indices = pd.merge(indices2, indices1, how='outer')
            else:
                Qanio = self.df_GbaInd['PerAno'] == self.anio
                Qmes = self.df_GbaInd['PerMes'] <= self.mes
                Qreg = self.df_GbaInd['RegCod'] == RegCod
                Qgba = self.df_GbaInd['GbaCod'] == GbaCod
                Qsem = self.df_GbaInd['PerSem'] == 3
                indices = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba & Qsem][['PerAno','PerMes','GbaInd']]
            nombre_gba = self.get_nombre_Gba(GbaCod)
            indices_final = []
            if len(indices) != 0:
                for i in range(len(indices)):
                    mes_abr = mes_by_ordinal(indices['PerMes'].iat[i])
                    anio = indices['PerAno'].iat[i]
                    fecha = f'{mes_abr}-{anio}'
                    indice = indices['GbaInd'].iat[i]
                    indices_final.append((fecha, indice))
                series.append((nombre_gba, indices_final))
        return series

    def serie_historica_ipc_pdr_adq(self, RegCod: int, Qpdr_adq: bool=False):
        serie = []
        if Qpdr_adq:
            funcion = self.poder_adquisitivo
        else:
            funcion = self.calcular_IPC
        if self.mes != 12:
            for i in range(self.mes, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio - 1}'
                ipc = funcion(self.anio - 1, i, RegCod)
                serie.append((fecha, ipc))
            for i in range(1, self.mes + 1):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                ipc = funcion(self.anio, i, RegCod)
                serie.append((fecha, ipc))
        else:
            for i in range(1, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                ipc = funcion(self.anio, i, RegCod)
                serie.append((fecha, ipc))
        return serie

    def serie_historica_inflacion(self, RegCod: int, tipo: str):
        serie = []
        if tipo == 'intermensual':
            funcion = self.inflacion_mensual
        elif tipo == 'interanual':
            funcion = self.inflacion_interanual
        elif tipo == 'acumulada':
            funcion = self.inflacion_acumulada
        if self.mes != 12:
            for i in range(self.mes, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio - 1}'
                indice = funcion(self.anio - 1, i, RegCod)
                serie.append((fecha, indice))
            for i in range(1, self.mes + 1):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                indice = funcion(self.anio, i, RegCod)
                serie.append((fecha, indice))
        else:
            for i in range(1, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                indice = funcion(self.anio, i, RegCod)
                serie.append((fecha, indice))
        return serie

    def serie_cobertura_fuentes(self):
        serie = []
        if self.mes != 12:
            for i in range(self.mes, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio - 1}'
                mes_ = self.df_Fnt['PerMes'] == i
                anio_ = self.df_Fnt['PerAno'] == self.anio - 1
                conteo = self.df_Fnt[anio_ & mes_].shape[0]
                serie.append((fecha, conteo))
            for i in range(1, self.mes + 1):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                mes_ = self.df_Fnt['PerMes'] == i
                anio_ = self.df_Fnt['PerAno'] == self.anio
                conteo = self.df_Fnt[anio_ & mes_].shape[0]
                serie.append((fecha, conteo))
        else:
            for i in range(1, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                mes_ = self.df_Fnt['PerMes'] == i
                anio_ = self.df_Fnt['PerAno'] == self.anio
                conteo = self.df_Fnt[anio_ & mes_].shape[0]
                serie.append((fecha, conteo))
        return serie

    def desagregacion_fuentes(self):
        serie = []
        mes_ = self.df_Fnt['PerMes'] == self.mes
        anio_ = self.df_Fnt['PerAno'] == self.anio
        S = 0
        for i in range(24):
            if i in (17,18,19): # no existen estos tipos de fuentes
                continue
            tipo_fuente_ = self.df_Fnt['TfnCod'] == i
            conteo = self.df_Fnt[anio_ & mes_ & tipo_fuente_].shape[0]
            S += conteo
            nmbr_Fnt = self.nombre_fuentes.get(i)
            serie.append((nmbr_Fnt, conteo))
        invertir = [(i[1] / S * 100, i[0]) for i in serie]
        serie = [i[::-1] for i in sorted(invertir, reverse=True)]
        return serie
    
    def cobertura_fuentes(self):
        cobertura = []
        mes_ = self.df_Fnt['PerMes'] == self.mes
        anio_ = self.df_Fnt['PerAno'] == self.anio
        for i in range(1, 9):
            RegCod_ = self.df_Fnt['RegCod'] == i
            conteo = self.df_Fnt[anio_ & mes_ & RegCod_].shape[0]
            cobertura.append((i, conteo))
        return cobertura

p = sqlINE(2022, 10)
for i in p.desagregacion_fuentes():
    print(i)