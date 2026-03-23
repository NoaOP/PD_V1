###########  INSTALAR #########################
# opencv-python
# aiortc
###############################################


import asyncio
import fractions

import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from aiortc.contrib.signaling import BYE, object_from_string, object_to_string
from av import VideoFrame


class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id):
        super().__init__()
        print("Preparando la camara ...")
        self.cap = cv2.VideoCapture(camera_id)
        self.frame_count = 0

    async def recv(self):
        self.frame_count += 1
        ok, frame = self.cap.read()
        if not ok:
            await asyncio.sleep(0.02)
            frame = cv2.imread("", cv2.IMREAD_COLOR)  # stays None, handled below
            if frame is None:
                # Retry on next tick if camera dropped a frame.
                return await self.recv()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)
        return video_frame

    def close(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None


class MultiClientCameraService:
    def __init__(self, host="0.0.0.0", port=9999, camera_id=0):
        self.host = host
        self.port = port
        self.camera_track = CustomVideoStreamTrack(camera_id)
        self.relay = MediaRelay()
        self.peers = set()
        self.server = None

    async def _handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"Cliente conectado: {addr}")

        pc = RTCPeerConnection()
        self.peers.add(pc)
        pc.addTrack(self.relay.subscribe(self.camera_track))

        try:
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            writer.write((object_to_string(pc.localDescription) + "\n").encode("utf8"))
            await writer.drain()

            while True:
                data = await reader.readline()
                if not data:
                    break

                message = data.decode("utf8").strip()
                if not message:
                    continue

                obj = object_from_string(message)

                if isinstance(obj, RTCSessionDescription):
                    await pc.setRemoteDescription(obj)
                elif obj is BYE:
                    break
                # Candidates are optional here because aiortc includes ICE in SDP,
                # but object_from_string already parses them if sent.
                else:
                    try:
                        await pc.addIceCandidate(obj)
                    except Exception:
                        pass
        except Exception as exc:
            print(f"Error con cliente {addr}: {exc}")
        finally:
            self.peers.discard(pc)
            try:
                await pc.close()
            except Exception:
                pass
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            print(f"Cliente desconectado: {addr}")

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port,reuse_address=True)
        print(f"CameraService multi-cliente en {self.host}:{self.port}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

        await asyncio.gather(*(pc.close() for pc in list(self.peers)), return_exceptions=True)
        self.peers.clear()
        self.camera_track.close()


async def main():
    service = MultiClientCameraService(host="0.0.0.0", port=9999, camera_id=0)
    try:
        await service.start()
    finally:
        await service.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("CameraService detenido")
