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


**9. El servicio de cámara debe suministrar el stream de video por WebRTC a todos los módulos que lo soliciten**

### 5.1.2 Dashboard en C#

