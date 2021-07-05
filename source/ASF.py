# Standard library imports
import json
import threading
import requests
from datetime import datetime
from time import sleep

URL = 'http://127.0.0.1:1242'


def log(data: str):
    print('[' + datetime.now().strftime('%d/%m/%y %H:%M') + '] ' + data)


def get(endpoint: str):
    headers = {'Authentication': '', 'accept': 'application/json'}
    uri = f'{URL}/Api/{endpoint}'
    try:
        return requests.get(uri, headers=headers)
    except:
        return False


def post(endpoint: str, data: str):
    headers = {'Authentication': '', 'accept': 'application/json',
               'Content-Type': 'application/json'}
    uri = f'{URL}/Api/{endpoint}'
    requests.post(uri, data, headers=headers)


def cmd(data: str):
    #log(f'CMD: {data}')
    post('Command', '{"Command":"' + data + '"}')


def idle_bot(bot: str, ismain=False):
    sleep(10)

    logged_on = get(f'Bot/{bot}')
    retries = 0
    while(not logged_on):
        sleep(5)
        logged_on = get(f'Bot/{bot}')
        retries += 1
        if(retries > 3):
            log(f'No se ha podido conectar el bot {bot}')
            return 1
    with open('test.json', 'w') as f:
        json.dump(logged_on.json(), f)

    log(f'Bot {bot} conectado correctamente')

    cmd(f'pause {bot}')
    cmd(f'start {bot}')

    while(True):
        log(f'Buscando juegos con cromos restantes para {bot}...')
        cmd(f'resume {bot}')
        sleep(10)
        cmd(f'pause {bot}')

        games_to_farm = get(
            f'Bot/{bot}').json()['Result'][bot]['CardsFarmer']['GamesToFarm']
        hours_played = max([games_to_farm[i]['HoursPlayed']
                           for i in range(len(games_to_farm))], default=0)
        remaining_cards = sum([int(games_to_farm[i]['CardsRemaining'])
                              for i in range(len(games_to_farm))])
        appids = [games_to_farm[i]['AppID'] for i in range(len(games_to_farm))]

        if(len(appids) != 0):
            if(hours_played >= 3):
                log(f'Se encontraron {len(appids)} juegos para farmear, {str(remaining_cards)} cromos restantes')
                log(f'Farmeando {len(appids[:32])} juegos por 5 minutos')
                cmd(f'play {bot} {",".join(list(map(str,appids[:32])))}')
                sleep(300)
            else:
                log(f'Ningun juego llegó a las 3 horas aún')
                remaining_time_hours = 3 - hours_played
                remaining_time_minutes = remaining_time_hours * 60
                remaining_time_seconds = remaining_time_minutes * 60
                if remaining_time_hours < 1:
                    log(
                        f'Farmeando {len(appids[:31])} juegos por {str(round(remaining_time_minutes))} minutos')
                else:
                    log(
                        f'Farmeando {len(appids[:31])} juegos por {str(round(remaining_time_hours, 1))} horas')
                cmd(f'play {bot} {",".join(list(map(str,appids[:32])))}')
                sleep(remaining_time_seconds)
        else:
            log(f'No hay juegos para farmear en {bot}')
            break

        log('Pausando por 20 segundos')
        cmd(f'pause {bot}')
        sleep(20)

        for appid in appids:
            log(f'Farmeando {appid} por 7 segundos...')
            cmd(f'play {bot} {appid}')
            sleep(7)

        if(ismain == False):
            cmd(f'loot {bot}')


def wait_for_threads(threads: list[threading.Thread]):
    for thread in threads:
        thread.join()
    log('No quedan cromos por farmear. Presione cualquier tecla para volver a Haze')
    try:
        cmd('exit')
    except:
        pass
