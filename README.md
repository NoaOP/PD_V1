# PD Versión 1

## Introducción
En la **Versión 1** del proyecto se resuelven los ejercicios propuestos con el fin de familiarizarnos con el código y los diferentes escenarios. Este repositorio se organiza en dos carpetas principales:

* **`C1`**: Contiene los trabajos y ejercicios realizados en C#.
* **`P1`**: Contiene los códigos y problemas resueltos en Python.

## 4.1 Escenario Local



## 4.2 Escenario Global
Para los escenarios globales se nos plantean 3 casos distintos: uno en el **Dashboard Global de Python** y otros dos que se basan en **WebApps** (utilizando protocolos MQTT y HTTP). 

(PONER LO DE RANDOM Y EL GRUPO)

### 4.2.1 Escenario Global. Dashboard Global Python
Empezando por el Dashboard Global de Python, este tiene una interfaz muy similar al local, pero para funcionar necesita ejecutar el fichero `AutopilotService.py`. 

Durante esta fase, se resolvieron los siguientes ejercicios:
**1. El botón de parar la recepción de datos de telemetría no está funcionando. Detectar el error y corregirlo.**
Este ejercicio básicamente consiste en revisar el fichero `AutopilotService.py` y depurar un error de ejecución. Al ejecutar el script, el sistema lanzaba un error indicando que se esperaba un tipo de dato `int`, pero en su lugar estaba recibiendo un `float`.
Para resolverlo, identificamos la línea exacta que generaba el conflicto, solucionamos forzando la conversión del dato a entero mediante la función `int()` donde saltaba el error y finalmente tras una breve comprobación, verificamos que el botón de recepción de datos de telemetría ya se puede utilizar correctamente.
Ademas en esta funcion la funcion publish_telemetry_info esta inacabada y la acabamos de rellenar, hacemos que hasta que no pase mas de medio segundo no se vuelve a enviar, asi ayudamos a la no saturacion. 

(FOTO DASHBOARD)

**2. Los cambios de velocidad y de heading no están operativos en el dashboard. Introducir el código necesario para implementar estas funcionalidades.**
Para que las slide bar funcionen debemos implementearlas en los dos scrripts, en `DashboardGlobalPython.py` y en `AutopilotService.py`.
En `DaschboardGlobalPython.py` hace falta poner que publique y avise de que la slide bar se ha pulsado y la informacion correspondiente, para las dos funciones tanto para cambiar la velocidad como para el heading.
Por otro lado en `AutopilotService.py` debemos añadir que cuando el comando sea `changeHeading` o `changeNavSpeed` el heading o la velocidad se cambie a la debida gracias a las funciones originales de la libreria dron


### 4.2.2 Escenario Global. WebApp HTTP
Ahora empezamos con las web app, estas nos dan la possibilidad de conectarnos para controlar el dron sin tener que instalarnos nada. Primero usaremos el protocolo HTTP.

**1. El botón de aterrizar tiene un comportamiento diferente al de despegar. Hacer los cambios necesarios para que el botón también se ponga en color amarillo cuando empiece el aterrizaje y se ponga en verde cuando el dron esté en tierra.**
Para que el boton se ponga en amaraillo y luego en verde debemos en `indexHTTP.html` ponemos que cuando le demos al boton de aterizar este se ponga de color amarillo, nosotros hemos añadido que cuando el modo de vuelo cambie de `flying` a `LAND` y la altura sea menor a 0,5 m el boton de aterizar vuelva a cambiar a verde y el boton de despegar se quite los colores previos.

**2. Añadir un nuevo botón para realizar la operación RTL.**
Para añadir el boton de RTL empezamos copiando el boton de aterizaje, ya que se parecen mucho y luego cambiaremos la funcion a RTL, esto lo debemos hacer en todos los scripts ya que siempre que hay alguna referencia al boton de aterizaje debemos copiarlo y cambiarle el nombre.

(FOTO WEB APP HTTP todo verde)


### 4.2.3 Escenario Global. WebApp MQTT




## 4.3 Video Streaming



## 4.4 Reconocimiento de Objetos




