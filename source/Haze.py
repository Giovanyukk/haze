# Standard library imports
import os
import subprocess
import sys
import logging
import json
import threading as thr
import ctypes

# Third party imports
import pandas as pd

# Local application imports
from functions import to_dataframe, save_database, delete_database, get_appid_list, welcome_screen
from classes import User
from ASF import idle_bot, cmd, wait_for_threads

VERSION = '0.10.0'

# Titulo de la ventana
ctypes.windll.kernel32.SetConsoleTitleW(f'Haze v{VERSION}')

os.system('cls')
welcome_screen()

# Se inicializa el logger para el manejo de errores
logging.basicConfig(filename='log.txt', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

# Si no existe la carpeta database, se crea
if(not os.path.exists('database')):
    os.makedirs('database')

# Se crea un objeto usuario
user = User()

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

# Entradas del menu principal
menu = {}
menu['1'] = 'Actualizar base de datos local'
menu['2'] = 'Actualizar desde Steam'
menu['3'] = 'ArchiSteamFarm'

os.system('cls')

# TODO: Iniciar ASF directamente desde Haze
with open('./user.json', 'r') as f:
    try:
        asf_path = json.load(f)['asf_path']
    except:
        print('No se ha definido la ruta del ejecutable de ArchiSteamFarm. Puede definirla editando el archivo user.json')
        asf_path = None

try:
    while(True):
        # Se imprime el menu principal
        print('Ingrese una de las siguientes opciones:')
        for entry in list(menu.keys()):
            print(f'\t({entry}) {menu[entry]}')
        print('\t(Enter) Salir')

        option = input('Opción: ')
        if(option == '1'):
            if(database['AppID'].tolist() != [] and os.path.isfile('database/main.csv')):
                database = database.append(to_dataframe(
                    database['AppID'].tolist(), user.session), ignore_index=True)
                save_database(database)
            else:
                os.system('cls')
                print('La base de datos no existe o está vacia.')
        elif(option == '2'):
            delete_database()
            database = pd.DataFrame.from_dict(data_structure)
            appid_list = get_appid_list()
            # Da la opcion de omitir los juegos que ya estan comprados
            if(user.webAPIKey != '' and (input('Omitir juegos que ya estan en mi biblioteca? (Y/n) ') or 'y') == 'y'):
                owned_games_URL = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + \
                    user.webAPIKey + '&steamid=' + \
                    str(user.steamID64) + '&format=json'
                games_data = user.session.get(owned_games_URL).json()
                owned_games_list = [int(games_data['response']['games'][x]['appid']) for x in range(
                    len(games_data['response']['games']))]
                appid_list = [x for x in appid_list if int(
                    x) not in owned_games_list]
                database = database.append(to_dataframe(
                    appid_list, user.session), ignore_index=True)
                save_database(database)
            else:
                database = database.append(to_dataframe(
                    appid_list, user.session), ignore_index=True)
                save_database(database)
        elif(option == '3'):
            os.system('cls')
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
            
            ctypes.windll.kernel32.SetConsoleTitleW(f'Haze v{VERSION}')
            os.system('cls')
        else:
            break
# Salvo que el programa se cierre de forma inesperada, se guardan los detalles en el logger antes de cerrarse
except KeyboardInterrupt:
    sys.exit()
except Exception as e:
    logging.error(e)
    sys.exit()
