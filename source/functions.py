import os
import json
from time import sleep
from datetime import datetime

import numpy as np
import pandas as pd

headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas.
# Crea un diccionario con la estructura de la base de datos.
data_structure = {header: [] for header in headers}


# Obtiene una lista de los precios mínimos de los cromos del juego.
def get_price_list(appID, session):
    # Obtiene el link a los cromos de un juego.
    cards_URL = 'https://steamcommunity.com/market/search/render/?l=spanish&currency=34&category_753_cardborder%5B%5D=tag_cardborder_0&category_753_item_class%5B%5D=tag_item_class_2&appid=753&norender=1&category_753_Game%5B%5D=tag_app_' + \
        str(appID)
    responses = session.get(cards_URL)
    # Si falla la solicitud, reintenta cada 5 segundos.
    while(responses.status_code != 200):
        os.system('cls')
        print('Error, reintentando en 5 segundos...')
        sleep(5)
        os.system('cls')
        responses = session.get(cards_URL)

    cards_data = json.loads(responses.text)
    # Si no existen cromos, retorna 0 para evitar un error
    if(cards_data['total_count'] == 0):
        return [0]
    # Genera una array con la misma longitud que la cantidad de cromos.
    cards_prices = np.zeros(len(cards_data['results']))

    for i in range(len(cards_data['results'])):
        # Obtiene el valor de la iésima carta y limpia el string para sólo obtener el valor numérico.
        lowest_price = cards_data['results'][i]['sell_price_text'][5:]
        cards_prices[i] = float(lowest_price.replace(',', '.'))

    # Retorna la lista de los cromos en orden ascendente.
    return np.sort(cards_prices)


# Transforma una lista de appIDs en un dataframe con los respectivos juegos.
def to_dataframe(appID, session):
    # Crea una base de datos auxiliar.
    database_aux = pd.DataFrame.from_dict(data_structure)
    for i in range(len(appID)):
        # Obtiene el link al juego.
        store_URL = 'https://store.steampowered.com/api/appdetails?cc=ar&appids=' + \
            str(appID[i])
        # Envia una solicitud al servidor para obtener los datos del juego.
        response = session.get(store_URL)
        # Si falla la solicitud, reintenta cada 5 segundos.
        while(response.status_code != 200):
            os.system('cls')
            print('Error, reintentando en 5 segundos...')
            sleep(5)
            os.system('cls')
            response = session.get(store_URL)

        if(len(appID) > 250):
            sleep(1)
        game_data = json.loads(response.text)

        # Obtiene el precio de los cromos.
        cards_prices = get_price_list(appID[i], session)
        if(len(appID) > 250):
            sleep(1)

        # Obtiene el nombre del juego.
        game_name = game_data[str(appID[i])]['data']['name']
        # Detecta si el juego es gratis o no.
        is_free = game_data[str(appID[i])]['data']['is_free']
        # Inicializa la variable data_array
        data_array = []

        if (len(cards_prices) != 0):  # Si el juego posee cromos...
            # Obtiene la cantidad de los cromos que se dropean del juego.
            cards_dropped = 3 if len(
                cards_prices) == 5 else len(cards_prices)//2
            # Calcula la media de los precios de los cromos.
            average_price = np.average(cards_prices)
            # Calcula la mediana de los precios de los cromos.
            median_price = np.median(cards_prices)

            if is_free:  # Si el juego es gratis...
                # Arma un array de arrays unidimensionales con los datos que se van a agregar.
                data_array = [[game_name], [0], [0], [0], [0], [str(appID[i])], [cards_prices], [
                    datetime.now().strftime('%d/%m/%y %H:%M')]]
            else:
                # Obtiene el precio del juego en centavos.
                game_price = game_data[str(
                    appID[i])]['data']['price_overview']['final']
                # Calcula el retorno mínimo posible.
                minimum_profit = (
                    (cards_prices[0] * cards_dropped * 0.8696 / (game_price / 100)) - 1)
                # Calcula el retorno mínimo posible.
                average_profit = (
                    (average_price * cards_dropped * 0.8696 / (game_price / 100)) - 1)
                # Calcula el retorno mínimo posible.
                median_profit = ((median_price * cards_dropped *
                                 0.8696 / (game_price / 100)) - 1)
                # Arma un array de arrays unidimensionales con los datos que se van a agregar.
                data_array = [[game_name], [game_price / 100], [round(minimum_profit, 3)], [round(average_profit, 3)], [
                    round(median_profit, 3)], [str(appID[i])], [cards_prices], [datetime.now().strftime('%d/%m/%y %H:%M')]]

        # Crea un DataFrame con los datos para poder agregarlos.
        games_data = pd.DataFrame.from_dict(
            {headers[j]: data_array[j] for j in range(len(data_array))})
        # Agrega el iésimo juego a la base de datos auxiliar.
        database_aux = database_aux.append(games_data, ignore_index=True)

        os.system('cls')
        # Imprime el número de juego / número de juegos totales.
        print(str(i+1) + '/' + str(len(appID)))
        # Imprime la información del juego siendo analizado actualmente.
        games_data.drop(columns=['Lista de cromos',
                        'Ultima actualización'], inplace=True)
        print(games_data)
    os.system('cls')
    print(database_aux.drop(columns=['Lista de cromos', 'Ultima actualización']).sort_values(
        'Retorno mínimo', ascending=False, ignore_index=True).head())
    return database_aux


def save_database(dataBase):
    dataBase.drop_duplicates(subset='Nombre', keep='last',
                             inplace=True, ignore_index=True)
    dataBase.sort_values('Retorno mínimo', ascending=False, inplace=True)
    dataBase.to_csv('database/main.csv', index=False)
    excel_writer = pd.ExcelWriter('database/main.xlsx', engine='xlsxwriter')
    dataBase.to_excel(excel_writer, index=False, float_format='%.3f',
                      encoding='cp1252', sheet_name='Cromos')
    worksheet = excel_writer.sheets['Cromos']  # Formateo del archivo .xlsx
    for idx, col in enumerate(dataBase):
        series = dataBase[col]
        max_len = max((
            series.astype(str).map(len).max(),  # Ancho del item mas grande
            len(str(series.name))  # Ancho del nombre de la columna
        )) + 1  # Espacio extra
        # Se establece el ancho de la columna
        worksheet.set_column(idx, idx, max_len)
    worksheet.conditional_format('C2:C{}'.format(len(
        dataBase) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format('D2:D{}'.format(len(
        dataBase) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format('E2:E{}'.format(len(
        dataBase) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    excel_writer.save()
