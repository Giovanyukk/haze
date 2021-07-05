import os
import requests

import pandas as pd
from lxml import html

from classes import Game

headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas
# Se crea un diccionario con la estructura de la base de datos
data_structure = {header: [] for header in headers}


def to_dataframe(appID, session):
    '''Transformar una lista de appIDs en un dataframe con los respectivos juegos y retornarlo'''
    # Se crea una base de datos auxiliar
    database = pd.DataFrame.from_dict(data_structure)
    for i in range(len(appID)):
        game = Game(appID[i], session)
        # Arma un array de arrays unidimensionales con los datos que se van a agregar
        game_data = [[game.name], [game.price], [game.min_profit], [game.avg_profit], [
            game.med_profit], [game.appID], [game.card_list], [game.last_updated]]

        # Crea un dataframe con los datos para poder agregarlos
        game_df = pd.DataFrame.from_dict(
            {headers[j]: game_data[j] for j in range(len(game_data))})
        # Agrega el i-ésimo juego a la base de datos auxiliar
        database = database.append(game_df, ignore_index=True)

        os.system('cls')
        # Imprime el número de juego / número de juegos totales
        print(f'{str(i+1)}/{str(len(appID))}')
        # Imprime la información del juego siendo analizado actualmente
        game_df.drop(columns=['Lista de cromos',
                              'Ultima actualización'], inplace=True)
        print(game_df)
    os.system('cls')
    print(database.drop(columns=['Lista de cromos', 'Ultima actualización']).sort_values(
        'Retorno mínimo', ascending=False, ignore_index=True).head())
    return database


def save_database(database):
    '''Generar los archivos .csv y .xlsx'''
    # Se eliminan los duplicados de la base de datos, se ordenan por retorno minimo y se guarda el .csv
    database.drop_duplicates(subset='Nombre', keep='last',
                             inplace=True, ignore_index=True)
    database.sort_values('Retorno mínimo', ascending=False, inplace=True)
    database.to_csv('database/main.csv', index=False)
    # Se aplica formato al archivo .xlsx
    excel_writer = pd.ExcelWriter(  # pylint: disable=abstract-class-instantiated
        'database/main.xlsx', engine='xlsxwriter')
    database.to_excel(excel_writer, index=False, float_format='%.3f',
                      encoding='cp1252', sheet_name='Cromos')
    worksheet = excel_writer.sheets['Cromos']

    for appid, i in zip(database['AppID'].values, range(len(database['AppID'].values))):
        worksheet.write_url(
            f'F{str(i + 2)}', f'https://store.steampowered.com/app/{str(appid)}/', string=str(appid))
    for idx, col in enumerate(database):
        series = database[col]
        max_len = max((
            series.astype(str).map(len).max(),  # Ancho del item mas grande
            len(str(series.name))  # Ancho del nombre de la columna
        )) + 1  # Espacio extra
        # Se establece el ancho de la columna
        worksheet.set_column(idx, idx, max_len)

    worksheet.conditional_format(f'C2:C{str(len(database) + 1)}', {
                                 'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format(f'D2:D{str(len(database) + 1)}', {
                                 'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format(f'E2:E{str(len(database) + 1)}', {
                                 'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    # Se guarda el .xlsx
    excel_writer.save()


def delete_database():
    '''Eliminar los archivos .csv y .xlsx'''
    if(os.path.isfile('database/main.csv')):
        os.remove('database/main.csv')
        try:
            os.remove('database/main.xlsx')
        except:
            pass
        os.system('cls')
        print('Se eliminó la base de datos.')
    else:
        os.system('cls')
        print('No existe base de datos.')


def get_appid_list(maxprice=16):
    '''Obtener los appids de los juegos con precio inferior a maxprice'''
    appid_list = []
    i = 1
    while(True):
        page = requests.get(
            f'https://store.steampowered.com/search/results/?query&start=0&count=200&dynamic_data=&sort_by=Price_ASC&ignore_preferences=1&maxprice=70&category1=998&category2=29&snr=1_7_7_2300_7&specials=1&infinite=0&page={i}')
        tree = html.fromstring(page.content)
        price_list = tree.xpath(
            '//div[@class="col search_price discounted responsive_secondrow"]/text()')
        price_list = [x[5:].replace(',', '.') for x in [
            y.rstrip() for y in price_list] if x not in ['']]
        price_list = [float(x) if x != '' else 0 for x in price_list]
        if any(float(x) > 16 for x in price_list):
            try:
                appid_list += tree.xpath('//a[@data-ds-appid]/@data-ds-appid')[
                    :price_list.index(next(filter(lambda x: x > maxprice, price_list), None)) + 1]
            except:
                appid_list += tree.xpath('//a[@data-ds-appid]/@data-ds-appid')[
                    :price_list.index(next(filter(lambda x: x > maxprice, price_list), None))]
            break
        appid_list += tree.xpath('//a[@data-ds-appid]/@data-ds-appid')
        i += 1
    appid_list = [x for x in appid_list if not ',' in x]
    return appid_list
