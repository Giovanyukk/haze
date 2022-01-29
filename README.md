El archivo README corresponde a la ultima versión del código, no de compilación

# Haze

Una herramienta para monitorear el retorno esperado de la compra de juegos y venta de cromos en la plataforma Steam.  

## Integración con Steam
Se puede utilizar la opcion **2** para generar una lista de juegos con precio menor a ARS$ 16. Esta lista es obtenida directamente de **Steam**.
Adicionalmente, si se habilita la *[Clave de Web API de Steam](https://steamcommunity.com/dev/apikey)*, puede utilizar la opción para omitir los juegos que ya se encuentran en la biblioteca.

## Integración con Steam Desktop Authenticator
La autenticación en 2 factores puede automatizarse si se coloca el archivo de secretos generado por [SDA](https://github.com/Jessecar96/SteamDesktopAuthenticator) en la carpeta donde está el ejecutable, con el nombre **2FA.maFile**

## Modo de uso

El ejecutable debe ser colocado en un directorio propio, ya que en este se guardarán los archivos de configuración y la base de datos.

En el primer uso se solicitara el nombre de usuario y contraseña de Steam, los cuales se guardaran en el archivo **user.json**. Si se desea iniciar sesión con otro usuario, este archivo debe ser eliminado.

## Compilación

Compilar con Python 3.10

`python -m pip install -r .\requirements.txt`

`pyinstaller -i .\logo.ico --clean --onefile .\source\Haze.py`

El ejecutable será guardado en la carpeta *dist*

[![Invitame un cafecito](https://cdn.cafecito.app/imgs/buttons/button_1.svg)](https://cafecito.app/enzosanchezc)
