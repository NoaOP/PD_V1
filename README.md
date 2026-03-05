# PD Versión 1

## Introducción
En la **Versión 1** del proyecto se resuelven los ejercicios propuestos con el fin de familiarizarnos con el código y los diferentes escenarios. Este repositorio se organiza en dos carpetas principales:

* **`C1`**: Contiene los trabajos y ejercicios realizados en C#.
* **`P1`**: Contiene los códigos y problemas resueltos en Python.

## 4.1 Escenario Local



## 4.2 Escenario Global
Para los escenarios globales se nos plantean 3 casos distintos: uno en el **Dashboard Global de Python** y otros dos que se basan en **WebApps** (utilizando protocolos MQTT y HTTP). Haciendo este apartado en clase, nos dimos cuenta de que, como había otros ordenadores a la vez utilizando los brokers y el simulador, las WebApp se liaban y se conectaban a otros ordenadores. Para solucionar esto, le añadimos un número random al nombre del broker para que siempre sea diferente y al topic le añadimos que somos el Grupo 2.


### 4.2.1 Escenario Global. Dashboard Global Python
Empezando por el Dashboard Global de Python, este tiene una interfaz muy similar al local, pero para funcionar necesita ejecutar el fichero `AutopilotService.py`. 

Durante esta fase, se resolvieron los siguientes ejercicios:

**1. El botón de parar la recepción de datos de telemetría no está funcionando. Detectar el error y corregirlo.**

Este ejercicio básicamente consiste en revisar el fichero `AutopilotService.py` y depurar un error de ejecución. Al ejecutar el script, el sistema lanzaba un error indicando que se esperaba un tipo de dato `int`, pero en su lugar estaba recibiendo un `float`.
Para resolverlo, identificamos la línea exacta que generaba el conflicto, solucionamos forzando la conversión del dato a entero mediante la función `int()` donde saltaba el error y, finalmente, tras una breve comprobación, verificamos que el botón de recepción de datos de telemetría ya se puede utilizar correctamente.
Ademas en esta funcion la funcion publish_telemetry_info esta inacabada y la acabamos de rellenar, hacemos que hasta que no pase mas de medio segundo no se vuelve a enviar, asi ayudamos a la no saturacion. 

(FOTO DASHBOARD)

**2. Los cambios de velocidad y de heading no están operativos en el dashboard. Introducir el código necesario para implementar estas funcionalidades.**

Para que las slide bars funcionen, debemos implementarlas en los dos scripts, en `DashboardGlobalPython.py` y en `AutopilotService.py`.
En `DaschboardGlobalPython.py` hace falta poner que publique y avise de que la slide bar se ha pulsado y la información correspondiente, para las dos funciones, tanto para cambiar la velocidad como para el heading.
Por otro lado, en `AutopilotService.py` debemos añadir que cuando el comando sea `changeHeading` o `changeNavSpeed` el heading o la velocidad se cambie a la debida gracias a las funciones originales de la librería dron.


### 4.2.2 Escenario Global. WebApp HTTP
Ahora empezamos con las web app, estas nos dan la posibilidad de conectarnos para controlar el dron sin tener que instalarnos nada. Primero usaremos el protocolo HTTP.

**1. El botón de aterrizar tiene un comportamiento diferente al de despegar. Hacer los cambios necesarios para que el botón también se ponga en color amarillo cuando empiece el aterrizaje y se ponga en verde cuando el dron esté en tierra.**

Para que el botón se ponga en amarillo y luego en verde, debemos en `indexHTTP.html` poner que cuando le demos al botón de aterrizar este se ponga de color amarillo. Nosotros hemos añadido que cuando el modo de vuelo cambie de `flying` a `LAND` y la altura sea menor a 0,5 m, el botón de aterrizar vuelva a cambiar a verde y el botón de despegar se quite los colores previos.

**2. Añadir un nuevo botón para realizar la operación RTL.**

Para añadir el botón de RTL, empezamos copiando el botón de aterrizaje, ya que se parecen mucho, y luego cambiaremos la función a RTL, esto lo debemos hacer en todos los scripts, ya que siempre que hay alguna referencia al botón de aterrizaje debemos copiarlo y cambiarle el nombre.

(FOTO WEB APP HTTP todo verde)


### 4.2.3 Escenario Global. WebApp MQTT
En el protocolo HTTP, la información no fluye de la forma más dinámica, por eso ahora utilizaremos MQTT para hacer la WebApp. 
Hemos resuelto los siguientes ejercicios:


**1. El botón de aterrizar tiene un comportamiento diferente al de despegar. Hacer los cambios necesarios para que el botón también se ponga en color amarillo cuando empiece el aterrizaje y se ponga en verde cuando el dron esté en tierra.**

Similar al anterior apartado, para poner el botón en amarillo al darle, tenemos que ir en `indexMQTT.html` y en la función de `aterrizarDron` ponemos que al darle se vuelva de color amarillo. Para poner que se ponga de color verde al aterrizar, hacemos como antes, añadimos que cuando el status no sea `flying`, el modo de vuelo sea `LAND` y la altura sea inferior a 0,5 m, el botón se pone en verde, además, el botón de despegar le quitamos el color.


**2. Añadir un nuevo botón para realizar la operación RTL.**

Similar a antes, para crear el botón de RTL, copiamos las funciones y los sitios donde pone aterrizar para cambiarlos a RTL, las dos funciones se parecen mucho y trabajan de forma similar. Así tenemos un botón que hace RTL y al darle se pone en amarillo, para luego ponerse en verde una vez aterrizado.


**3. Añadir los elementos necesarios para poder cambiar el heading del dron, igual que puede hacerse en las aplicaciones descritas en apartados anteriores.**

Primero añadimos como tal la slide bar para poder cambiar el heading, pero para que funcione debemos añadir una función que coja el valor donde está la slide bar y lo publique, todo esto en `indexMQTT.html`. Como en `AutopilotService.py` ya habíamos añadido las funciones y código necesario para hacer el change heading en el `DashboardGlobalPython.py` no tenemos que añadir nada mas.


(FOTO WEBAPP MQTT heading)

## 4.3 Video Streaming



## 4.4 Reconocimiento de Objetos




