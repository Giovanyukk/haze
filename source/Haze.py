import os
import sys
import threading
import logging
import requests
import json
import numpy as np
import pandas as pd
import steam.webauth as wa
import steam.guard as guard
from subprocess import call
from lxml import html
from zipfile import ZipFile

import functions as f # Funciones internas

os.system('cls')  # Limpia la pantalla

# Se inicializa el logger para el manejo de errores
logging.basicConfig(filename='log.txt', level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

# Si no existe la carpeta database, la crea
if(not os.path.exists('database')):
    os.makedirs('database')

# Si no existe la carpeta pupflare, la descarga e instala el script
if(not os.path.exists('pupflare')):
    download_link = 'https://github.com/unixfox/pupflare/archive/refs/heads/master.zip'
    r = requests.get(download_link, allow_redirects=True)
    with open('pupflare-master.zip', 'wb') as zip:
        zip.write(r.content)
    with ZipFile('pupflare-master.zip', 'r') as zip:
        zip.extractall()
    os.rename('pupflare-master', 'pupflare')
    os.remove('pupflare-master.zip')
    os.remove('pupflare/.gitignore')
    os.remove('pupflare/Dockerfile')
    call('npm install', cwd='pupflare', shell=True)

# Configura el thread que corre el script de puppeteer
js = threading.Thread(target=call, args=('node pupflare/index.js',), daemon=True)
js.start()

# Variables de usuario
username = ''
password = ''
webAPIKey = '' # https://steamcommunity.com/dev/apikey
steamID64 = '' # https://steamidfinder.com/

# Detecta si existe un archivo de configuracion, utilizándolo en tal caso o creando uno en caso contrario
if (os.path.isfile('user.json')):
    try:
        with open('user.json','r',encoding='utf-8') as usercfg:
            data = json.load(usercfg)
            username = data['username']
            password = data['password']
            webAPIKey = data['key']
            steamID64 = data['steamID64']
    except:
        print('Archivo de configuración inválido. Por favor eliminelo y reinicie el programa\n')
        input()
        sys.exit()
else:
    with open('user.json','w',encoding='utf-8') as usercfg:
        print('Se creará un archivo de configuracion en el directorio del programa')
        print('Para poder omitir los juegos ya comprados al agregar juegos desde steamdb.info, deberá agregar su SteamID64 y Steam API Key al archivo de configuración')
        username = input('Ingrese su nombre de usuario: ')
        password = input('Ingrese su contraseña: ')
        data = {'username':username, 'password':password, 'key':'', 'steamID64':''}
        json.dump(data, usercfg)

# Intenta iniciar sesión. Si existe el archivo 2FA.maFile, genera el código 2FA automaticamente
user = wa.WebAuth(username)
if(os.path.isfile('2FA.maFile')):
    with open('2Fa.maFile','r') as f:
        data = json.load(f)
    # La sesion se guarda en una variable para poder usarse posteriormente para las solicitudes
    session = user.cli_login(password, twofactor_code=guard.SteamAuthenticator(secrets=data).get_code())
else:
    session = user.cli_login(password)

# Centra los headers de la DataFrame.
pd.set_option('colheader_justify', 'center')
headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas.
# Crea un diccionario con la estructura de la base de datos.
data_structure = {header: [] for header in headers}

# Verifica si existe una base de datos en formato .csv.
if (os.path.isfile('database/main.csv')):
    # Si existe, carga el .csv como un DataFrame.
    database = pd.read_csv('database/main.csv')
else:
    # Si no existe, crea una DataFrame temporal
    database = pd.DataFrame.from_dict(data_structure)

# Entradas del menu principal
menu = {}
menu['1']="Actualización general" 
menu['2']="Actualizar desde steamdb.info"
menu['3']="Eliminar base de datos"
menu['4']="Salir"

try:
    while(True):
        print('Ingrese una de las siguientes opciones:')
        for entry in list(menu.keys())[0:-1]:
            print(f'\t({entry}) {menu[entry]}')
        print('\t(Enter) Salir')

        option = input('Opción: ')
        if(option == '1'):
            if(database['AppID'].tolist() != [] and os.path.isfile('database/main.csv')):
                database = database.append(f.toDataFrame(database['AppID'].tolist(), session), ignore_index=True)
                f.saveDatabase(database)
            else:
                os.system('cls')
                print('La base de datos no existe o está vacia.')
        elif(option == '2'):
            with open('database/steamdb.html', 'w', encoding='utf-8') as f:
                while(os.stat('database/steamdb.html').st_size < 10000):
                    f.write(requests.get('http://localhost:3000/?url=https://steamdb.info/sales/?max_price=16&min_reviews=0&min_rating=0&min_discount=0&cc=ar&category=29&displayOnly=Game').text)
            with open('database/steamdb.html','r',encoding='utf-8') as htmlfile:
                # Da la opcion de omitir los juegos que ya estan comprados
                if(webAPIKey != "" and steamID64 != "" and (input('Omitir juegos que ya estan en mi biblioteca? (Y/n) ') or 'y') == "y"):
                    ownedGamesURL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + webAPIKey + "&steamid=" + steamID64 + "&format=json"
                    gamesData = json.loads(session.get(ownedGamesURL).text)
                    ownedGamesList = [0] * len(gamesData['response']['games'])
                    for i in range(len(gamesData['response']['games'])):
                        ownedGamesList[i] = int(gamesData['response']['games'][i]['appid'])
                    content = htmlfile.read()
                    tree = html.fromstring(content)
                    appidlist = tree.xpath('//tr[@data-appid]/@data-appid')
                    for i in ownedGamesList:
                        if str(i) in appidlist:
                            appidlist.remove(str(i))
                    database = database.append(f.toDataFrame(appidlist, session), ignore_index=True)
                    f.saveDatabase(database)
                else:
                    content = htmlfile.read()
                    tree = html.fromstring(content)
                    appidlist = tree.xpath('//tr[@data-appid]/@data-appid')
                    database = database.append(f.toDataFrame(appidlist, session), ignore_index=True)
                    f.saveDatabase(database)
        elif(option == '3'):
            if(os.path.isfile('database/main.csv')):
                database = pd.DataFrame.from_dict(data_structure)
                os.remove('database/main.csv')
                try:
                    os.remove('database/main.xlsx')
                except:
                    pass
                os.system('cls')
                print("Se eliminó la base de datos.")
            else:
                os.system('cls')
                print("No existe base de datos.")
        else:
            break
    try:
        os.system('taskkill /f /im node.exe')
    except:
        pass
except KeyboardInterrupt:
    sys.exit()
except Exception as e:
    logging.error(e)
    sys.exit()
    