import datetime
import os
import requests

import pandas as pd
from lxml import html
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from matplotlib import dates, ticker

from classes import Game, User

headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas
# Se crea un diccionario con la estructura de la base de datos
data_structure = {header: [] for header in headers}


def to_dataframe(appID: list, session: requests.Session):
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

    for appid, list, i in zip(database['AppID'].values, database['Lista de cromos'].values, range(len(database['AppID'].values))):
        worksheet.write_url(
            f'F{str(i + 2)}', f'https://store.steampowered.com/app/{str(appid)}/', string=str(appid))
        worksheet.write_url(
            f'G{str(i + 2)}', f'https://steamcommunity.com/market/search?category_753_Game%5B%5D=tag_app_{str(appid)}&category_753_cardborder%5B%5D=tag_cardborder_0&category_753_item_class%5B%5D=tag_item_class_2&appid=753', string=str(list))

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
    '''Obtener los appids de los juegos con precio inferior a maxprice

    Retorna: appid_list

    appid_list: list[str] Lista de appids

    1 REQUEST
    '''

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


def get_card_price_history(market_hash_name: str, session: requests.Session = requests.Session, since: datetime.date = None):
    '''Obtener el historial de precios de un cromo

    Retorna: X, Y, N

    X: list[datetime] Fechas
    Y: list[float] Precios
    N: list[int] Cantidad vendidos

    1 REQUEST
    '''

    response = session.get(
        f'https://steamcommunity.com/market/pricehistory/?appid=753&market_hash_name={market_hash_name}')
    json = response.json()

    X: list[datetime.datetime]
    Y: list[float]
    N: list[int]

    if(json['success'] == True):
        X = [datetime.datetime.strptime(
            json['prices'][i][0][:-4], '%b %d %Y %H') for i in range(len(json['prices']))]
        Y = [json['prices'][i][1]
             for i in range(len(json['prices']))]
        N = [int(json['prices'][i][2])
             for i in range(len(json['prices']))]
        if(since == None):
            return X, Y, N
        else:
            X = [i for i in X if i > datetime.datetime.combine(
                since, datetime.time(0, 0))]
            Y = Y[-len(X):]
            N = N[-len(X):]
            return X, Y, N
    else:
        raise ValueError(
            f'Hubo un error al obtener el historial de precios del cromo {market_hash_name}')


def get_card_sales_histogram(market_hash_name: str, session: requests.Session = requests.Session):
    '''Obtener el histograma de oferta/demanda de un cromo

    Retorna: X_buy, Y_buy, X_sell, Y_sell

    X_buy: list[float] Precio de compra
    Y_buy: list[int] Cantidad de ordenes de compra
    X_sell: list[float] Precio de venta
    Y_sell: list[int] Cantidad de ordenes de venta

    2 REQUESTS
    '''

    response = session.get(
        f'https://steamcommunity.com/market/listings/753/{market_hash_name}/?currency=34&country=AR')
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    last_script = str(soup.find_all('script')[-1])
    last_script_token = last_script.split('(')[-1]
    item_nameid = last_script_token.split(');')[0].strip()

    response = session.get(
        f'https://steamcommunity.com/market/itemordershistogram?country=AR&language=spanish&currency=34&item_nameid={item_nameid}&two_factor=0')
    json = response.json()

    X_buy: list[float]
    Y_buy: list[int]
    X_sell: list[float]
    Y_sell: list[int]

    if(json['success'] == 1):
        X_buy = [json['buy_order_graph'][i][0]
                 for i in range(len(json['buy_order_graph']))]
        Y_buy = [json['buy_order_graph'][i][1]
                 for i in range(len(json['buy_order_graph']))]
        X_sell = [json['sell_order_graph'][i][0]
                  for i in range(len(json['sell_order_graph']))]
        Y_sell = [json['sell_order_graph'][i][1]
                  for i in range(len(json['sell_order_graph']))]

        return X_buy, Y_buy, X_sell, Y_sell
    else:
        raise ValueError(
            f'Hubo un error al obtener el histograma de oferta/demanda del cromo {market_hash_name}')


def setup_subplots():
    '''Crear un subplot con el formato de colores de Steam.

    Retorna: fig, ax

    fig: plt.figure.Figure Figura
    ax: list[plt.axes.Axes] Pares de ejes
    '''

    fig, ax = plt.subplots(nrows=2, ncols=1)
    fig.set_facecolor('#1b2838')

    ax[0].yaxis.set_major_formatter(ticker.FormatStrFormatter("ARS$%.2f"))
    ax[0].xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%y'))

    for i in range(2):
        ax[i].set_facecolor('#1b2838')
        ax[i].grid()
        ax[i].tick_params(axis='x', colors='white')
        ax[i].tick_params(axis='y', colors='white')
        ax[i].xaxis.label.set_color('white')
        ax[i].yaxis.label.set_color('white')
        ax[i].spines['left'].set_color('white')
        ax[i].spines['top'].set_color('white')
        ax[i].spines['bottom'].set_color('white')
        ax[i].spines['right'].set_color('white')

    return ax


def plot_graphs(session: requests.Session = requests.Session):
    '''Graficar el historial de ventas y el histograma de precios de un cromo'''

    X_buy, Y_buy, X_sell, Y_sell = get_card_sales_histogram(
        '399430-Super%20Tinboy', session)
    X, Y, _ = get_card_price_history(
        '399430-Super%20Tinboy', session, since=datetime.date(2021, 6, 1))

    ax = setup_subplots()

    ax[0].plot(X, Y, color='#688F3E')

    ax[1].fill_between(X_buy, Y_buy, step='post',
                       color='#6B8FC3', alpha=0.9, lw=1.5)
    ax[1].fill_between(X_sell, Y_sell, step='post',
                       color='#688F3E', alpha=0.9, lw=1.5)

    plt.show()
