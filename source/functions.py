import os
import json
import numpy as np
import pandas as pd
from time import sleep
from datetime import datetime

headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas.
# Crea un diccionario con la estructura de la base de datos.
dataStructure = {header: [] for header in headers}

# Obtiene una lista de los precios mínimos de los cromos del juego.
def priceList(appID, session):
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
def toDataFrame(appID, session):
    # Crea una base de datos auxiliar.
    dataBaseAux = pd.DataFrame.from_dict(dataStructure)
    for i in range(len(appID)):
        # Obtiene el link al juego.
        storeURL = "https://store.steampowered.com/api/appdetails?cc=ar&appids=" + \
            str(appID[i])
        # Envia una solicitud al servidor para obtener los datos del juego.
        response = session.get(storeURL)
        # Si falla la solicitud, reintenta cada 5 segundos.
        while(response.status_code != 200):
            os.system('cls')
            print('Error, reintentando en 5 segundos...')
            sleep(5)
            os.system("cls")
            response = session.get(storeURL)
        
        if(len(appID) > 250):
            sleep(1)
        gameData = json.loads(response.text)

        cardPrices = priceList(appID[i], session)  # Obtiene el precio de las cartas.
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

def saveDatabase(dataBase):
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
