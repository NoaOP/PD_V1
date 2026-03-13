############  INSTALAR ##############
# paho-mqtt, version 1.6.1
#####################################
import random

import paho.mqtt.client as mqtt
import json
from dronLink.Dron import Dron
import random
import time
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import cv2
import threading

active_origins = set()
last_telemetry_time = 0

# esta función sirve para publicar los eventos resultantes de las acciones solicitadas
def publish_event (event):
    global sending_topic, client
    client.publish(sending_topic + '/'+event)


def publish_telemetry_info(telemetry_info):
    global active_origins, client, last_telemetry_time

    current_time = time.time()
    if current_time - last_telemetry_time < 0.5:
        return
    last_telemetry_time = current_time

    for origin in active_origins:
        topic = "Grup2/autopilotServiceDemo/" + origin + "/telemetryInfo"
        client.publish(topic, json.dumps(telemetry_info))


class CameraStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            print("ERROR: No se puede leer de la cámara")
            return None
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = pts
        new_frame.time_base = time_base
        return new_frame



loop = asyncio.new_event_loop()
pc = None
video_running = False
video_loop = None

def start_webrtc_video(origin):
    global pc, video_loop, client, video_running
    video_running= True

    async def run_video():
        global pc, video_running

        video_track = CameraStreamTrack()
        pc = RTCPeerConnection()
        pc.addTrack(video_track)
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        payload = json.dumps({"offer": {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}})
        client.publish(f"Grup2/autopilotServiceDemo/{origin}/videoOffer", payload)
        while video_running:
            await asyncio.sleep(1)
        await pc.close()
        video_track.cap.release()

    video_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(video_loop)
    video_loop.run_until_complete(run_video())

def stop_webrtc_video():
    global video_running
    print("Deteniendo bucle de video...")
    video_running = False

def process_answer(answer_data):
    global pc, video_loop
    async def set_answer():
        if pc:
            answer = RTCSessionDescription(sdp=answer_data["answer"]["sdp"], type=answer_data["answer"]["type"])
            await pc.setRemoteDescription(answer)
            print("Remote description (Answer) establecida con éxito.")
    if video_loop:
        asyncio.run_coroutine_threadsafe(set_answer(), video_loop)


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

    if command == 'startVideo':
        print("Recibida petición de video. Iniciando...")
        # Ejecutamos WebRTC
        threading.Thread(target=start_webrtc_video, args=(origin,)).start()

    if command == 'videoAnswer':
        print("Recibida respuesta de video de la web")
        data = json.loads(message.payload.decode("utf-8"))
        process_answer(data)

    if command == 'iceCandidate':
        pass
    if command == 'stopVideo':
        print("Petición de parada de video recibida")
        stop_webrtc_video()


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

