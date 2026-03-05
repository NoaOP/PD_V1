############  INSTALAR ##############
# paho-mqtt, version 1.6.1
#####################################
import random

import paho.mqtt.client as mqtt
import json
from dronLink.Dron import Dron
import random
import time

active_origins = set()
last_telemetry_time = 0

# esta función sirve para publicar los eventos resultantes de las acciones solicitadas
def publish_event (event):
    global sending_topic, client
    client.publish(sending_topic + '/'+event)


def publish_telemetry_info(telemetry_info):
    global active_origins, client, last_telemetry_time

    # 1. FRENO: Si no ha pasado al menos medio segundo (0.5s), ignoramos el dato para no saturar
    current_time = time.time()
    if current_time - last_telemetry_time < 0.5:
        return
    last_telemetry_time = current_time

    # 2. BROADCAST: Enviamos la telemetría a TODAS las interfaces que estén conectadas
    for origin in active_origins:
        topic = "Grup2/autopilotServiceDemo/" + origin + "/telemetryInfo"
        client.publish(topic, json.dumps(telemetry_info))

def on_message(cli, userdata, message):
    global  sending_topic, client
    global dron
    # el mensaje que se recibe tiene este formato:
    #    "origen"/autopilotServiceDemo/"command"
    # tengo que averiguar el origen y el command
    splited = message.topic.split("/")
    origin = splited[0] # aqui tengo el nombre de la aplicación que origina la petición
    command = splited[2] # aqui tengo el comando

    active_origins.add(origin)  # Guardamos quién nos acaba de hablar


    sending_topic = "Grup2/autopilotServiceDemo/" + origin # lo necesitaré para enviar las respuestas

    if command == 'connect':
        connection_string = 'tcp:127.0.0.1:5763'
        baud = 115200
        dron.connect(connection_string, baud, freq=10)
        publish_event('connected')

    if command == 'arm_takeOff':
        if dron.state == 'connected':
            print ('vamos a armar')

            try:
                payload_str = message.payload.decode("utf-8")
                if payload_str.strip():  # Si el mensaje no está vacío
                    altura_deseada = int(float(payload_str))
                else:
                    altura_deseada = 5  # Entero por defecto
            except (ValueError, TypeError):
                altura_deseada = 5  # Entero por defecto si envían letras

            # 2. Reemplazamos el 5 fijo por 'altura_deseada', conservando tus callbacks originales
            dron.arm()
            print('vamos a despegar')
            dron.takeOff(altura_deseada, blocking=False, callback=publish_event, params='flying')


    if command == 'go':
        if dron.state == 'flying':
            direction = message.payload.decode("utf-8")
            dron.go(direction)

    if command == 'Land':

        # operación no bloqueante. Cuando acabe publicará el evento correspondiente
        dron.Land(blocking=False, callback=publish_event, params='landed')

    if command == 'RTL':

        # operación no bloqueante. Cuando acabe publicará el evento correspondiente
        dron.RTL(blocking=False, callback=publish_event, params='atHome')

    if command == 'startTelemetry':
        # indico qué función va a procesar los datos de telemetría cuando se reciban
        dron.send_telemetry_info(publish_telemetry_info)

    if command == 'stopTelemetry':
        dron.stop_sending_telemetry_info()

    if command == 'changeHeading':
        if dron.state == 'flying':
            grados = int(message.payload.decode("utf-8"))
            dron.changeHeading(grados)

    if command == 'changeNavSpeed':
        if dron.state == 'flying':
            velocidad = float(message.payload.decode("utf-8"))
            dron.changeNavSpeed(velocidad)


def on_connect(client, userdata, flags, rc):
    global connected
    if rc==0:
        print("connected OK Returned code=",rc)
        connected = True
    else:
        print("Bad connection Returned code=",rc)


dron = Dron()
n = str(random.randint(0,10000))
client = mqtt.Client("autopilotServiceDemo"+ n, transport="websockets")

# me conecto al broker publico y gratuito
broker_address = "broker.hivemq.com"
broker_port = 8000

client.on_message = on_message
client.on_connect = on_connect
client.connect (broker_address,broker_port)

# me subscribo a todos los mensajes cuyo destino sea este servicio
client.subscribe('+/autopilotServiceDemo/#')
print ('AutopilotServiceDemo esperando peticiones')
client.loop_forever()

