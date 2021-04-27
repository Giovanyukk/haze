# Haze

Una herramienta para monitorear el retorno esperado de la compra de juegos y venta de cromos en la plataforma Steam.  

## Integración con SteamDB
Se puede utilizar la opcion **2** para generar una lista de juegos con precio menor a ARS$ 16. Esta lista es obtenida de **steamdb.info**.
Adicionalmente, si se edita el archivo **user.json** y se completan los campos **key** y **SteamID64** con la *[Clave de Web API de Steam](https://steamcommunity.com/dev/apikey)* y el *[SteamID64](https://steamidfinder.com/)* del usuario, puede utilizar la opción para omitir los juegos de la búsqueda de steamdb.info que ya se encuentran en la biblioteca.

## Integración con Steam Desktop Authenticator
La autenticación en 2 factores puede automatizarse si se coloca el archivo de secretos generado por [SDA](https://github.com/Jessecar96/SteamDesktopAuthenticator) en la carpeta donde esta el ejecutable, con el nombre **2FA.maFile**

## Modo de uso

El zip debe ser descomprimido en un directorio propio, ya que en este se guardarán los archivos de configuración y las bases de datos que se creen.

En el primer uso se solicitara el nombre de usuario y contraseña de Steam, los cuales se guardaran en el archivo **user.json**. Si se desea iniciar sesión con otro usuario, este archivo debe ser eliminado.

A partir de la version 0.7.0 es necesaria la instalacion de [Node.js](https://nodejs.org/es/) para la ejecución del programa.