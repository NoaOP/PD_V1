# PD Versión 1

## Introducción
En la **Versión 1** del proyecto se resuelven los ejercicios propuestos con el fin de familiarizarnos con el código y los diferentes escenarios. Este repositorio se organiza en dos carpetas principales:

* **`C1`**: Contiene los trabajos y ejercicios realizados en C#.
* **`P1`**: Contiene los códigos y problemas resueltos en Python.

## 4.1 Escenario Local
En el escenario local, la estación de tierra está conectada directamente al dron y es el propio programa quien envía las órdenes utilizando las librerías proporcionadas. En esta parte del proyecto hemos trabajado con dos versiones distintas de la estación de tierra: una desarrollada en Python y otra en C#. En ambos casos, el objetivo ha sido comprender el funcionamiento básico de la interfaz, revisar el código proporcionado y completar los ejercicios propuestos para añadir o corregir funcionalidades.


### 4.1.1 Escenario Global. Dashboard Global Python
En primer lugar, trabajamos con el fichero **DashboardLocalPython.py**, que implementa una interfaz gráfica en Tkinter para controlar el dron en un entorno local. Esta interfaz incluye botones para conectar con el dron, despegar, aterrizar, ejecutar un RTL, consultar datos de telemetría y controlar la navegación en distintas direcciones como se muestra en la imagen.


<img width="270" height="414" alt="image" src="https://github.com/user-attachments/assets/180ac4d0-9f79-40e1-8804-8120ce5282e4" />


A partir de este código base, se resolvieron los ejercicios planteados:


**1. Modificar el código para que las operaciones de aterrizaje y RTL tengan un comportamiento similar a la operación de despegue (llamada no bloqueante).**


Inicialmente, las funciones de aterrizaje y RTL estaban programadas de forma bloqueante, lo que provocaba que la interfaz gráfica quedase congelada mientras el dron completaba la maniobra. Para corregirlo, se modificó el código para que ambas operaciones funcionaran con llamadas no bloqueantes, del mismo modo que el despegue. De esta forma, la interfaz sigue activa durante la maniobra y el usuario puede seguir viendo la telemetría o interactuando con la aplicación mientras el dron aterriza o regresa al punto de origen.


(VIEDO DE COM FUNCIONA EL RTL I ENCARA HI HA TELEMETRIA?)


**2. Incorporar al bloque de datos de telemetría algún dato más.**
Además de los datos que ya mostraba el dashboard, se añadieron nuevos valores de telemetría para ampliar la información disponible en pantalla. Se incorporaron datos adicionales como el estado del dron y su velocidad, haciendo la interfaz más útil a la hora de supervisar el comportamiento del vehículo durante el vuelo.


(FOTITO DE LA TELEMETRIA)


**3. Añadir un botón más para realizar una nueva función.**

También se añadió una nueva funcionalidad mediante un botón extra en la interfaz: la función Go To. Esta función pide al usuario una latitud, una longitud y una altitud y, al pulsar el botón, el dron se dirige automáticamente hacia esa posición indicada. Para implementarlo, se creó el nuevo botón en la interfaz, se añadieron los campos necesarios para introducir las coordenadas y la altura, y se vinculó todo con la función correspondiente de la librería `DronLink`. De este modo, la aplicación incorpora una orden de navegación más avanzada que permite enviar el dron directamente a un punto concreto.

(VIDEO)

### 4.1.2 Escenario Global. Dashboard Global Python

La segunda parte del escenario local se desarrolló en C#, utilizando la aplicación de la carpeta DashboardLocalCsharp, creada con Windows Forms. Esta versión ofrece una interfaz muy similar a la de Python, aunque incorpora algunas diferencias, como la posibilidad de indicar la altura de despegue y mostrar también la posición del dron en latitud y longitud como se muestra en la imagen.

<img width="459" height="403" alt="image" src="https://github.com/user-attachments/assets/e560f507-28b5-4b79-897b-e33b41a9384d" />


Sobre esta base, se realizaron los ejercicios propuestos:

**1. Hacer que el usuario pueda establecer la altura de despegue con una barra de desplazamiento, igual que el heading o la velocidad.**

Se modificó la interfaz para que la altura de despegue no tuviera que introducirse manualmente, sino que pudiera ajustarse mediante una barra deslizante, igual que otros parámetros como el heading o la velocidad. Su funcionamiento puede observarse en el siguiente vídeo:

https://drive.google.com/file/d/1N8Hu4X_CTP35p9wE4oufnds0ANmOSBUR/view?usp=sharing

**2. Añadir algún dato más a los datos de telemetría.**

Se amplió también la información mostrada en pantalla incorporando un nuevo dato de telemetría: la velocidad ground aproximada del dron. De este modo, además de los valores básicos, el usuario puede visualizar información extra relevante para seguir el estado del dron durante la operación. Esta nueva información se muestra también en el siguiente vídeo:

https://drive.google.com/file/d/1q-8HAw81WQCiybMOLZxCH2JSykyGLKtZ/view?usp=sharing

**3. Incorporar un botón para realizar alguna nueva función.**

Finalmente, se añadió un nuevo botón con una funcionalidad adicional pensada para situaciones de emergencia. Esta nueva función hace que, independientemente del punto en el que se encuentre el dron, ascienda automáticamente 5 metros de altitud al pulsar el botón. El objetivo de esta acción es aumentar rápidamente la separación vertical en caso de que el dron pueda chocar con un obstáculo cercano. De este modo, se amplían las capacidades del dashboard en C# incorporando una orden útil de seguridad. El funcionamiento de esta nueva función puede observarse en el siguiente vídeo:

https://drive.google.com/file/d/1TdIIdKZL2Lew9zLa5RKhy9QaKaxGhT5I/view?usp=sharing


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




