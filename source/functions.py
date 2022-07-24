import datetime
import os
import requests
import curses
import pickle

import pandas as pd
from lxml import html
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from matplotlib import dates, ticker
from time import time, sleep
from curseXcel import Table

from classes import Game

headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas
# Se crea un diccionario con la estructura de la base de datos
data_structure = {header: [] for header in headers}


def to_dataframe(appID: list, session: requests.Session, stdscr: curses.window = None):
    '''Transformar una lista de appIDs en un dataframe con los respectivos juegos y retornarlo'''
    # Se crea una base de datos auxiliar
    database = pd.DataFrame.from_dict(data_structure)
    if stdscr != None and stdscr.getmaxyx()[0] > 6:
        table_column_width = stdscr.getmaxyx()[1] // (len(headers) - 2)
        table = Table(stdscr, 7, len(headers) - 2, table_column_width,
                      stdscr.getmaxyx()[1], stdscr.getmaxyx()[0], col_names=True)
        table.cursor_down()
        for idx, header in enumerate(headers[:-2]):
            table.set_column_header(header.center(
                stdscr.getmaxyx()[1] // (len(headers) - 2)), idx)
    for i in range(len(appID)):
        game = Game(appID[i], session, stdscr=stdscr)
        # Arma un array de arrays unidimensionales con los datos que se van a agregar
        game_data = [[game.name], [game.price], [game.min_profit], [game.avg_profit], [
            game.med_profit], [game.appID], [game.card_list], [game.last_updated]]

        # Crea un dataframe con los datos para poder agregarlos
        game_df = pd.DataFrame.from_dict(
            {headers[j]: game_data[j] for j in range(len(game_data))})
        # Agrega el i-ésimo juego a la base de datos auxiliar
        database = pd.concat([database, game_df], ignore_index=True)

        if stdscr != None and stdscr.getmaxyx()[0] > 6:
            top_df = database.drop(columns=['Lista de cromos',
                                            'Ultima actualización']).sort_values('Retorno mínimo', ascending=False,
                                                                                 ignore_index=True).head(5)
            table.set_cell(1, 2, "TOP".center(table_column_width))
            table.set_cell(
                1, 3, f'{str(i+1)}/{str(len(appID))}'.center(table_column_width))
            for j in range(len(headers) - 2):
                table.set_cell(0, j, str(game_df.iloc[0, j]))
                for k in range(2, 9):
                    try:
                        table.set_cell(k, j, str(top_df.iloc[k - 2, j]))
                    except:
                        pass
            table.refresh()
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
    else:
        pass


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
        if any(float(x) > maxprice for x in price_list):
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


def get_card_price_history(market_hash_name: str, session: requests.Session = requests.Session, since: str = 'general'):
    '''Obtener el historial de precios de un cromo

    since : str
        'general', 'last-week', 'last-month', default:'general'

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
        if(since == 'general'):
            return X, Y, N
        elif(since == 'last-week'):
            X = [i for i in X if i > datetime.datetime.today() -
                 datetime.timedelta(7)]
            Y = Y[-len(X):]
            N = N[-len(X):]
            return X, Y, N
        elif(since == 'last-month'):
            X = [i for i in X if i > datetime.datetime.today() -
                 datetime.timedelta(31)]
            Y = Y[-len(X):]
            N = N[-len(X):]
            return X, Y, N
        else:
            raise ValueError(
                f'Debe indicar un periodo de tiempo válido')
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
    fig.set_facecolor('#1B2838')

    ax[0].yaxis.set_major_formatter(ticker.FormatStrFormatter("ARS$%.2f"))
    ax[0].xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%y'))

    for i in range(2):
        ax[i].set_facecolor('#101822')
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
        '399430-Super%20Tinboy', session, since='last-month')

    ax = setup_subplots()

    ax[0].plot(X, Y, color='#688F3E')

    ax[1].fill_between(X_buy, Y_buy, step='post',
                       color='#6B8FC3', alpha=0.9, lw=1.5)
    ax[1].fill_between(X_sell, Y_sell, step='post',
                       color='#688F3E', alpha=0.9, lw=1.5)

    plt.show()


def trusty_sleep(seconds: float):
    start = time()
    while (time() - start < seconds):
        sleep(seconds - (time() - start))


def print_center(stdscr, text: str):
    '''Imprimir un texto centrado en la pantalla'''

    stdscr.clear()
    if len(text.split('\n')) > 1:
        for idx, line in enumerate(text.split('\n')):
            stdscr.addstr(stdscr.getmaxyx()[
                          0]//2 - len(text.split('\n')) + idx, stdscr.getmaxyx()[1]//2 - len(line)//2, line)
    else:
        stdscr.addstr(stdscr.getmaxyx()[
                      0]//2, stdscr.getmaxyx()[1]//2 - len(text)//2, text)
    stdscr.refresh()


def print_menu(stdscr: curses.window, menu: list[str], selected_row_idx: int = 0, logo: str = None, title: str = None):
    '''Imprimir un menú en la pantalla'''

    stdscr.clear()
    lines = stdscr.getmaxyx()[0]
    cols = stdscr.getmaxyx()[1]
    if logo != None:
        x_free = cols - len(logo.split('\n')[0]) - len(max(menu, key=len))
        y_free = lines - len(logo.split('\n')) - len(menu)

    if logo != None and x_free >= 3 and lines >= max((len(menu), len(logo.split('\n')))) + 2:
        for idx, row in enumerate(logo.split('\n')):
            x = x_free//3
            y = lines//2 - len(logo.split('\n'))//2 + idx
            stdscr.addstr(y, x, row)
        for idx, row in enumerate(menu):
            x = 2*(x_free//3) + len(logo.split('\n')
                                    [0]) + len(max(menu, key=len))//2 - len(row)//2
            y = lines//2 - len(menu)//2 + idx
            if idx == selected_row_idx:
                stdscr.attron(curses.color_pair(
                    2 if idx == len(menu) - 1 else 1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(
                    2 if idx == len(menu) - 1 else 1))
            else:
                stdscr.addstr(y, x, row)
    elif logo != None and y_free >= 3:
        for idx, row in enumerate(logo.split('\n')):
            x = cols//2 - len(row)//2
            y = y_free//3 + idx
            stdscr.addstr(y, x, row)
        for idx, row in enumerate(menu):
            x = cols//2 - len(row)//2
            y = 2*(y_free//3) + len(logo.split('\n')) + idx
            if idx == selected_row_idx:
                stdscr.attron(curses.color_pair(
                    2 if idx == len(menu) - 1 else 1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(
                    2 if idx == len(menu) - 1 else 1))
            else:
                stdscr.addstr(y, x, row)
    elif lines > len(menu) + (2 if title == None else 3) and cols > len(max(menu, key=len)):
        if title != None:
            stdscr.addstr(lines//2 - len(menu)//2 - 1,
                          cols//2 - len(title)//2, title)
        for idx, row in enumerate(menu):
            x = cols//2 - len(row)//2
            y = lines//2 - len(menu)//2 + idx
            if idx == selected_row_idx:
                stdscr.attron(curses.color_pair(
                    2 if idx == len(menu) - 1 else 1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(
                    2 if idx == len(menu) - 1 else 1))
            else:
                stdscr.addstr(y, x, row)
    else:
        try:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(lines//2, cols//2 - 14,
                          'No se puede mostrar el menu!')
        except:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(lines//2, cols//2, '!')

    stdscr.refresh()


def create_menu(stdscr, menu: list[str], current_row: int = 0, logo=None, title=None):
    '''Crear un menú en la pantalla'''

    while True:
        print_menu(stdscr, menu, current_row, logo, title)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            if current_row > 0:
                current_row -= 1
            else:
                current_row = len(menu) - 1
        elif key == curses.KEY_DOWN:
            if current_row < len(menu) - 1:
                current_row += 1
            else:
                current_row = 0
        elif key == curses.KEY_ENTER or key in [10, 13]:
            # if user selected last row, exit the program
            if current_row == len(menu) - 1:
                break
            break
    # Retorna la opción seleccionada
    return current_row


def initscr():
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.clear()
    # Desactivar el parpadeo del cursor
    curses.curs_set(0)

    # Esquema de colores para la fila seleccionada
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)
    return stdscr


def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)


def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
