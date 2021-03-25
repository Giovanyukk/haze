import requests
import json
import numpy as np
import pandas as pd
import steam.webauth as wa
import steam.guard as guard
import os
from time import sleep
from datetime import datetime
from lxml import html
import sys
import logging

# Se inicializa el logger para el manejo de errores
logging.basicConfig(filename='log.txt', level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

os.system('cls')  # Limpia la pantalla

# Si no existe la carpeta database, la crea
if(not os.path.exists('database')):
    os.makedirs('database')

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
    # Si el primer appID es -1, se actualiza toda la lista.
    if(appID[0] == -1):
        if(dataBase['AppID'].tolist() != [] and os.path.isfile('database/main.csv')):
            return toDataFrame(dataBase['AppID'].tolist())
        else:
            os.system('cls')
            print('La base de datos no existe o está vacia.')
            main()
    # Si es -2, saca los appIDs del archivo steamdb.html ubicado en la carpeta database
    if(appID[0] == -2):
        if(os.path.exists('database/steamdb.html')):
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
                    return toDataFrame(appidlist)
                else:
                    content = htmlfile.read()
                    tree = html.fromstring(content)
                    appidlist = tree.xpath('//tr[@data-appid]/@data-appid')
                    return toDataFrame(appidlist)
        else:
            os.system('cls')
            print("No existe el archivo steamdb.html. Debe descargarlo y ubicarlo en la carpeta 'database'.")
            main()
    # Si es -3, borra el archivo main
    if(appID[0] == -3):
        if(os.path.isfile('database/main.csv')):
            dataBase = pd.DataFrame.from_dict(dataStructure)
            os.remove('database/main.csv')
            if(os.path.isfile('database/main.xlsx')):
                os.remove('database/main.xlsx')
            os.system('cls')
            print("Se eliminó la base de datos.")
            main()
        else:
            os.system('cls')
            print("No existe base de datos.")
            main()

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
        
        sleep(1)
        gameData = json.loads(response.text)

        cardPrices = priceList(appID[i])  # Obtiene el precio de las cartas.
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
    print(dataBaseAux.drop(columns=['Lista de cromos', 'Ultima actualización']))
    return dataBaseAux

def main():
    global dataBase
    global storeSession
    # AppIDs de los juegos a analizar.
    print('Ingrese AppIDs separados por comas o una de las siguientes opciones:')
    print('\t(-1) Actualización general')
    print('\t(-2) Utilizar archivo steamdb.html')
    print('\t(-3) Eliminar base de datos')
    print('\t(Enter) Salir')
    appIDs = input('AppIDs:')
    if (appIDs == ''):  # Si no se especifican appIDs
        sys.exit()  # Termina el programa
    # Separa el string de appIDs en un array
    appID = [int(id) for id in appIDs.split(',')]

    # Elimina los duplicados.
    dataBase.drop_duplicates(subset='Nombre', keep='last',
                             inplace=True, ignore_index=True)
    # Se crea una sesion para hacer mas eficiente la conexion con el servidor
    storeSession = requests.Session()
    # Agrega los juegos a la base de datos.
    try:
        dataBase = dataBase.append(toDataFrame(appID), ignore_index=True)
    # Si ocurre algun error, guarda los detalles en el archivo log.txt
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        logging.error(e)
        sys.exit()
    # Elimina los duplicados.
    dataBase.drop_duplicates(subset='Nombre', keep='last',
                             inplace=True, ignore_index=True)
    # Ordena por retorno mínimo.
    dataBase.sort_values('Retorno mínimo', ascending=False, inplace=True)
    # Guarda todo en un archivo .csv para compatibilidad y un archivo .xlsx para mejor visualización.
    dataBase.to_csv('database/main.csv', index=False)
    dataBase.to_excel(pd.ExcelWriter('database/main.xlsx', engine='xlsxwriter'), index=False, float_format='%.3f', encoding='cp1252')
    main()
main()