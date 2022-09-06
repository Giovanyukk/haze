# Standard library imports
import os
import subprocess
import sys
import logging
import json
import threading as thr
import ctypes
import curses
import requests

# Third party imports
import pandas as pd

# Local application imports
from functions import to_dataframe, save_database, delete_database, get_appid_list, create_menu, print_center, save_cookies, load_cookies, initscr
from classes import User
from ASF import idle_bot, cmd, wait_for_threads

VERSION = '0.12.0'

# Titulo de la ventana
if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW(f'Haze v{VERSION}')
elif os.name == 'posix':
    print(f'\33]0;Haze v{VERSION}\a', end='', flush=True)

stdscr = initscr()

# Se inicializa el logger para el manejo de errores
logging.basicConfig(filename='log.txt', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

# Si no existe la carpeta database, se crea
if(not os.path.exists('database')):
    os.makedirs('database')

# Se intenta cargar la sesión de usuario desde el archivo de sesión session.pkl
# Si no existe el archivo o la sesión expiró, se crea un objeto usuario
try:
    session = requests.session()
    session.cookies = load_cookies('session.pkl')
    user = User(session=session, stdscr=stdscr)
    save_cookies(user.session.cookies, 'session.pkl')
except:
    user = User(stdscr=stdscr)
    save_cookies(user.session.cookies, 'session.pkl')

# Se centran los headers de la dataframe
pd.set_option('colheader_justify', 'center')
headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas
# Se crea un diccionario con la estructura de la base de datos
data_structure = {header: [] for header in headers}

# Se verifica si existe una base de datos en formato .csv
if (os.path.isfile('database/main.csv')):
    # Si existe, se carga el .csv como un dataframe
    database = pd.read_csv('database/main.csv')
else:
    # Si no existe, se crea una dataframe temporal
    database = pd.DataFrame.from_dict(data_structure)

logo = '''      ___           ___           ___           ___      
     /\__\         /\  \         /\  \         /\  \     
    /:/  /        /::\  \        \:\  \       /::\  \    
   /:/__/        /:/\:\  \        \:\  \     /:/\:\  \   
  /::\  \ ___   /::\~\:\  \        \:\  \   /::\~\:\  \  
 /:/\:\  /\__\ /:/\:\ \:\__\ _______\:\__\ /:/\:\ \:\__\ 
 \/__\:\/:/  / \/__\:\/:/  / \::::::::/__/ \:\~\:\ \/__/ 
      \::/  /       \::/  /   \:\~~\~~      \:\ \:\__\   
      /:/  /        /:/  /     \:\  \        \:\ \/__/   
     /:/  /        /:/  /       \:\__\        \:\__\     
     \/__/         \/__/         \/__/         \/__/     
'''

# Entradas del menu principal
menu = ['Actualizar desde Steam', 'Actualizar base de datos local',
        'ArchiSteamFarm', 'Salir']

with open('./user.json', 'r') as f:
    try:
        asf_path = json.load(f)['asf_path']
    except:
        stdscr.addstr(
            'No se ha definido la ruta del ejecutable de ArchiSteamFarm. Puede definirla editando el archivo user.json')
        stdscr.refresh()
        asf_path = None

try:
    while True:
        # Se imprime el menu principal
        option = create_menu(stdscr, menu, 0, logo)

        if(option == 0):
            # Actualizar desde Steam
            print_center(stdscr, 'Borrando base de datos...')
            delete_database()
            database = pd.DataFrame.from_dict(data_structure)
            print_center(stdscr, 'Obteniendo lista de juegos...')
            appid_list = get_appid_list()
            # Da la opcion de omitir los juegos que ya estan comprados
            if(user.webAPIKey != ''):
                if create_menu(stdscr, ['Si', 'No'], title='Omitir juegos que ya estan en la biblioteca?') == 1:
                    break
                stdscr.clear()
                stdscr.refresh()
                owned_games_URL = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + \
                    user.webAPIKey + '&steamid=' + \
                    str(user.steamID64) + '&format=json'
                games_data = user.session.get(
                    owned_games_URL).json()['response']
                owned_games_list = [int(games_data['games'][x]['appid']) for x in range(
                    len(games_data['games']))]
                appid_list = [x for x in appid_list if int(
                    x) not in owned_games_list]
                database = pd.concat([database, to_dataframe(
                    appid_list, user.session, stdscr)], ignore_index=True)
                save_database(database)
            else:
                database = pd.concat([database, to_dataframe(
                    appid_list, user.session, stdscr)], ignore_index=True)
                save_database(database)
            print_center(
                stdscr, 'Base de datos actualizada.\nPresione cualquier tecla para continuar...')
            stdscr.getch()
        elif(option == 1):
            if(database['AppID'].tolist() != [] and os.path.isfile('database/main.csv')):
                database = pd.concat([database, to_dataframe(
                    database['AppID'].tolist(), user.session, stdscr)], ignore_index=True)
                save_database(database)
                print_center(
                    stdscr, 'Base de datos actualizada.\nPresione cualquier tecla para continuar...')
                stdscr.getch()
            else:
                stdscr.clear()
                print_center(
                    stdscr, 'La base de datos no existe o está vacia.\nPresione cualquier tecla para continuar...')
                stdscr.getch()
        elif(option == 2):
            curses.nocbreak()
            stdscr.keypad(False)
            curses.curs_set(1)
            curses.echo()
            curses.endwin()

            os.system('cls' if os.name == 'nt' else 'clear')

            bots = []
            while(len(bots) == 0):
                bots = [i.strip() for i in input(
                    'Ingrese los nombres de los bots separados por comas: ').split(',')]
            thread = thr.Thread(target=idle_bot, args=(
                bots[0], True), daemon=True, name=f'{bots[0]}Thread')
            thread.start()
            threads = [thread]
            for bot in bots[1:]:
                thread = thr.Thread(target=idle_bot, args=(
                    bot,), daemon=True, name=f'{bot}Thread')
                thread.start()
                threads += [thread]
            if(asf_path != None and os.path.exists(asf_path)):
                print('Iniciando ASF')

                def subprocess_no_stdout(path): return subprocess.Popen(
                    path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ASF_thread = thr.Thread(
                    target=subprocess_no_stdout, args=(asf_path,), daemon=True, name='ASFThread')
                ASF_thread.start()
                threads += [ASF_thread]
            else:
                print(
                    'No se encontró el ejecutable de ASF. Se activará solo el fast-mode')
            thread_manager = thr.Thread(
                target=wait_for_threads, args=(threads,), daemon=True, name='ThreadManager')
            thread_manager.start()
            input('')

            try:
                cmd('exit')
            except:
                pass

            if os.name == 'nt':
                ctypes.windll.kernel32.SetConsoleTitleW(f'Haze v{VERSION}')
            elif os.name == 'posix':
                print(f'\33]0;Haze v{VERSION}\a', end='', flush=True)

            os.system('cls' if os.name == 'nt' else 'clear')
            stdscr = initscr()
        else:
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            break
# Salvo que el programa se cierre de forma inesperada, se guardan los detalles en el logger antes de cerrarse
except Exception as e:
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    logging.error(e)
    sys.exit()
