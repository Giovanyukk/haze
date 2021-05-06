# Standard library imports
import os
import sys
import logging
import json

# Third party imports
import pandas as pd

# Local application imports
from functions import to_dataframe, save_database, delete_database, get_appid_list
from classes import User

os.system('cls')

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
menu['1'] = 'Actualización general'
menu['2'] = 'Actualizar desde steamdb.info'
menu['3'] = 'Eliminar base de datos'
menu['4'] = 'Salir'

os.system('cls')

try:
    while(True):
        print('Ingrese una de las siguientes opciones:')
        for entry in list(menu.keys())[0:-1]:
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
                games_data = json.loads(
                    user.session.get(owned_games_URL).text)
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
            delete_database()
            database = pd.DataFrame.from_dict(data_structure)
        else:
            break
# Salvo que el programa se cierre de forma inesperada, se guardan los detalles en el logger antes de cerrarse
except KeyboardInterrupt:
    sys.exit()
except Exception as e:
    logging.error(e)
    sys.exit()
