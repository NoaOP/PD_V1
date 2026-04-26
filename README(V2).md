# PD Versión 2

## 5.1 Requisitos específicos de la versión 2

### 5.1.1 Dashboard en Python

**1. El dashboard en Python debe integrar el servicio de autopiloto y el servicio de cámara**
En la versión 2 se ha desarrollado un dashboard principal en Python llamado DashboardAll.py, que integra en una misma interfaz el control del autopiloto y la recepción de vídeo de la cámara.
El servicio de autopiloto se integra mediante la clase Dron, que proporciona las funciones necesarias para conectar con el dron, armarlo, despegar, aterrizar, ejecutar RTL, moverlo manualmente, cambiar el heading, modificar la velocidad de navegación, enviar el dron a una posición concreta mediante Go To y recibir telemetría.
Por otro lado, el servicio de cámara se integra mediante WebRTC. El dashboard incluye el botón Recibir video por WebRTC, que permite iniciar la recepción del vídeo transmitido por CameraService.py. Además, sobre este vídeo se puede activar la detección de objetos, seleccionando desde la propia interfaz qué elementos se quieren identificar.

**2. Debe poder trabajar en modo local o en modo global, según indique el usuario (quizá con un botón)**
El dashboard permite trabajar en dos modos de funcionamiento: modo local y modo global. Esta selección se realiza directamente desde la parte superior de la interfaz mediante los botones Mode Local y Mode Global. Además, el propio dashboard muestra en todo momento el modo activo mediante una etiqueta.

**3. Si se pone marcha en modo local entonces debe activar el servicio de autopiloto y el servicio de cámara**
Cuando el dashboard se inicia en modo local, se activan automáticamente los dos servicios principales necesarios para operar el dron: el servicio de autopiloto y el servicio de cámara.

El servicio de autopiloto se ejecuta mediante el archivo AutopilotService.py, que se encarga de gestionar la conexión con el dron y de procesar los comandos de control. Por otro lado, el servicio de cámara se ejecuta mediante CameraService.py, que permite capturar y transmitir el vídeo por WebRTC.

En la interfaz se puede comprobar el estado de estos servicios mediante el mensaje situado en la parte inferior central. En la imagen aparece:

Autopilot: OBERT | Camera: OBERT

**4. Siempre tiene que haber una (y solo una) instancia del dashboard que se ponga en marcha en modo local, en el portátil que tenga la radio de telemetría y el receptor del vídeo del dron**
En esta versión, el modo local solo debe ejecutarse en el portátil que tiene la conexión directa con el dron, es decir, el ordenador que dispone de la radio de telemetría y del receptor de vídeo. Para evitar que se abran varias interfaces locales al mismo tiempo, el programa incorpora un sistema de bloqueo de instancia única.

Este sistema funciona mediante un mutex, que puede entenderse como un “candado” del sistema operativo. Cuando se abre el dashboard en modo local, el programa intenta crear ese candado. Si no existe todavía, significa que no hay ninguna otra instancia local abierta, por lo que el dashboard puede continuar funcionando normalmente. En cambio, si el candado ya existe, el programa interpreta que ya hay otro dashboard local en marcha y no permite abrir una segunda instancia.

```python
def switch_mode(self, mode):
    if self.mode == mode:
        return
    if mode == "local" and not self.local_lock_owned:
        if not _acquire_single_instance_lock():
            messagebox.showwarning(
                "Mode local ocupat",
                "Ja hi ha una instancia en mode local oberta."
            )
            return
        self.local_lock_owned = True
```
Esta parte hace que si el usuario intenta entrar en modo local y ya hay otra instancia local abierta, se muestra un aviso y no le deja entrar en modo local.

**5. Pueden ponerse en marcha una o varias instancias del dashboard en modo global que interactuarán con el servicio de autopiloto por MQTT y con el servicio de cámara por WebRTC**
En modo global, el dashboard crea un cliente MQTT y se conecta al broker mediante WebSockets. Además, se suscribe a los tópicos donde el `AutopilotService` publica la telemetría y los eventos de estado. De esta manera, el dashboard global puede recibir información del dron sin estar conectado físicamente a él.
```python
self.global_client = mqtt.Client("InterfazGlobal", transport="websockets")
self.global_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
self.global_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
self.global_client.subscribe("Grup2/autopilotServiceDemo/interfazGlobal/#")
self.global_client.loop_start()
```
El `AutopilotService` también está conectado al broker MQTT y se suscribe al patrón de tópicos `+/autopilotServiceDemo/#`. El símbolo `+` permite recibir mensajes procedentes de diferentes orígenes, por lo que varias instancias del dashboard en modo global pueden enviar comandos al mismo servicio de autopiloto.
```python
client = mqtt.Client("autopilotServiceDemo" + n, transport="websockets")
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
client.subscribe("+/autopilotServiceDemo/#")
client.loop_forever()
```
La interacción con el servicio de cámara se realiza mediante WebRTC. El archivo `CameraService.py` captura el vídeo de la cámara y crea una conexión WebRTC para enviarlo al dashboard. Así, las instancias en modo global pueden recibir el vídeo del dron mientras los comandos de control se envían por MQTT.

**6. Tanto en modo local como en modo global, el dashboard debe mostrar al usuario un mapa geolocalizado que muestre la posición en la que está el dron en cada momento, igual que lo hace Mission Planner**


**7. El usuario debe poder interactuar con el dron a través del mapa, por ejemplo clicando en un punto del mapa para que el dron se dirija a ese punto**


**8. Tanto en modo local como en modo global el usuario debe poder solicitar el reconocimiento de objetos en el stream de video. Incluso debe poder solicitar que se reconozcan varios tipos de objetos simultaneamente, seleccionados de entre un subconjunto del data set de COCO**
El dashboard permite activar el reconocimiento de objetos sobre el vídeo recibido por WebRTC. Para ello, la interfaz incluye un apartado llamado Deteccion de objects, donde el usuario puede seleccionar uno o varios objetos de un subconjunto del dataset COCO. En el código, este subconjunto se define así:

COCO_SUBSET = [
    ("Persona", 0),
    ("Perro", 16),
    ("Banana", 46),
    ("Naranja", 49),
    ("Pizza", 53),
    ("Pastel", 55),
    ("Reloj", 74),
]
```python
def _get_selected_object_ids(self, mode):
    vars_map = self.local_detect_vars if mode == "local" else self.global_detect_vars
    selected = {obj_id for obj_id, var in vars_map.items() if var.get() == 1}

    if mode == "local":
        self.local_selected_objects = selected
    else:
        self.global_selected_objects = selected

    return selected
```
Esta función comprueba qué casillas están activadas y devuelve el conjunto de identificadores COCO seleccionados.

**9. El servicio de cámara debe suministrar el stream de video por WebRTC a todos los módulos que lo soliciten**
En el CameraService.py, la clase CustomVideoStreamTrack lee continuamente frames de la cámara y los prepara para enviarlos por WebRTC:
```python
class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id=0):
        super().__init__()
        self.cap = cv2.VideoCapture(camera_id)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
```
Además, el servicio también escucha peticiones mediante MQTT para poder suministrar vídeo a la web app. Cuando recibe el comando startVideo, inicia una conexión WebRTC y publica una oferta de vídeo para que el cliente pueda responder y establecer la conexión.
CameraService puede atender las peticiones de vídeo procedentes de distintos módulos, como el dashboard Python o la interfaz web. El vídeo se transmite mediante WebRTC, mientras que MQTT se utiliza para iniciar la conexión con los clientes web.

### 5.1.2 Dashboard en C#

**1.Debe funcionar en modo global, es decir, haciendo peticiones al servicio de autopiloto por MQTT**


**2.Debe mostrar al usuario un mapa geolocalizado con la ubicación del dron en cada momento**

El dashboard en C# incorpora un mapa geolocalizado para mostrar la posición actual del dron durante el vuelo. Este mapa está implementado en el archivo MapForm.cs, donde se crea una ventana independiente llamada Mapa del dron.
Para mostrar el mapa, se utiliza un componente WebBrowser dentro del formulario de C#. Dentro de este navegador se carga una página HTML con la librería Leaflet y mapas de OpenStreetMap. Esta parte permite representar el entorno geográfico y colocar un marcador sobre la posición del dron.

La posición del dron se actualiza a partir de los datos de telemetría recibidos. En Form1.cs, la función ProcesarTelemetria extrae la latitud y la longitud del dron y si el mapa está abierto llama a mapForm.UpdateLocation(lat, lon) para actualizar su posición en el mapa.
Después, en MapForm.cs, la función UpdateLocation envía las nuevas coordenadas al mapa y ejecuta la función JavaScript updateMarker, que mueve el marcador del dron y centra su posición.

<img width="400" height="300" alt="Captura de pantalla 2026-04-26 170441" src="https://github.com/user-attachments/assets/e3982c4a-a3e9-4422-919b-be279da4fb31" />


**3.El usuario debe poder clicar en el mapa para hacer que el dron se dirija a ese punto**
El dashboard en C# permite que el usuario interactúe directamente con el mapa geolocalizado. Además de mostrar la posición actual del dron, el mapa permite seleccionar un punto de destino haciendo clic sobre él.

Cuando el usuario clica sobre una posición del mapa, el programa obtiene las coordenadas geográficas de ese punto, es decir, la latitud y la longitud. A continuación, estas coordenadas se envían al dashboard para que pueda ordenar al dron desplazarse hacia esa ubicación.

De esta forma, el usuario no necesita introducir manualmente las coordenadas del destino, sino que puede seleccionar visualmente el punto sobre el mapa. Esto hace que la navegación sea más intuitiva y parecida al funcionamiento de Mission Planner, donde el operador puede controlar el movimiento del dron a partir de posiciones geográficas.

El funcionamiento del mapa geolocalizado y la navegación mediante clic se muestra en el siguiente vídeo:
https://drive.google.com/file/d/10JzNUpuTVQDBkeTfOPZDLzyI7tp5GlI8/view?usp=drive_link

**4.Debe mostrar el stream de video que se recibe por WebRTC del servicio de cámara. Para implementar este requisito es muy importante mirar lo que se explica en el apartado 5.2**


**5.El usuario debe poder solicitar el reconocimiento de uno o varios objetos de entre un subconjunto del data ser de COCO**


**6.Debe permitir capturar imagenes del stream de video (hacer fotos) y guardarlas, de manera que el usuario pueda verlas cuando quiera en un formulario que muestre una galería de las fotos tomadas**


### 5.1.3 WebApp

**1.Debe tener una pestaña que muestre los botones para controlar el dron, otra para mostrar un mapa geolocalizado con la posición del dron en cada momento y otra con el stream de video que se recibe del dron**
La WebApp está organizada en tres pestañas principales: Control, Mapa y Video. Esta estructura permite separar las funciones principales de la aplicación y facilita su uso.
En la pestaña Control, el usuario puede enviar comandos al dron, como conectar, despegar, aterrizar, ejecutar RTL, modificar el heading, cambiar la velocidad, mover el dron mediante botones direccionales y activar el control por voz. También se muestra información básica como la altitud actual del dron.
En la pestaña Mapa, se muestra un mapa geolocalizado basado en Leaflet y OpenStreetMap, donde se puede visualizar la posición del dron a partir de la telemetría recibida.
En la pestaña Video, el usuario puede iniciar y detener el stream de vídeo recibido desde el servicio de cámara. Esta pestaña incluye una zona reservada para visualizar en tiempo real la imagen capturada por el dron.
Por tanto, este requisito queda cumplido porque la WebApp integra en una misma interfaz las tres funciones principales: control del dron, visualización de mapa y recepción de vídeo.
En las imágenes se puede ver la distribución de la web:

<img style="width:auto; height:200px" alt="Captura de pantalla 2026-04-26 174239" src="https://github.com/user-attachments/assets/2a7795c2-ba4e-45f3-94a9-f1d60c792a8b" />

<img style="width:auto; height:200px" alt="Captura de pantalla 2026-04-26 174257" src="https://github.com/user-attachments/assets/f0326b57-e6b7-4598-ad00-c70a2bcd1320" />

<img style="width:auto; height:100px img-align:center" alt="Captura de pantalla 2026-04-26 174311" src="https://github.com/user-attachments/assets/76b16c5a-8730-41fe-a6f6-766a17b64f3b" />


**2.Debe comunicarse con el servicio de autopiloto por MQTT y con el servicio de cámara por WebRTC**


**3.El usuario debe poder controlar el dron mediante la voz, diciendo palabras clave como: "Despega", "Aterriza", "Vuela hacia el Norte", etc. Para implementar este requisito es muy importante mirar lo que se explica en el apartado 5.2**

