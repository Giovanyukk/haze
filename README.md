# Project Haze (WIP Branch)

Una herramienta para monitorear la rentabilidad de la compra de juegos y venta de cromos en la plataforma Steam.

Los juegos a monitorear se deben agregar mediante el appID del juego. Varios juegos pueden ser agregados simultaneamente colocando sus respectivos appIDs separados por comas.

Se puede agregar automaticamente una busqueda entera en steamdb.info, descargando la pagina una vez filtrados los juegos y guardando el archivo html en la carpeta database con el nombre steamdb.html. Luego debe seleccionarse la opcion -2 al ingresar AppIDs. Para filtrar los juegos que ya se encuentran en la biblioteca del usuario, se debe agregar en el codigo fuente el SteamID64 y la webAPI key y posteriormente se habilitará esta opcion de forma automatica.

El archivo README se irá modificando a lo largo del desarrollo del proyecto
