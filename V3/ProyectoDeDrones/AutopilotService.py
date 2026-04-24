############  INSTALAR ##############
# paho-mqtt, version 1.6.1
#####################################

import random
import os
import time
import json
import threading

import paho.mqtt.client as mqtt
from P2.ProyectoDeDrones.dronLink.Dron import Dron

active_origins    = set()
last_telemetry_time = 0

# MAVProxy endpoint per a l'AutopilotService (port diferent del dashboard local)
MAVPROXY_AUTOPILOT_ENDPOINT = os.getenv("MAVPROXY_AUTOPILOT_ENDPOINT", "udp:127.0.0.1:14551")
MAVPROXY_AUTOPILOT_BAUD     = int(os.getenv("MAVPROXY_AUTOPILOT_BAUD", "115200"))

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "dronseetac.upc.edu")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "8000"))
MQTT_USERNAME    = os.getenv("MQTT_USERNAME", "dronsEETAC")
MQTT_PASSWORD    = os.getenv("MQTT_PASSWORD", "mimara1456.")


def publish_event(origin, event):
    """Publica un event a totes les interfícies que han interaccionat."""
    # global active_origins, client
    # for origin in active_origins:
    #     topic = "Grup21/autopilotServiceDemo/" + origin + "/" + event
    #     client.publish(topic)
    global client

    topic = "Grup21/autopilotServiceDemo/" + origin + "/" + event
    client.publish(topic)


def publish_telemetry_info(telemetry_info):
    """Publica telemetria amb fre de 0.5s per no saturar el broker."""
    global active_origins, client, last_telemetry_time
    current_time = time.time()
    if current_time - last_telemetry_time < 0.5:
        return
    last_telemetry_time = current_time
    for origin in active_origins:

        topic = "Grup21/autopilotServiceDemo/" + origin + "/telemetryInfo"
        client.publish(topic, json.dumps(telemetry_info))


def _on_connected_callback():
    """Cridat per dronLink quan la connexió MAVProxy s'estableix (no bloquejant)."""
    publish_event("connected")
    print("Dron connectat correctament via MAVProxy")

def do_triangle(origin):
    global dron
    try:
        if dron.state != "flying":
            return
        dron.go("North")
        time.sleep(2)

        dron.go("SouthEast")
        time.sleep(2)

        dron.go("SouthWest")
        time.sleep(2)

        dron.go("Stop")
        publish_event(origin, "triangleDone")

    except Exception as e:
        print(f"Error haciendo triángulo: {e}")
        try:
            dron.go("Stop")
        except:
            pass

def on_message(cli, userdata, message):
    global active_origins, client, dron

    splited = message.topic.split("/")
    if len(splited) < 3:
        return

    origin  = splited[0]
    command = splited[2]

    active_origins.add(origin)

    if command == "connect":
        if dron.state != "disconnected":
            # Ja connectat: resposta immediata
            publish_event(origin,"connected")
        else:
            # Connexio no bloquejant perque vagi fluid el MQTT
            print("Conectando via MAVProxy...")
            dron.connect(
                MAVPROXY_AUTOPILOT_ENDPOINT,
                MAVPROXY_AUTOPILOT_BAUD,
                freq=4,
                blocking=False,
                callback = lambda: publish_event(origin, "connected")
            )

     # afegit per la simulacio de la web app
    elif command == 'Simulacion':
        if dron.state != "disconnected":
            publish_event(origin, "connected")
        else:
            payload_raw = message.payload.decode("utf-8")
            try:
                partes = payload_raw.split(',')
                opcion = int(partes[0])
                if opcion == 1:  # Dron Real COM
                    puerto_com = f'COM{partes[1]}'
                    print(f"Conectando a Dron Real en {puerto_com}...")
                    dron.connect(puerto_com, 57600, freq=4, blocking=False,
                                callback=lambda: publish_event(origin, 'connected'))
                elif opcion == 2:  # Simulador TCP
                    print("Conectando a Simulador TCP...")
                    dron.connect('tcp:127.0.0.1:5763', 115200, freq=4, blocking=False,

                                callback=lambda: publish_event(origin, 'connected'))
            except Exception as e:
                print(f"Error conexión Simulacion: {e}")



    elif command == "arm_takeOff":
        # Només actuar si està connectat o armat, no si ja vola
        if dron.state in ("connected", "armed"):
            try:
                payload_str = message.payload.decode("utf-8").strip()
                altura_deseada = int(float(payload_str)) if payload_str else 5
            except (ValueError, TypeError):
                altura_deseada = 5

            print(f"Armant i despegant a {altura_deseada}m")
            dron.arm()
            dron.takeOff(altura_deseada, blocking=False,
                         callback=lambda p: publish_event(origin, p), params="flying")
        elif dron.state == "flying":
            # Ja en vol: notifica igualment per sincronitzar la UI
            publish_event(origin,"flying")

    elif command == "go":
        if dron.state == "flying":
            direction = message.payload.decode("utf-8")
            dron.go(direction)


    elif command == "triangle":
        if dron.state == "flying":
            threading.Thread(
                target=do_triangle,
                args=(origin,),
                daemon=True
            ).start()



    elif command == "Land":
        if dron.state in ("flying", "armed", "connected"):
            dron.Land(blocking=False, callback=lambda p: publish_event(origin, p), params="landed")

    elif command == "RTL":
        if dron.state in ("flying", "armed", "connected"):
            dron.RTL(blocking=False, callback=lambda p: publish_event(origin, p), params="atHome")

    elif command == "startTelemetry":
        dron.send_telemetry_info(publish_telemetry_info)

    elif command == "stopTelemetry":
        dron.stop_sending_telemetry_info()

    elif command == "changeHeading":
        if dron.state == "flying":
            try:
                grados = int(message.payload.decode("utf-8"))
                dron.changeHeading(grados)
            except (ValueError, TypeError):
                pass

    elif command == "changeNavSpeed":
        if dron.state == "flying":
            try:
                velocidad = float(message.payload.decode("utf-8"))
                dron.changeNavSpeed(velocidad)
            except (ValueError, TypeError):
                pass


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("AutopilotService connectat al broker MQTT, rc=", rc)
    else:
        print("AutopilotService error connexió broker, rc=", rc)


# ------------------------------------------------------------------ main

dron = Dron()

n = str(random.randint(0, 10000))
client = mqtt.Client("autopilotServiceDemo" + n, transport="websockets")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_message  = on_message
client.on_connect  = on_connect
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
client.subscribe("+/autopilotServiceDemo/#")

print("AutopilotService esperant peticions...")
client.loop_forever()