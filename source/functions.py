import os
import json
from time import sleep
from datetime import datetime

import numpy as np
import pandas as pd

from classes import Game

headers = ['Nombre', 'Precio', 'Retorno mínimo', 'Retorno medio', 'Retorno mediano',
           'AppID', 'Lista de cromos', 'Ultima actualización']  # Nombres de las columnas
# Se crea un diccionario con la estructura de la base de datos
data_structure = {header: [] for header in headers}


def to_dataframe(appID, session):
    '''Transformar una lista de appIDs en un dataframe con los respectivos juegos y retornarlo'''
    # Se crea una base de datos auxiliar
    database_aux = pd.DataFrame.from_dict(data_structure)
    for i in range(len(appID)):
        game = Game(appID[i], session)
        # Arma un array de arrays unidimensionales con los datos que se van a agregar
        data_array = [[game.name], [game.price], [game.min_profit], [game.avg_profit], [
            game.med_profit], [game.appID], [game.card_list], [game.last_updated]]

        # Crea un dataframe con los datos para poder agregarlos
        games_data = pd.DataFrame.from_dict(
            {headers[j]: data_array[j] for j in range(len(data_array))})
        # Agrega el i-ésimo juego a la base de datos auxiliar
        database_aux = database_aux.append(games_data, ignore_index=True)

        os.system('cls')
        # Imprime el número de juego / número de juegos totales
        print(f'{str(i+1)}/{str(len(appID))}')
        # Imprime la información del juego siendo analizado actualmente
        games_data.drop(columns=['Lista de cromos',
                        'Ultima actualización'], inplace=True)
        print(games_data)
    os.system('cls')
    print(database_aux.drop(columns=['Lista de cromos', 'Ultima actualización']).sort_values(
        'Retorno mínimo', ascending=False, ignore_index=True).head())
    return database_aux


def save_database(database):
    '''Generar los archivos .csv y .xlsx'''
    # Se eliminan los duplicados de la base de datos, se ordenan por retorno minimo y se guarda el .csv
    database.drop_duplicates(subset='Nombre', keep='last',
                             inplace=True, ignore_index=True)
    database.sort_values('Retorno mínimo', ascending=False, inplace=True)
    database.to_csv('database/main.csv', index=False)
    # Se aplica formato al archivo .xlsx
    excel_writer = pd.ExcelWriter('database/main.xlsx', engine='xlsxwriter')
    database.to_excel(excel_writer, index=False, float_format='%.3f',
                      encoding='cp1252', sheet_name='Cromos')
    worksheet = excel_writer.sheets['Cromos']
    for idx, col in enumerate(database):
        series = database[col]
        max_len = max((
            series.astype(str).map(len).max(),  # Ancho del item mas grande
            len(str(series.name))  # Ancho del nombre de la columna
        )) + 1  # Espacio extra
        # Se establece el ancho de la columna
        worksheet.set_column(idx, idx, max_len)
    worksheet.conditional_format('C2:C{}'.format(len(
        database) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format('D2:D{}'.format(len(
        database) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
    worksheet.conditional_format('E2:E{}'.format(len(
        database) + 1), {'type': '3_color_scale', 'min_type': 'num', 'mid_value': 0, 'mid_color': '#FFFFFF'})
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
