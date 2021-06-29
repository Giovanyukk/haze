import requests
from datetime import datetime
from time import sleep

URL = 'http://127.0.0.1:1242'


def log(data: str):
    print('[' + datetime.now().strftime('%d/%m/%y %H:%M') + ']', end=' ')
    print(data)


def get(endpoint: str):
    headers = {'Authentication': '', 'accept': 'application/json'}
    uri = f'{URL}/Api/{endpoint}'
    return requests.get(uri, headers=headers)


def post(endpoint: str, data: str):
    headers = {'Authentication': '', 'accept': 'application/json',
               'Content-Type': 'application/json'}
    uri = f'{URL}/Api/{endpoint}'
    return requests.post(uri, data, headers=headers)


def cmd(data: str):
    log(f'CMD: {data}')
    post('Command', '{"Command":"' + data + '"}')


def idle_bot(bot: str):
    try:
        cmd(f'pause {bot}')
        cmd(f'start {bot}')

        while(True):
            log(f'Buscando juegos con cromos restantes...')
            cmd(f'resume {bot}')
            sleep(10)
            cmd(f'pause {bot}')

            appids = get(f'Bot/{bot}').json()['Result'][bot]['CardsFarmer']['GamesToFarm'] 
            appids = [appids[i]['AppID'] for i in range(len(appids))]
            
            if(len(appids) != 0):
                log(f'Se encontraron {len(appids)} juegos para farmear')
                log(f'Farmeando {len(appids[:31])} juegos por 5 minutos...')
                cmd(f'play {bot} {",".join(list(map(str,appids[:31])))}')
                sleep(300)
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
    except KeyboardInterrupt:
        log(f'Se ha detenido la recolección en {bot}')
        