###########  INSTALAR #########################
# opencv-python
# aiortc
###############################################
import asyncio
import cv2
import json
import os
import threading
import paho.mqtt.client as mqtt

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame


# afegim MQTT per la web app
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "dronseetac.upc.edu")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "8000"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "dronsEETAC")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "mimara1456.")


pc_mqtt = None
video_sender_mqtt = None
async_loop = None


class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id=0):
        super().__init__()
        print(f"Encendiendo la cámara {camera_id}...")
        self.cap = cv2.VideoCapture(camera_id)

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()
        if not ret:
            print("Fallo al leer la cámara")
            await asyncio.sleep(0.1)
            return None

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self):
        super().stop()
        if self.cap:
            self.cap.release()
            print("Cámara liberada.")


#part del MQTT
async def start_mqtt_video(mqtt_client, origin):
    global pc_mqtt, video_sender_mqtt
    await stop_mqtt_video()

    pc_mqtt = RTCPeerConnection()
    video_sender_mqtt = CustomVideoStreamTrack(0)
    pc_mqtt.addTrack(video_sender_mqtt)

    offer = await pc_mqtt.createOffer()
    await pc_mqtt.setLocalDescription(offer)

    payload = json.dumps({
        "offer": {"sdp": pc_mqtt.localDescription.sdp, "type": pc_mqtt.localDescription.type}
    })
    mqtt_client.publish(f"Grup2/autopilotServiceDemo/{origin}/videoOffer", payload)
    print("WebRTC: Oferta de video enviada a la Web.")


async def process_mqtt_answer(data):
    global pc_mqtt
    if pc_mqtt:
        answer = RTCSessionDescription(sdp=data["answer"]["sdp"], type=data["answer"]["type"])
        await pc_mqtt.setRemoteDescription(answer)
        print("WebRTC: Conexión de video establecida con la Web.")


async def stop_mqtt_video():
    global pc_mqtt, video_sender_mqtt
    if pc_mqtt:
        await pc_mqtt.close()
        pc_mqtt = None
    if video_sender_mqtt:
        video_sender_mqtt.stop()
        video_sender_mqtt = None
    print("WebRTC: Video de la Web detenido.")


def on_message(client, userdata, message):
    global async_loop
    topic_parts = message.topic.split("/")
    if len(topic_parts) < 3: return

    origin = topic_parts[0]
    command = topic_parts[2]

    if command == "startVideo":
        asyncio.run_coroutine_threadsafe(start_mqtt_video(client, origin), async_loop)
    elif command == "videoAnswer":
        data = json.loads(message.payload.decode("utf-8"))
        asyncio.run_coroutine_threadsafe(process_mqtt_answer(data), async_loop)
    elif command == "stopVideo":
        asyncio.run_coroutine_threadsafe(stop_mqtt_video(), async_loop)


def run_mqtt_listener():
    client = mqtt.Client("CameraService_" + str(os.getpid()), transport="websockets")
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_message = on_message
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.subscribe("+/autopilotServiceDemo/#")
    print("-> CameraService escuchando peticiones Web por MQTT...")
    client.loop_forever()


# part del python normal com abans
async def setup_webrtc_tcp(ip_address, port, camera_id):
    signaling = TcpSocketSignaling(ip_address, port)

    while True:
        pc = RTCPeerConnection()
        video_sender = CustomVideoStreamTrack(camera_id)
        pc.addTrack(video_sender)

        try:
            print(f"-> CameraService esperando al Dashboard en {ip_address}:{port}...")
            await signaling.connect()
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)
            await signaling.send(pc.localDescription)

            while True:
                obj = await signaling.receive()
                if isinstance(obj, RTCSessionDescription):
                    await pc.setRemoteDescription(obj)
                    print("Dashboard conectado al video.")
                elif obj is None:
                    print("Dashboard desconectado.")
                    break
        except Exception as e:
            pass
        finally:
            video_sender.stop()
            await pc.close()


#main
async def main():
    global async_loop
    async_loop = asyncio.get_running_loop()
    threading.Thread(target=run_mqtt_listener, daemon=True).start()
    await setup_webrtc_tcp("0.0.0.0", 9999, 0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCerrando CameraService...")
