import os
import json
import sys
from time import sleep
from datetime import datetime
import requests
import curses

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


def print_center(stdscr, text: str):
    '''Imprimir un texto centrado en la pantalla'''

    stdscr.clear()
    if len(text.split('\n')) > 1:
        for idx, line in enumerate(text.split('\n')):
            stdscr.addstr(stdscr.getmaxyx()[
                          0]//2 - len(text.split('\n')) + idx, stdscr.getmaxyx()[1]//2 - len(line)//2, line)
    else:
        stdscr.addstr(stdscr.getmaxyx()[
                      0]//2, stdscr.getmaxyx()[1]//2 - len(text)//2, text)
    stdscr.refresh()


class Game:
    '''Contiene la informacion de un juego

    Parametros
    ----------
    appid : int
        AppID del juego
    session : requests.Session
        Objeto request.session por el cual se realizan las requests. Normalmente se utiliza la propiedad User.session
    fast_mode : bool
        Determina si se evitan las pausas entre requests

    Atributos
    ---------
    appID : int
        AppID del juego
    name : str
        Nombre del juego
    price : float
        Precio
    min_profit : float
        Retorno minimo
    avg_profit : float
        Retorno medio
    med_profit : float
        Retorno mediano
    card_list : list[float]
        Lista de precios de los cromos
    last_updated : datetime.datetime
        Fecha y hora de ultima actualización
    session : request.Session
        Sesión del usuario
    stdscr : curses.window
        Pantalla principal del programa
    '''

    def __init__(self, appid: int, session: requests.Session = requests.Session, fast_mode: bool = True, stdscr: curses.window = None):
        self.appID = appid
        self.name = ''
        self.price = 0
        self.min_profit = 0
        self.avg_profit = 0
        self.med_profit = 0
        self.card_list = []
        self.last_updated = ''
        self.session = session
        self.stdscr = stdscr
        self.update(fast_mode)

    def update(self, fast_mode=True):
        store_URL = 'https://store.steampowered.com/api/appdetails?cc=ar&appids=' + \
            str(self.appID)
        response = self.session.get(store_URL)
        # Si falla la solicitud, reintenta cada 5 segundos
        while(response.status_code != 200):
            if self.stdscr != None:
                for i in range(5, 0, -1):
                    print_center(
                        self.stdscr, f'Error al actualizar el juego. Reintentando en {i} segundos...')
                    sleep(1)
            else:
                os.system('cls')
                for i in range(5, 0, -1):
                    print(
                        f'Error al actualizar el juego. Reintentando en {i} segundos...')
                    sleep(1)
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
            if self.stdscr != None:
                for i in range(5, 0, -1):
                    print_center(
                        self.stdscr, f'Error al actualizar el juego. Reintentando en {i} segundos...')
                    sleep(1)
            else:
                os.system('cls')
                for i in range(5, 0, -1):
                    print(
                        f'Error al actualizar el juego. Reintentando en {i} segundos...')
                    sleep(1)
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
    El inicio de sesion es automático

    Parametros
    ----------
    username : str
        Nombre de usuario
    password : str
        Contraseña
    dir : str
        Ruta del archivo de configuracion

    Atributos
    ---------
    username : str
        Nombre de usuario
    password : str
        Contraseña
    steamID64 : str
        SteamID64 del usuario de Steam
    webAPIKey : str
        Clave de web API del usuario de Steam
    session : request.Session
        Sesión del usuario
    logged_on : bool
        Indica si la sesion del usuario esta iniciada
    stdscr: curses.window
        Pantalla principal del programa
    email_code : str
        Codigo de verificacion de email
    twofactor_code : str
        Codigo de verificacion de 2FA
    '''

    def __init__(self, username: str = '', password: str = '', dir: str = 'user.json', stdscr: curses.window = None, session: requests.Session = None):
        self.username = username
        self.password = password
        self.steamID64 = ''
        self.webAPIKey = ''
        self.session = ''
        self.logged_on = False
        self.stdscr = stdscr
        self.email_code = ''
        self.twofactor_code = ''

        if session != None:
            if 'login' not in session.get('https://steamcommunity.com/dev/apikey').url.split('/'):
                self.session = session
                self.logged_on = True
                self.steamID64 = html.fromstring(self.session.get('https://store.steampowered.com/account/').content).xpath(
                    '//*[@id="responsive_page_template_content"]/div[1]/div/div[2]')[0].text.split(' ')[3]
                # https://steamcommunity.com/dev/apikey
                # //*[@id="responsive_page_template_content"]/div[1]/div/div[2]
                key = html.fromstring(self.session.get(
                    'https://steamcommunity.com/dev/apikey').content).xpath('//*[@id="bodyContents_ex"]/p[1]/text()')[0]
                self.webAPIKey = key.split(' ')[1] if key[0] != 'R' else ''
                return

        if(os.path.isfile(dir)):
            if not self.load(dir):
                os.remove('user.json')
                self.create(dir)
        else:
            self.create(dir)

    def load(self, dir='user.json'):
        try:
            with open(dir, 'r', encoding='utf-8') as usercfg:
                data = json.load(usercfg)
                self.username = data['username']
                self.password = data['password']
                if self.username == '' or self.password == '':
                    raise Exception()
                self.login()
            return True
        except:
            if self.stdscr != None:
                print_center(
                    self.stdscr, 'Archivo de configuración inválido.\nSe autoeliminará y se intentará crear uno nuevo.')
                sleep(2)
            else:
                print(
                    'Archivo de configuración inválido.\nSe autoeliminará y se intentará crear uno nuevo.')
                sleep(2)
            return False

    def create(self, dir='user.json'):
        with open(dir, 'w', encoding='utf-8') as usercfg:
            if self.stdscr != None:
                print_center(self.stdscr, 'Se creará un archivo de configuracion en el directorio del programa.\nPara poder omitir los juegos que ya están en su biblioteca,\ndeberá activar la Steam API Key desde la página web de Steam')
            else:
                print('Se creará un archivo de configuracion en el directorio del programa.\nPara poder omitir los juegos que ya están en su biblioteca,\ndeberá activar la Steam API Key desde la página web de Steam')
            if self.username == '' or self.password == '':
                self.stdscr.addstr(self.stdscr.getmaxyx()[
                                   0]//2 + 3, self.stdscr.getmaxyx()[1]//2 - 35, 'Ingrese su nombre de usuario: ')
                self.stdscr.addstr(self.stdscr.getmaxyx()[
                                   0]//2 + 4, self.stdscr.getmaxyx()[1]//2 - 28, 'Ingrese su contraseña: ')
                curses.echo()
                curses.nocbreak()
                curses.curs_set(1)
                self.stdscr.refresh()
                self.username = self.stdscr.getstr(
                    self.stdscr.getmaxyx()[0]//2 + 3, self.stdscr.getmaxyx()[1]//2 - 5).decode(encoding="utf-8")
                self.password = self.stdscr.getstr(
                    self.stdscr.getmaxyx()[0]//2 + 4, self.stdscr.getmaxyx()[1]//2 - 5).decode(encoding="utf-8")
                curses.noecho()
                curses.cbreak()
                curses.curs_set(0)

            self.login()
            data = {'username': self.username,
                    'password': self.password,
                    'asf_path': ''}
            json.dump(data, usercfg)

    def login(self):
        user = wa.WebAuth(self.username)
        while user.logged_on == False:
            try:
                user = wa.WebAuth(self.username)
                if(os.path.isfile('2FA.maFile')):
                    with open('2FA.maFile', 'r') as f:
                        data = json.load(f)
                    self.session = user.login(
                        self.password, twofactor_code=guard.SteamAuthenticator(secrets=data).get_code())
                else:
                    self.session = user.login(
                        self.password, email_code=self.email_code, twofactor_code=self.twofactor_code)
            except wa.TwoFactorCodeRequired:
                self.stdscr.addstr(self.stdscr.getmaxyx()[
                    0]//2 + 5, self.stdscr.getmaxyx()[1]//2 - 28, 'Ingrese el código 2FA: ' + ' ' * len(self.twofactor_code))
                self.stdscr.refresh()
                curses.echo()
                curses.nocbreak()
                curses.curs_set(1)
                self.email_code = ''
                self.twofactor_code = self.stdscr.getstr(self.stdscr.getmaxyx()[
                    0]//2 + 5, self.stdscr.getmaxyx()[1]//2 - 5).decode(encoding="utf-8").strip()
                curses.noecho()
                curses.cbreak()
                curses.curs_set(0)
            except wa.EmailCodeRequired:
                self.stdscr.addstr(self.stdscr.getmaxyx()[
                    0]//2 + 5, self.stdscr.getmaxyx()[1]//2 - 28, 'Ingrese el código 2FA: ' + ' ' * len(self.email_code))
                self.stdscr.refresh()
                curses.echo()
                curses.nocbreak()
                curses.curs_set(1)
                self.twofactor_code = ''
                self.email_code = self.stdscr.getstr(self.stdscr.getmaxyx()[
                    0]//2 + 5, self.stdscr.getmaxyx()[1]//2 - 5).decode(encoding="utf-8").strip()
                curses.noecho()
                curses.cbreak()
                curses.curs_set(0)
            except wa.LoginIncorrect:
                self.stdscr.addstr(self.stdscr.getmaxyx()[
                    0]//2 + 3, self.stdscr.getmaxyx()[1]//2 - 5, ' ' * len(self.username))
                self.stdscr.addstr(self.stdscr.getmaxyx()[
                    0]//2 + 4, self.stdscr.getmaxyx()[1]//2 - 5, ' ' * len(self.password))
                curses.echo()
                curses.nocbreak()
                curses.curs_set(1)
                self.stdscr.refresh()
                self.username = self.stdscr.getstr(
                    self.stdscr.getmaxyx()[0]//2 + 3, self.stdscr.getmaxyx()[1]//2 - 5).decode(encoding="utf-8")
                self.password = self.stdscr.getstr(
                    self.stdscr.getmaxyx()[0]//2 + 4, self.stdscr.getmaxyx()[1]//2 - 5).decode(encoding="utf-8")
                curses.noecho()
                curses.cbreak()
                curses.curs_set(0)
            except wa.TooManyLoginFailures:
                print_center(
                    self.stdscr, 'Demasiados intentos fallidos.\nPor favor, intente más tarde.')
                sleep(5)
                curses.nocbreak()
                self.stdscr.keypad(False)
                curses.echo()
                curses.endwin()
                sys.exit()

        if user.logged_on:
            self.steamID64 = user.steam_id.as_64
            # https://steamcommunity.com/dev/apikey
            key = html.fromstring(self.session.get(
                'https://steamcommunity.com/dev/apikey').content).xpath('//*[@id="bodyContents_ex"]/p[1]/text()')[0]
            self.webAPIKey = key[5:] if key[0] != 'R' else ''
            self.logged_on = True
        else:
            if self.stdscr != None:
                print_center(self.stdscr, 'No se ha podido iniciar sesión')
            else:
                print(
                    'No se ha podido iniciar sesión')
