############  INSTALAR ##############
# paho-mqtt, version 1.6.1
#####################################

import random
import os
import time
import json
import threading
import math


import paho.mqtt.client as mqtt
from P2.ProyectoDeDrones.dronLink.Dron import Dron

active_origins    = set()
last_telemetry_time = 0
last_telemetry_info = None
writing_lock = threading.Lock()

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
    #     topic = "Grup212/autopilotServiceDemo/" + origin + "/" + event
    #     client.publish(topic)
    global client


    topic = "Grup212/autopilotServiceDemo/" + origin + "/" + event

    client.publish(topic)

def publish_telemetry_info(telemetry_info):
    """Publica telemetria amb fre de 0.5s per no saturar el broker."""
    global active_origins, client, last_telemetry_time, last_telemetry_info

    # Guardem sempre l’última telemetria, encara que no la publiquem
    last_telemetry_info = telemetry_info

    current_time = time.time()
    if current_time - last_telemetry_time < 0.5:
        return

    last_telemetry_time = current_time

    for origin in active_origins:

        topic = "Grup212/autopilotServiceDemo/" + origin + "/telemetryInfo"
        client.publish(topic, json.dumps(telemetry_info))


def do_triangle(origin):
    global dron
    try:
        if dron.state != "flying":
            return
        dron.go("North")
        time.sleep(4)

        dron.go("SouthEast")
        time.sleep(4)

        dron.go("SouthWest")
        time.sleep(4)

        dron.go("North")
        time.sleep(4)

        dron.go("Stop")
        publish_event(origin, "triangleDone")

    except Exception as e:
        print(f"Error haciendo triángulo: {e}")
        try:
            dron.go("Stop")
        except:
            pass


def do_cuadrado(origin):
    global dron
    try:
        if dron.state != "flying":
            return
        dron.go("North")
        time.sleep(6)

        dron.go("East")
        time.sleep(6)

        dron.go("South")
        time.sleep(6)

        dron.go("West")
        time.sleep(6)

        dron.go("Stop")
        publish_event(origin, "CuadradoDone")

    except Exception as e:
        print(f"Error haciendo el cuadrado: {e}")
        try:
            dron.go("Stop")
        except:
            pass


def do_redonda(origin):
    global dron
    try:
        if dron.state != "flying":
            return
        dron.go("North")
        time.sleep(2)
        dron.go("NorthEast")
        time.sleep(2)
        dron.go("East")
        time.sleep(2)
        dron.go("SouthEast")
        time.sleep(2)
        dron.go("South")
        time.sleep(2)
        dron.go("SouthWest")
        time.sleep(2)
        dron.go("West")
        time.sleep(2)
        dron.go("NorthWest")
        time.sleep(2)

        dron.go("Stop")
        publish_event(origin, "redondaDone")

    except Exception as e:
        print(f"Error haciendo Redonda: {e}")
        try:
            dron.go("Stop")
        except:
            pass

def do_corazon(origin):
    global dron
    try:
        if dron.state != "flying":
            return

        dron.go("NorthEast")
        time.sleep(3)
        dron.go("East")
        time.sleep(2)
        dron.go("SouthEast")
        time.sleep(2)
        dron.go("South")
        time.sleep(2)
        dron.go("SouthWest")
        time.sleep(6)
        dron.go("NorthWest")
        time.sleep(6)
        dron.go("North")
        time.sleep(2)
        dron.go("NorthEast")
        time.sleep(2)
        dron.go("East")
        time.sleep(2)
        dron.go("SouthEast")
        time.sleep(2)


        dron.go("Stop")
        publish_event(origin, "corazonDone")

    except Exception as e:
        print(f"Error haciendo corazón: {e}")
        try:
            dron.go("Stop")
        except:
            pass

# =========================================================
# ESCRIPTURA DE TEXT AMB PUNTS GPS
# =========================================================

METRES_PER_UNIT = 0.8      # Mida de la lletra. Si vols més gran: 1.0. Si vols més petit: 0.6
LETTER_GAP = 1.5           # Separació entre lletres
SPACE_GAP = 4.0            # Separació entre paraules
WRITING_SPEED = 0.7        # Velocitat del dron quan escriu
GOTO_SETTLE_TIME = 0.2     # Petita pausa entre punts

LETTER_PATHS = {
    "A": {
        "width": 4,
        "strokes": [
            [(0, 0), (2, 5), (4, 0)],
            [(1, 2.3), (3, 2.3)]
        ]
    },

    "B": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (3, 5), (4, 4), (4, 3), (3, 2.5), (0, 2.5)],
            [(0, 2.5), (3, 2.5), (4, 2), (4, 1), (3, 0), (0, 0)]
        ]
    },

    "C": {
        "width": 4,
        "strokes": [
            [(4, 5), (0, 5), (0, 0), (4, 0)]
        ]
    },

    "D": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (3, 5), (4, 4), (4, 1), (3, 0), (0, 0)]
        ]
    },

    "E": {
        "width": 4,
        "strokes": [
            [(4, 5), (0, 5), (0, 0), (4, 0)],
            [(0, 2.5), (3, 2.5)]
        ]
    },

    "F": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (4, 5)],
            [(0, 2.5), (3, 2.5)]
        ]
    },

    "G": {
        "width": 4,
        "strokes": [
            [(4, 5), (0, 5), (0, 0), (4, 0), (4, 2), (2.5, 2)]
        ]
    },

    "H": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5)],
            [(4, 0), (4, 5)],
            [(0, 2.5), (4, 2.5)]
        ]
    },

    "I": {
        "width": 3,
        "strokes": [
            [(0, 5), (3, 5)],
            [(1.5, 5), (1.5, 0)],
            [(0, 0), (3, 0)]
        ]
    },

    "J": {
        "width": 4,
        "strokes": [
            [(0, 5), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1)]
        ]
    },

    "K": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5)],
            [(0, 2.5), (4, 5)],
            [(0, 2.5), (4, 0)]
        ]
    },

    "L": {
        "width": 4,
        "strokes": [
            [(0, 5), (0, 0), (4, 0)]
        ]
    },

    "M": {
        "width": 5,
        "strokes": [
            [(0, 0), (0, 5), (2.5, 2.5), (5, 5), (5, 0)]
        ]
    },

    "N": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (4, 0), (4, 5)]
        ]
    },

    "O": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (4, 5), (4, 0), (0, 0)]
        ]
    },

    "P": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (3, 5), (4, 4), (4, 3), (3, 2.5), (0, 2.5)]
        ]
    },

    "Q": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (4, 5), (4, 0), (0, 0)],
            [(2.5, 1.5), (4.5, -0.5)]
        ]
    },

    "R": {
        "width": 4,
        "strokes": [
            [(0, 0), (0, 5), (3, 5), (4, 4), (4, 3), (3, 2.5), (0, 2.5)],
            [(0, 2.5), (4, 0)]
        ]
    },

    "S": {
        "width": 4,
        "strokes": [
            [(4, 5), (0, 5), (0, 2.5), (4, 2.5), (4, 0), (0, 0)]
        ]
    },

    "T": {
        "width": 4,
        "strokes": [
            [(0, 5), (4, 5)],
            [(2, 5), (2, 0)]
        ]
    },

    "U": {
        "width": 4,
        "strokes": [
            [(0, 5), (0, 0), (4, 0), (4, 5)]
        ]
    },

    "V": {
        "width": 4,
        "strokes": [
            [(0, 5), (2, 0), (4, 5)]
        ]
    },

    "W": {
        "width": 5,
        "strokes": [
            [(0, 5), (1.2, 0), (2.5, 2.5), (3.8, 0), (5, 5)]
        ]
    },

    "X": {
        "width": 4,
        "strokes": [
            [(0, 5), (4, 0)],
            [(4, 5), (0, 0)]
        ]
    },

    "Y": {
        "width": 4,
        "strokes": [
            [(0, 5), (2, 2.5), (4, 5)],
            [(2, 2.5), (2, 0)]
        ]
    },

    "Z": {
        "width": 4,
        "strokes": [
            [(0, 5), (4, 5), (0, 0), (4, 0)]
        ]
    }
}


def set_paint(origin, pintar):
    if origin is None:
        return

    if pintar:
        publish_event(origin, "paintOn")
    else:
        publish_event(origin, "paintOff")

    time.sleep(0.25)


def obtenir_posicio_actual():
    """
    Agafa l'última posició rebuda per telemetria.
    """
    global last_telemetry_info

    if last_telemetry_info is None:
        return None, None, None

    lat = (
        last_telemetry_info.get("lat")
        or last_telemetry_info.get("latitude")
    )

    lon = (
        last_telemetry_info.get("lon")
        or last_telemetry_info.get("lng")
        or last_telemetry_info.get("longitude")
    )

    alt = (
        last_telemetry_info.get("alt")
        or last_telemetry_info.get("altitude")
        or 5
    )

    return lat, lon, alt


def grid_to_gps(lat0, lon0, x, y):
    """
    Converteix punts de quadrícula a coordenades GPS.
    x positiu = Est
    y positiu = Nord
    """
    metres_nord = y * METRES_PER_UNIT
    metres_est = x * METRES_PER_UNIT

    metres_per_deg_lat = 111320
    metres_per_deg_lon = 111320 * math.cos(math.radians(lat0))

    lat = lat0 + metres_nord / metres_per_deg_lat
    lon = lon0 + metres_est / metres_per_deg_lon

    return lat, lon


def anar_a_punt(lat, lon, alt):
    """
    Porta el dron a un punt GPS.
    Si la teva llibreria usa goTo en comptes de goto,
    només canvia dron.goto per dron.goTo.
    """
    global dron

    try:
        dron.goto(lat, lon, alt, blocking=True)
    except TypeError:
        try:
            dron.goto(lat, lon, alt)
            time.sleep(2)
        except Exception as e:
            print(f"Error anant al punt GPS: {e}")

    time.sleep(GOTO_SETTLE_TIME)


def dibuixar_trac_gps(stroke, lat0, lon0, alt, x_offset, origin):
    """
    Va al primer punt sense pintar.
    Després encén pintura i segueix tots els punts del traç.
    """
    if not stroke:
        return

    start_x, start_y = stroke[0]
    lat_start, lon_start = grid_to_gps(lat0, lon0, x_offset + start_x, start_y)

    # Anar al principi del traç sense pintar
    set_paint(origin, False)
    anar_a_punt(lat_start, lon_start, alt)

    # Pintar el traç
    set_paint(origin, True)

    for x, y in stroke[1:]:
        lat, lon = grid_to_gps(lat0, lon0, x_offset + x, y)
        anar_a_punt(lat, lon, alt)

    set_paint(origin, False)


def escriure_text_gps(texto, origin):
    global dron, writing_lock

    if not writing_lock.acquire(blocking=False):
        print("Ja s'està escrivint un altre text.")
        publish_event(origin, "textError")
        return

    try:
        if dron.state != "flying":
            print("El dron no està volant. No es pot escriure text.")
            publish_event(origin, "textError")
            return

        texto = texto.upper().strip()

        if texto == "":
            publish_event(origin, "textError")
            return

        lat0, lon0, alt = obtenir_posicio_actual()

        if lat0 is None or lon0 is None:
            print("No hi ha telemetria GPS encara.")
            publish_event(origin, "textError")
            return

        try:
            dron.changeNavSpeed(WRITING_SPEED)
        except:
            pass

        print(f"Començant a escriure text amb punts GPS: {texto}")

        x_actual = 0.0

        set_paint(origin, False)

        for letra in texto:
            if letra == " ":
                x_actual += SPACE_GAP
                continue

            if letra not in LETTER_PATHS:
                print(f"Lletra no implementada: {letra}")
                x_actual += 4 + LETTER_GAP
                continue

            glyph = LETTER_PATHS[letra]

            for stroke in glyph["strokes"]:
                dibuixar_trac_gps(stroke, lat0, lon0, alt, x_actual, origin)

            # Separació entre lletres sense pintar
            x_actual += glyph["width"] + LETTER_GAP

        set_paint(origin, False)
        dron.go("Stop")
        publish_event(origin, "textDone")

        print("Text acabat correctament.")

    except Exception as e:
        print(f"Error escrivint text amb GPS: {e}")

        try:
            set_paint(origin, False)
            dron.go("Stop")
            publish_event(origin, "textError")
        except:
            pass

    finally:
        writing_lock.release()


def _on_connected_callback():
    """Cridat per dronLink quan la connexió MAVProxy s'estableix (no bloquejant)."""
    publish_event("connected")
    print("Dron connectat correctament via MAVProxy")


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
                if opcion == 1:  # Dron Real COM, no se utiliza
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
    elif command == "cuadrado":
        if dron.state == "flying":
            threading.Thread(
                target=do_cuadrado,
                args=(origin,),
                daemon=True
            ).start()
    elif command == "redonda":
        if dron.state == "flying":
            threading.Thread(
                target=do_redonda,
                args=(origin,),
                daemon=True
            ).start()
    elif command == "corazon":
        if dron.state == "flying":
            threading.Thread(
                target=do_corazon,
                args=(origin,),
                daemon=True
            ).start()

    elif command == "writeText":
        texto = message.payload.decode("utf-8")

        if dron.state == "flying":
            threading.Thread(
                target=escriure_text_gps,
                args=(texto, origin),
                daemon=True
            ).start()
        else:
            print("No es pot escriure text perquè el dron no està volant.")
            publish_event(origin, "textError")

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


    elif command == "executeLawnmower":

        if dron.state == "flying":

            try:

                payload_str = message.payload.decode("utf-8")

                lista_waypoints = json.loads(payload_str)

                print(f"RECIBIDA RUTA LAWNMOWER: {len(lista_waypoints)} waypoints.")

                def run_lawnmower_manual():

                    try:

                        # Bajamos velocidad para que el trazado quede más limpio

                        try:

                            dron.changeNavSpeed(2)

                        except:

                            pass

                        # Activamos pintura al empezar a rellenar

                        publish_event(origin, "paintOn")

                        time.sleep(0.3)

                        for wp in lista_waypoints:

                            lat = wp["lat"]

                            lon = wp["lon"]

                            alt = wp.get("alt", 5)

                            print(f"Anant a punt: lat={lat}, lon={lon}, alt={alt}")

                            try:

                                dron.goto(lat, lon, alt, blocking=True)

                            except TypeError:

                                dron.goto(lat, lon, alt)

                                time.sleep(2)

                            time.sleep(0.2)

                        # Apagamos pintura al acabar

                        publish_event(origin, "paintOff")

                        time.sleep(0.3)

                        # Paramos el dron en la última posición, SIN RTL

                        dron.go("Stop")

                        publish_event(origin, "missionCompleted")

                        print("Ruta lawnmower acabada. El dron es queda a l'última posició.")


                    except Exception as e:

                        print(f"Error durant la ruta lawnmower manual: {e}")

                        try:

                            publish_event(origin, "paintOff")

                            dron.go("Stop")

                        except:

                            pass

                        publish_event(origin, "missionError")

                threading.Thread(

                    target=run_lawnmower_manual,

                    daemon=True

                ).start()


            except Exception as e:

                print(f"Error al preparar ruta lawnmower: {e}")

                publish_event(origin, "missionError")

        else:

            print("No es pot executar lawnmower perquè el dron no està volant.")

            publish_event(origin, "missionError")


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