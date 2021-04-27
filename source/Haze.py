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
from time import sleep
from datetime import datetime
from lxml import html

os.system('cls')  # Limpia la pantalla

# Se inicializa el logger para el manejo de errores
logging.basicConfig(filename='log.txt', level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

# Configura el thread que corre el script de puppeteer
js = threading.Thread(target=call, args=('node pupflare/index.js',), daemon=True)
js.start()

# Si no existe la carpeta database, la crea
if(not os.path.exists('database')):
    os.makedirs('database')

if(not os.path.exists('pupflare/node_modules')):
    call('npm install', cwd='pupflare', shell=True)

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
    session = user.cli_login(password, twofactor_code=guard.SteamAuthenticator(secrets=data).get_code())
else:
    session = user.cli_login(password)

# Centra los headers de la DataFrame.
pd.set_option('colheader_justify', 'center')
headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas.
# Crea un diccionario con la estructura de la base de datos.
dataStructure = {header: [] for header in headers}

# Verifica si existe una base de datos en formato .csv.
if (os.path.isfile('database/main.csv')):
    # Si existe, carga el .csv como un DataFrame.
    dataBase = pd.read_csv('database/main.csv')
else:
    # Si no existe, crea una DataFrame temporal y al final la guarda en un archivo.
    dataBase = pd.DataFrame.from_dict(dataStructure)

# Obtiene una lista de los precios mínimos de los cromos del juego.
def priceList(appID):
    # Obtiene el link a los cromos de un juego.
    cardsURL = "https://steamcommunity.com/market/search/render/?l=spanish&currency=34&category_753_cardborder%5B%5D=tag_cardborder_0&category_753_item_class%5B%5D=tag_item_class_2&appid=753&norender=1&category_753_Game%5B%5D=tag_app_" + \
        str(appID)
    responses = session.get(cardsURL)
    # Si falla la solicitud, reintenta cada 5 segundos.
    while(responses.status_code != 200):
            os.system('cls')
            print('Error, reintentando en 5 segundos...')
            sleep(5)
            os.system('cls')
            responses = session.get(cardsURL)
    
    cardsData = json.loads(responses.text)
    # Si no existen cartas, retorna 0 para evitar un error
    if(cardsData['total_count'] == 0):
        return [0]
    # Genera una array con la misma longitud que la cantidad de cromos.
    cardPrices = np.zeros(len(cardsData['results']))

    for i in range(len(cardsData['results'])):
        # Obtiene el valor de la iésima carta y limpia el string para sólo obtener el valor numérico.
        lowestPrice = cardsData['results'][i]['sell_price_text'][5:]
        cardPrices[i] = float(lowestPrice.replace(',', '.'))

    # Retorna la lista de los cromos en orden ascendente.
    return np.sort(cardPrices)


# Transforma una lista de appIDs en un dataframe con los respectivos juegos.
def toDataFrame(appID):
    global dataBase
    # Crea una base de datos auxiliar.
    dataBaseAux = pd.DataFrame.from_dict(dataStructure)
    for i in range(len(appID)):
        # Obtiene el link al juego.
        storeURL = "https://store.steampowered.com/api/appdetails?cc=ar&appids=" + \
            str(appID[i])
        # Envia una solicitud al servidor para obtener los datos del juego.
        response = storeSession.get(storeURL)
        # Si falla la solicitud, reintenta cada 5 segundos.
        while(response.status_code != 200):
            os.system('cls')
            print('Error, reintentando en 5 segundos...')
            sleep(5)
            os.system("cls")
            response = storeSession.get(storeURL)
        
        if(len(appID) > 250):
            sleep(1)
        gameData = json.loads(response.text)

        cardPrices = priceList(appID[i])  # Obtiene el precio de las cartas.
        if(len(appID) > 250):
            sleep(1)

        # Obtiene el nombre del juego.
        gameName = gameData[str(appID[i])]['data']['name']
        # Detecta si el juego es gratis o no.
        isFree = gameData[str(appID[i])]['data']['is_free']
        # Inicializa la variable dataArray
        dataArray = []

        if (len(cardPrices) != 0):  # Si el juego posee cromos...
            # Obtiene la cantidad de los cromos que se dropean del juego.
            cardsDropped = 3 if len(cardPrices) == 5 else len(cardPrices)//2
            # Calcula la media de los precios de los cromos.
            averagePrice = np.average(cardPrices)
            # Calcula la mediana de los precios de los cromos.
            medianPrice = np.median(cardPrices)

            if isFree:  # Si el juego es gratis...
                # Arma un array de arrays unidimensionales con los datos que se van a agregar.
                dataArray = [[gameName], [0], [0], [0], [0], [str(appID[i])], [cardPrices], [
                    datetime.now().strftime('%d/%m/%y %H:%M')]]
            else:
                # Obtiene el precio del juego en centavos.
                gamePrice = gameData[str(
                    appID[i])]['data']['price_overview']['final']
                # Calcula el retorno mínimo posible.
                minimumProfit = (
                    (cardPrices[0] * cardsDropped * 0.8696 / (gamePrice / 100)) - 1)
                # Calcula el retorno mínimo posible.
                averageProfit = (
                    (averagePrice * cardsDropped * 0.8696 / (gamePrice / 100)) - 1)
                # Calcula el retorno mínimo posible.
                medianProfit = ((medianPrice * cardsDropped *
                                 0.8696 / (gamePrice / 100)) - 1)
                # Arma un array de arrays unidimensionales con los datos que se van a agregar.
                dataArray = [[gameName], [gamePrice / 100], [round(minimumProfit,3)], [round(averageProfit,3)], [
                    round(medianProfit,3)], [str(appID[i])], [cardPrices], [datetime.now().strftime('%d/%m/%y %H:%M')]]

        # Crea un DataFrame con los datos para poder agregarlos.
        gamesData = pd.DataFrame.from_dict(
            {headers[j]: dataArray[j] for j in range(len(dataArray))})
        # Agrega el iésimo juego a la base de datos auxiliar.
        dataBaseAux = dataBaseAux.append(gamesData, ignore_index=True)

        os.system('cls')
        # Imprime el número de juego / número de juegos totales.
        print(str(i+1) + '/' + str(len(appID)))
        # Imprime la información del juego siendo analizado actualmente.
        gamesData.drop(columns=['Lista de cromos', 'Ultima actualización'], inplace=True)
        print(gamesData)
    os.system('cls')
    print(dataBaseAux.drop(columns=['Lista de cromos', 'Ultima actualización']).sort_values('Retorno mínimo', ascending=False, ignore_index=True).head())
    return dataBaseAux

def saveDatabase():
    global dataBase
    dataBase.drop_duplicates(subset='Nombre', keep='last', inplace=True, ignore_index=True)
    dataBase.sort_values('Retorno mínimo', ascending=False, inplace=True)
    dataBase.to_csv('database/main.csv', index=False)
    excel_writer = pd.ExcelWriter('database/main.xlsx', engine='xlsxwriter')
    dataBase.to_excel(excel_writer, index=False, float_format='%.3f', encoding='cp1252', sheet_name='Cromos')
    worksheet = excel_writer.sheets['Cromos'] # Formateo del archivo .xlsx
    for idx, col in enumerate(dataBase):
        series = dataBase[col]
        max_len = max((
            series.astype(str).map(len).max(), # Ancho del item mas grande
            len(str(series.name)) # Ancho del nombre de la columna
            )) + 1 # Espacio extra
        worksheet.set_column(idx, idx, max_len) # Se establece el ancho de la columna
    worksheet.conditional_format('C2:C{}'.format(len(dataBase) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format('D2:D{}'.format(len(dataBase) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format('E2:E{}'.format(len(dataBase) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    excel_writer.save()

# Se crea una sesion para hacer mas eficiente la conexion con el servidor
storeSession = requests.Session()

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
            if(dataBase['AppID'].tolist() != [] and os.path.isfile('database/main.csv')):
                dataBase = dataBase.append(toDataFrame(dataBase['AppID'].tolist()), ignore_index=True)
                saveDatabase()
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
                    dataBase = dataBase.append(toDataFrame(appidlist), ignore_index=True)
                    saveDatabase()
                else:
                    content = htmlfile.read()
                    tree = html.fromstring(content)
                    appidlist = tree.xpath('//tr[@data-appid]/@data-appid')
                    dataBase = dataBase.append(toDataFrame(appidlist), ignore_index=True)
                    saveDatabase()
        elif(option == '3'):
            if(os.path.isfile('database/main.csv')):
                dataBase = pd.DataFrame.from_dict(dataStructure)
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