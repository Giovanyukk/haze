import os
import json
from time import sleep
from datetime import datetime
import requests

import numpy as np
import pandas as pd
import steam.webauth as wa
import steam.guard as guard
from lxml import html

# Se centran los headers de la dataframe
pd.set_option('colheader_justify', 'center')
headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas
# Se crea un diccionario con la estructura de la base de datos
data_structure = {header: [] for header in headers}


class Game:
    '''Datos de un juego'''

    def __init__(self, appid, session=requests, fast_mode=True):
        self.appID = appid
        self.name = ''
        self.price = 0
        self.min_profit = 0
        self.avg_profit = 0
        self.med_profit = 0
        self.card_list = []
        self.last_updated = ''
        self.session = session
        self.update(fast_mode)

    def update(self, fast_mode=True):
        store_URL = 'https://store.steampowered.com/api/appdetails?cc=ar&appids=' + \
            str(self.appID)
        response = self.session.get(store_URL)
        # Si falla la solicitud, reintenta cada 5 segundos
        while(response.status_code != 200):
            os.system('cls')
            print('Error al actualizar el juego. Reintentando en 5 segundos...')
            sleep(5)
            os.system('cls')
            response = self.session.get(store_URL)

        # Si la cantidad de appIDs ingresadas es mayor a 250, se reducen las requests por segundo para evitar error 503
        if(not fast_mode):
            sleep(1)
        game_data = json.loads(response.text)
        # Obtiene el precio de los cromos
        self.card_list = self.get_price_list()
        if(not fast_mode):
            sleep(1)

        # Obtiene el nombre del juego
        self.name = game_data[str(self.appID)]['data']['name']
        # Obtiene la cantidad de los cromos que se dropean del juego
        cards_dropped = 3 if len(
            self.card_list) == 5 else len(self.card_list)//2
        # Calcula la media de los precios de los cromos
        average_price = np.average(self.card_list)
        # Calcula la mediana de los precios de los cromos
        median_price = np.median(self.card_list)

        # Detecta si el juego es gratis o no
        is_free = game_data[str(self.appID)]['data']['is_free']
        if(not is_free):
            # Obtiene el precio del juego en centavos
            self.price = game_data[str(
                self.appID)]['data']['price_overview']['final'] / 100
            # Calcula el retorno mínimo
            self.min_profit = round((
                (self.card_list[0] * cards_dropped * 0.8696 / (self.price)) - 1), 3)
            # Calcula el retorno medio
            self.avg_profit = round((
                (average_price * cards_dropped * 0.8696 / (self.price)) - 1), 3)
            # Calcula el retorno mediano
            self.med_profit = round(((median_price * cards_dropped *
                                      0.8696 / (self.price)) - 1), 3)

        # Se actualiza el campo 'Ultima Actualizacion'
        self.last_updated = datetime.now().strftime('%d/%m/%y %H:%M')

    def get_price_list(self):
        '''Obtener una lista de los precios mínimos de los cromos del juego'''
        # Link a los cromos de un juego.
        cards_URL = 'https://steamcommunity.com/market/search/render/?l=spanish&currency=34&category_753_cardborder%5B%5D=tag_cardborder_0&category_753_item_class%5B%5D=tag_item_class_2&appid=753&norender=1&category_753_Game%5B%5D=tag_app_' + \
            str(self.appID)
        response = self.session.get(cards_URL)
        # Si falla la solicitud, reintenta cada 5 segundos
        while(response.status_code != 200):
            os.system('cls')
            print('Error al actualizar el juego. Reintentando en 5 segundos...')
            sleep(5)
            os.system('cls')
            response = self.session.get(cards_URL)

        cards_data = json.loads(response.text)
        # Si no existen cromos, retorna 0 para evitar un error
        if(cards_data['total_count'] == 0):
            return [0]
        # Obtiene el valor de los cromos, limpia el string para sólo obtener el valor numérico y los ordena de menor a mayor
        cards_prices = np.sort(
            [cards_data['results'][i]['sell_price'] / 100 for i in range(len(cards_data['results']))])
        # Retorna la lista de los cromos en orden ascendente
        return cards_prices


class User:
    '''Crear un objeto usuario donde se almacenan los datos del mismo.
    El inicio de sesion es automático'''

    def __init__(self, username='', password='', dir='user.json'):
        self.username = username
        self.password = password
        self.steamID64 = ''
        self.webAPIKey = ''
        self.session = ''
        self.logged_on = False

        if(os.path.isfile(dir)):
            self.load(dir)
        else:
            self.create(dir)

    def load(self, dir='user.json'):
        try:
            with open(dir, 'r', encoding='utf-8') as usercfg:
                data = json.load(usercfg)
                self.username = data['username']
                self.password = data['password']
                self.login()
        except:
            print(
                'Archivo de configuración inválido. Por favor eliminelo y reinicie el programa\n')

    def create(self, dir='user.json'):
        with open(dir, 'w', encoding='utf-8') as usercfg:
            print('Se creará un archivo de configuracion en el directorio del programa')
            print('Para poder omitir los juegos ya comprados al agregar juegos desde steamdb.info, deberá activar la Steam API Key desde la página web de Steam')
            self.username = input(
                'Ingrese su nombre de usuario: ') if self.username == '' else self.username
            self.password = input(
                'Ingrese su contraseña: ') if self.password == '' else self.password
            self.login()
            data = {'username': self.username,
                    'password': self.password}
            json.dump(data, usercfg)

    def login(self):
        user = wa.WebAuth(self.username)

        if(os.path.isfile('2FA.maFile')):
            with open('2Fa.maFile', 'r') as f:
                data = json.load(f)
            self.session = user.cli_login(
                self.password, twofactor_code=guard.SteamAuthenticator(secrets=data).get_code())
        else:
            self.session = user.cli_login(self.password)

        if user.logged_on:
            self.steamID64 = user.steam_id.as_64
            # https://steamcommunity.com/dev/apikey
            key = html.fromstring(self.session.get(
                'https://steamcommunity.com/dev/apikey').content).xpath('//*[@id="bodyContents_ex"]/p[1]/text()')[0]
            self.webAPIKey = key[5:] if key[0] != 'R' else ''
            self.logged_on = True
        else:
            print('No se ha podido iniciar sesión')
