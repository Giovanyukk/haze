El archivo README corresponde a la ultima versión del código, no de compilación

# Haze

Una herramienta para monitorear el retorno esperado de la compra de juegos y venta de cromos en la plataforma Steam.

## Integración con Steam
La lista de juegos es obtenida directamente de **Steam**.
Adicionalmente, si se habilita la *[Clave de Web API de Steam](https://steamcommunity.com/dev/apikey)*, puede utilizar la opción para omitir los juegos que ya se encuentran en la biblioteca.

## Integración con Steam Desktop Authenticator
La autenticación en 2 factores puede automatizarse si se coloca el archivo de secretos generado por [SDA](https://github.com/Jessecar96/SteamDesktopAuthenticator) en la carpeta donde está el ejecutable, con el nombre **2FA.maFile**

## Integración con ArchiSteamFarm
Este software puede ser utilizado para implementar el algoritmo rápido de IdleMaster sobre ArchiSteamFarm. Las instrucciones de uso se detallan a continuación:

1. Ejecutar ArchiSteamFarm y configurarlo (Las cuentas ya deben estar agregadas)
2. Ejecutar Haze y seleccionar la opción "ArchiSteamFarm"
3. Colocar los nombres asignados a los bots en ASF. Si es mas de uno, separarlos con comas. Aceptar con la tecla enter
4. Haze debería conectarse a ArchiSteamFarm mediante la API que brinda este programa. Si la conexión fue exitosa, será notificado en la consola de Haze

Haze primero esperará el tiempo necesario para que los juegos lleguen a las 3 horas y luego comenzará el algoritmo rápido.

## Modo de uso

El ejecutable debe ser colocado en un directorio propio, ya que en este se guardarán los archivos de configuración y la base de datos.

En el primer uso se solicitara el nombre de usuario y contraseña de Steam, los cuales se guardaran en el archivo **user.json**. Si se desea iniciar sesión con otro usuario, este archivo debe ser eliminado.

## Compilación

Compilar con Python 3.10

### Windows
	python -m pip install -r .\requirements.txt
	pyinstaller -i .\logo.ico --clean --onefile .\source\Haze.py --hidden-import=xlsxwriter

### Linux
	python -m pip install -r ./requirements.txt
	pyinstaller --clean --onefile ./source/Haze.py --hidden-import=xlsxwriter  

El ejecutable será guardado en la carpeta *dist*
