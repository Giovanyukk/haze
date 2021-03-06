# Haze

Una herramienta para monitorear el retorno esperado de la compra de juegos y venta de cromos en la plataforma Steam.  

Los juegos a analizar se deben agregar mediante el AppID del juego. Varios juegos pueden ser agregados simultáneamente colocando sus respectivos AppIDs separados por comas.

## *Integración con SteamDB*
Si se realiza una búsqueda en steamdb.info, se descarga como página .html y se guarda el archivo en la carpeta **database** con el nombre **steamdb.html**, puede utilizarse la opción **-2** para cargar automáticamente todos los juegos de la búsqueda.
Adicionalmente, si se edita el archivo **user.json** y se completan los campos **key** y **SteamID64** con la *[Clave de Web API de Steam](https://steamcommunity.com/dev/apikey)* y el *[SteamID64](https://steamidfinder.com/)* del usuario, puede utilizar la opción para omitir los juegos de la búsqueda de steamdb.info que ya se encuentran en la biblioteca.

## *Integración con Steam Desktop Authenticator*
La autenticación en 2 factores puede automatizarse si se coloca el archivo de secretos generado por [SDA](https://github.com/Jessecar96/SteamDesktopAuthenticator) en la carpeta donde esta el ejecutable, con el nombre **2FA.maFile**

## *Modo de uso*

El ejecutable debe ser guardado en un directorio propio, ya que en este se guardarán los archivos de configuración y las bases de datos que se creen.

En el primer uso se solicitara el nombre de usuario y contraseña de Steam, los cuales se guardaran en el archivo **user.json**. Si se desea iniciar sesión con otro usuario, este archivo debe ser eliminado.