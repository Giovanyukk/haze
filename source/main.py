import requests
import json
import numpy as np
import pandas as pd
import steam.webauth as wa
import os
from time import sleep
from datetime import datetime
from lxml import html

os.system('cls')  # Limpia la pantalla

username = ""
password = ""
# Hay que completar estos datos para poder utilizar la funcion de omitir juegos que ya estan en la biblioteca
webAPIKey = "" # https://steamcommunity.com/dev/apikey
steamID64 = "" # https://steamidfinder.com/

if (os.path.isfile('user.json')):
    try:
        with open('./user.json','r',encoding='utf-8') as usercfg:
            data = json.load(usercfg)
            username = data['username']
            password = data['password']
            webAPIKey = data['key']
            steamID64 = data['steamID64']
    except:
        print('Archivo de configuración inválido. Por favor eliminelo y reinicie el programa\n')
        input()
        exit()
else:
    with open('./user.json','w',encoding='utf-8') as usercfg:
        print('Se creará un archivo de configuracion en el directorio del programa\n')
        print('Para poder omitir los juegos ya comprados al agregar juegos desde steamdb.info, deberá agregar su SteamID64 y Steam API Key al archivo de configuración\n')
        username = input('Ingrese su nombre de usuario: ')
        password = input('\nIngrese su contraseña: ')
        data = {'username':username, 'password':password, 'key':'', 'steamID64':''}
        json.dump(data, usercfg)

user = wa.WebAuth(username)  # Crea un objeto usuario.
# Solicita la contraseña y el código 2FA para crear una sesión (session se utiliza de la misma forma que request).
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
            print("Error, reintentando en 5 segundos...")
            sleep(5)
            os.system("cls")
            responses = session.get(cardsURL)
    
    cardsData = json.loads(responses.text)
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
    # Si el primer appID es -1, se actualiza toda la lista.
    if(appID[0] == -1):
        return toDataFrame(dataBase['AppID'].tolist())
    # Si es -2, saca los appIDs del archivo steamdb.html ubicado en la carpeta database
    if(appID[0] == -2):
        if(os.path.exists('./database/steamdb.html')):
            with open('./database/steamdb.html','r',encoding='utf-8') as htmlfile:
                # Da la opcion de omitir los juegos que ya estan comprados
                if(webAPIKey != "" and steamID64 != "" and input('Omitir juegos que ya estan en mi biblioteca? (y/n)') == "y"):
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
            print("No existe el archivo steamdb.html. Debe descargarlo y ubicarlo en la carpeta 'database'. Se actualizaran los juegos existentes...")
            sleep(5)
            return toDataFrame(dataBase['AppID'].tolist())

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
            print("Error, reintentando en 5 segundos...")
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
                dataArray = [[gameName], [gamePrice / 100], [minimumProfit], [averageProfit], [
                    medianProfit], [str(appID[i])], [cardPrices], [datetime.now().strftime('%d/%m/%y %H:%M')]]

        # Crea un DataFrame con los datos para poder agregarlos.
        gamesData = pd.DataFrame.from_dict(
            {headers[j]: dataArray[j] for j in range(len(dataArray))})
        # Agrega el iésimo juego a la base de datos auxiliar.
        dataBaseAux = dataBaseAux.append(gamesData, ignore_index=True)

        os.system('cls')
        # Imprime el número de juego / número de juegos totales.
        print(str(i+1) + '/' + str(len(appID)))
        # Imprime la información del juego siendo analizado actualmente.
        print(gamesData)
    os.system('cls')
    print(dataBaseAux)
    return dataBaseAux


while(1):
    # AppIDs de los juegos a analizar.
    print('A continuacion, ingrese AppIDs separados por comas (Tambien puede usar -1 para actualizacion general y -2 para usar el archivo steamdb.html)')
    appIDs = input('AppIDs:')
    if (appIDs == ''):  # Si no se especifican appIDs
        exit()  # Termina el programa
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
        exit()
    except Exception as e:
        with open('log.txt',"w") as f:
            f.write(str(e))
        exit()
    # Elimina los duplicados.
    dataBase.drop_duplicates(subset='Nombre', keep='last',
                             inplace=True, ignore_index=True)
    # Ordena por retorno mínimo.
    dataBase.sort_values('Retorno mínimo', ascending=False, inplace=True)
    # Guarda todo en un archivo .csv.
    if (os.path.exists('database')):
        dataBase.to_csv('database/main.csv', index=False)
    else:
        os.makedirs('database')
        dataBase.to_csv('database/main.csv', index=False)