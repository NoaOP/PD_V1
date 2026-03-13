import asyncio
import json
import threading
import tkinter as tk

import paho.mqtt.client as mqtt
from dronLink.Dron import Dron

try:
    import cv2
    import numpy as np
    import torch
    from aiortc import MediaStreamTrack, RTCPeerConnection
    from aiortc.contrib.signaling import TcpSocketSignaling
    from av import VideoFrame

    VIDEO_DEPS_OK = True
except Exception:
    cv2 = None
    np = None
    torch = None
    MediaStreamTrack = object
    RTCPeerConnection = None
    TcpSocketSignaling = None
    VideoFrame = object
    VIDEO_DEPS_OK = False


class LocalDetector:
    def __init__(self):
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
        self.model.eval()

    def detect(self, frame, object_id):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model(img_rgb)
        for *box, _conf, cls in results.xyxy[0]:
            if int(cls.item()) == object_id:
                x1, y1, x2, y2 = map(int, box)
                return True, (x1, y1, x2, y2)
        return False, None


class LocalVideoReceiver:
    def __init__(self, object_getter, stop_event):
        self.object_getter = object_getter
        self.stop_event = stop_event
        self.detector = LocalDetector()

    async def handle_track(self, track):
        frame_count = 0
        detected = False
        rect = None

        while not self.stop_event.is_set():
            try:
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                frame_count += 1

                if isinstance(frame, VideoFrame):
                    frame = frame.to_ndarray(format="bgr24")
                elif isinstance(frame, np.ndarray):
                    pass
                else:
                    continue

                object_id = self.object_getter()
                if object_id is not None and frame_count % 10 == 0:
                    detected, rect = self.detector.detect(frame, object_id)

                if detected and rect is not None:
                    x1, y1, x2, y2 = rect
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "here", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow("Local Camera", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.stop_event.set()
                    break
            except asyncio.TimeoutError:
                continue
            except Exception:
                break


class DashboardAllApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard All (Local / Global)")

        self.mode = None
        self.local_dron = None
        self.global_client = None
        self.local_previous_btn = None
        self.global_previous_btn = None

        self.local_widgets = {}
        self.global_widgets = {}

        self.local_video_thread = None
        self.local_video_stop_event = threading.Event()
        self.local_selected_object = None

        self._build_shell()
        self.switch_mode("local")

    def _build_shell(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        header = tk.Frame(self.root)
        header.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=8, pady=8)
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)

        self.local_mode_btn = tk.Button(header, text="Mode Local", bg="purple", fg="white", command=lambda: self.switch_mode("local"))
        self.local_mode_btn.grid(row=0, column=0, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.global_mode_btn = tk.Button(header, text="Mode Global", bg="purple", fg="white", command=lambda: self.switch_mode("global"))
        self.global_mode_btn.grid(row=0, column=1, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.mode_label = tk.Label(header, text="")
        self.mode_label.grid(row=0, column=2, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.content_frame = tk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=8, pady=8)
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.columnconfigure(0, weight=1)

    def switch_mode(self, mode):
        if self.mode == mode:
            return

        self._cleanup_mode()
        self.mode = mode

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if mode == "local":
            self.mode_label.config(text="Actiu: Local")
            self.local_mode_btn.config(bg="purple", fg="white")
            self.global_mode_btn.config(bg="cadetblue", fg="black")
            self._build_local_view()
        else:
            self.mode_label.config(text="Actiu: Global")
            self.local_mode_btn.config(bg="purple", fg="white")
            self.global_mode_btn.config(bg="green", fg="white")
            self._build_global_view()

    def _cleanup_mode(self):
        if self.mode == "local" and self.local_dron is not None:
            try:
                self.local_dron.stop_sending_telemetry_info()
            except Exception:
                pass
            self._stop_local_video()

        if self.mode == "global" and self.global_client is not None:
            try:
                self.global_client.loop_stop()
                self.global_client.disconnect()
            except Exception:
                pass
            self.global_client = None

    def _build_local_view(self):
        self.local_dron = Dron()
        self.local_previous_btn = None
        self.local_widgets = {}

        panel = tk.Frame(self.content_frame)
        panel.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)

        for idx in range(12):
            panel.rowconfigure(idx, weight=1)
        for idx in range(4):
            panel.columnconfigure(idx, weight=1)

        connect_btn = tk.Button(panel, text="Conectar", bg="purple", fg="white", command=self._local_connect)
        connect_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        arm_btn = tk.Button(panel, text="Armar", bg="purple", fg="white", command=self._local_arm)
        arm_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        takeoff_btn = tk.Button(panel, text="Despegar", bg="purple", fg="white", command=self._local_takeoff)
        takeoff_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        heading_sldr = tk.Scale(panel, label="Grados:", resolution=5, from_=0, to=360, tickinterval=45, orient=tk.HORIZONTAL)
        heading_sldr.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        heading_sldr.bind("<ButtonRelease-1>", self._local_change_heading)

        land_btn = tk.Button(panel, text="Aterrizar", bg="purple", fg="white", command=self._local_land)
        land_btn.grid(row=4, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        rtl_btn = tk.Button(panel, text="RTL", bg="purple", fg="white", command=self._local_rtl)
        rtl_btn.grid(row=4, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        nav_frame = tk.LabelFrame(panel, text="Navegacion")
        nav_frame.grid(row=5, column=0, columnspan=2, padx=50, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        self._build_nav_buttons(nav_frame, self._local_go)

        speed_sldr = tk.Scale(panel, label="Velocidad (m/s):", resolution=1, from_=0, to=20, tickinterval=5, orient=tk.HORIZONTAL)
        speed_sldr.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        speed_sldr.bind("<ButtonRelease-1>", self._local_change_speed)

        start_telem_btn = tk.Button(panel, text="Empezar telemetria", bg="purple", fg="white", command=self._local_start_telem)
        start_telem_btn.grid(row=7, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        stop_telem_btn = tk.Button(panel, text="Parar telemetria", bg="purple", fg="white", command=self._local_stop_telem)
        stop_telem_btn.grid(row=7, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        telemetry_frame = tk.LabelFrame(panel, text="Telemetria")
        telemetry_frame.grid(row=8, column=0, columnspan=4, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)
        self._build_local_telemetry(telemetry_frame)

        lat_entry = tk.Entry(panel)
        lat_entry.grid(row=9, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        lon_entry = tk.Entry(panel)
        lon_entry.grid(row=9, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        alt_entry = tk.Entry(panel)
        alt_entry.grid(row=9, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        goto_btn = tk.Button(panel, text="Go to", bg="purple", command=lambda: self._local_goto(lat_entry, lon_entry, alt_entry, goto_btn))
        goto_btn.config(fg="white")
        goto_btn.grid(row=9, column=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        video_btn = tk.Button(panel, text="Recibir video por WebRTC", bg="purple", fg="white", command=self._local_start_video)
        video_btn.grid(row=10, column=0, columnspan=4, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        detect_frame = tk.LabelFrame(panel, text="Deteccion de objetos")
        detect_frame.grid(row=11, column=0, columnspan=4, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        for idx in range(7):
            detect_frame.columnconfigure(idx, weight=1)

        detect_buttons = [
            ("Sin deteccion", None),
            ("Banana", 46),
            ("Reloj", 74),
            ("Pizza", 53),
            ("Perro", 16),
            ("Naranja", 49),
            ("Pastel", 55),
        ]
        for col, (label, object_id) in enumerate(detect_buttons):
            tk.Button(
                detect_frame,
                text=label,
                bg="purple",
                fg="white",
                command=lambda oid=object_id: self._local_set_object(oid),
            ).grid(row=0, column=col, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.local_widgets = {
            "connect_btn": connect_btn,
            "arm_btn": arm_btn,
            "takeoff_btn": takeoff_btn,
            "land_btn": land_btn,
            "rtl_btn": rtl_btn,
            "heading_sldr": heading_sldr,
            "speed_sldr": speed_sldr,
            "alt_show": self.local_widgets.get("alt_show"),
            "heading_show": self.local_widgets.get("heading_show"),
            "state_show": self.local_widgets.get("state_show"),
            "speed_show": self.local_widgets.get("speed_show"),
            "mode_show": self.local_widgets.get("mode_show"),
            "video_btn": video_btn,
        }

    def _build_global_view(self):
        self.global_previous_btn = None
        self.global_widgets = {}

        self.global_client = mqtt.Client("InterfazGlobal", transport="websockets")
        self.global_client.on_message = self._global_on_message
        self.global_client.on_connect = self._global_on_connect
        self.global_client.connect("broker.hivemq.com", 8000)
        self.global_client.subscribe("Grup2/autopilotServiceDemo/interfazGlobal/#")
        self.global_client.loop_start()

        panel = tk.Frame(self.content_frame)
        panel.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)

        for idx in range(10):
            panel.rowconfigure(idx, weight=1)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        connect_btn = tk.Button(panel, text="Conectar", bg="purple", fg="white", command=self._global_connect)
        connect_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        arm_takeoff_btn = tk.Button(panel, text="Despegar", bg="purple", fg="white", command=self._global_takeoff)
        arm_takeoff_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        heading_sldr = tk.Scale(panel, label="Grados:", resolution=5, from_=0, to=360, tickinterval=45, orient=tk.HORIZONTAL)
        heading_sldr.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        heading_sldr.bind("<ButtonRelease-1>", self._global_change_heading)

        land_btn = tk.Button(panel, text="Aterrizar", bg="purple", fg="white", command=self._global_land)
        land_btn.grid(row=5, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        rtl_btn = tk.Button(panel, text="RTL", bg="purple", fg="white", command=self._global_rtl)
        rtl_btn.grid(row=5, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        nav_frame = tk.LabelFrame(panel, text="Navegacion")
        nav_frame.grid(row=6, column=0, columnspan=2, padx=50, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        self._build_nav_buttons(nav_frame, self._global_go)

        speed_sldr = tk.Scale(panel, label="Velocidad (m/s):", resolution=1, from_=0, to=20, tickinterval=5, orient=tk.HORIZONTAL)
        speed_sldr.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        speed_sldr.bind("<ButtonRelease-1>", self._global_change_speed)

        start_telem_btn = tk.Button(panel, text="Empezar telemetria", bg="purple", fg="white", command=self._global_start_telem)
        start_telem_btn.grid(row=8, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        stop_telem_btn = tk.Button(panel, text="Parar telemetria", bg="purple", fg="white", command=self._global_stop_telem)
        stop_telem_btn.grid(row=8, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        telemetry_frame = tk.LabelFrame(panel, text="Telemetria")
        telemetry_frame.grid(row=9, column=0, columnspan=2, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)
        self._build_global_telemetry(telemetry_frame)

        self.global_widgets = {
            "connect_btn": connect_btn,
            "arm_takeoff_btn": arm_takeoff_btn,
            "land_btn": land_btn,
            "rtl_btn": rtl_btn,
            "heading_sldr": heading_sldr,
            "speed_sldr": speed_sldr,
            "alt_show": self.global_widgets.get("alt_show"),
            "heading_show": self.global_widgets.get("heading_show"),
            "state_show": self.global_widgets.get("state_show"),
        }

    def _build_nav_buttons(self, nav_frame, go_handler):
        nav_frame.rowconfigure(0, weight=1)
        nav_frame.rowconfigure(1, weight=1)
        nav_frame.rowconfigure(2, weight=1)
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.columnconfigure(1, weight=1)
        nav_frame.columnconfigure(2, weight=1)

        buttons = [
            ("NW", "NorthWest", 0, 0),
            ("No", "North", 0, 1),
            ("NE", "NorthEast", 0, 2),
            ("We", "West", 1, 0),
            ("St", "Stop", 1, 1),
            ("Ea", "East", 1, 2),
            ("SW", "Down", 2, 0),
            ("So", "South", 2, 1),
            ("SE", "Up", 2, 2),
        ]

        for text, direction, row, col in buttons:
            btn = tk.Button(nav_frame, text=text, bg="purple", fg="white")
            btn.config(command=lambda d=direction, b=btn: go_handler(d, b))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    def _build_local_telemetry(self, parent):
        labels = ["Altitud", "Heading", "Estado", "Speed", "Mode"]
        for idx in range(5):
            parent.columnconfigure(idx, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        for idx, text in enumerate(labels):
            tk.Label(parent, text=text).grid(row=0, column=idx, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.local_widgets["alt_show"] = tk.Label(parent, text="")
        self.local_widgets["alt_show"].grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.local_widgets["heading_show"] = tk.Label(parent, text="")
        self.local_widgets["heading_show"].grid(row=1, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.local_widgets["state_show"] = tk.Label(parent, text="")
        self.local_widgets["state_show"].grid(row=1, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.local_widgets["speed_show"] = tk.Label(parent, text="")
        self.local_widgets["speed_show"].grid(row=1, column=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.local_widgets["mode_show"] = tk.Label(parent, text="")
        self.local_widgets["mode_show"].grid(row=1, column=4, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    def _build_global_telemetry(self, parent):
        labels = ["Altitud", "Heading", "Estado"]
        for idx in range(3):
            parent.columnconfigure(idx, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        for idx, text in enumerate(labels):
            tk.Label(parent, text=text).grid(row=0, column=idx, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.global_widgets["alt_show"] = tk.Label(parent, text="")
        self.global_widgets["alt_show"].grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.global_widgets["heading_show"] = tk.Label(parent, text="")
        self.global_widgets["heading_show"].grid(row=1, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        self.global_widgets["state_show"] = tk.Label(parent, text="")
        self.global_widgets["state_show"].grid(row=1, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # Local camera and detection
    def _local_set_object(self, object_id):
        self.local_selected_object = object_id

    def _local_start_video(self):
        if not VIDEO_DEPS_OK:
            self.local_widgets["video_btn"].config(text="Faltan deps video", bg="red", fg="white")
            return

        if self.local_video_thread is not None and self.local_video_thread.is_alive():
            self.local_widgets["video_btn"].config(text="Video activo", bg="green", fg="white")
            return

        self.local_video_stop_event = threading.Event()
        self.local_video_thread = threading.Thread(target=self._local_video_thread_runner, daemon=True)
        self.local_video_thread.start()
        self.local_widgets["video_btn"].config(text="Video activo", bg="green", fg="white")

    def _local_video_thread_runner(self):
        try:
            asyncio.run(self._local_video_receiver())
        finally:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

    async def _local_video_receiver(self):
        signaling = TcpSocketSignaling("localhost", 9999)
        pc = RTCPeerConnection()
        receiver = LocalVideoReceiver(lambda: self.local_selected_object, self.local_video_stop_event)

        @pc.on("track")
        def on_track(track):
            if isinstance(track, MediaStreamTrack):
                asyncio.ensure_future(receiver.handle_track(track))

        try:
            await signaling.connect()
            offer = await signaling.receive()
            await pc.setRemoteDescription(offer)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await signaling.send(pc.localDescription)

            while not self.local_video_stop_event.is_set() and pc.connectionState != "connected":
                await asyncio.sleep(0.1)

            while not self.local_video_stop_event.is_set():
                await asyncio.sleep(0.2)
        except Exception:
            pass
        finally:
            try:
                await pc.close()
            except Exception:
                pass

    def _stop_local_video(self):
        self.local_video_stop_event.set()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        if self.local_widgets.get("video_btn") is not None:
            self.local_widgets["video_btn"].config(text="Recibir video por WebRTC", bg="purple", fg="white")

    # Local handlers
    def _local_show_telemetry(self, telemetry_info):
        self.local_widgets["alt_show"].config(text=round(telemetry_info["alt"], 2))
        self.local_widgets["heading_show"].config(text=round(telemetry_info["heading"], 2))
        self.local_widgets["state_show"].config(text=telemetry_info["state"])
        self.local_widgets["speed_show"].config(text=round(telemetry_info["groundSpeed"], 2))
        self.local_widgets["mode_show"].config(text=telemetry_info["flightMode"])

    def _local_connect(self):
        self.local_dron.connect("tcp:127.0.0.1:5763", 115200)
        self.local_widgets["connect_btn"].config(text="Conectado", fg="white", bg="green")
        self.local_widgets["speed_sldr"].set(1)

    def _local_arm(self):
        self.local_dron.arm()
        self.local_widgets["arm_btn"].config(text="Armado", fg="white", bg="green")

    def _local_in_the_air(self):
        self.local_widgets["takeoff_btn"].config(text="En el aire", fg="white", bg="green")

    def _local_takeoff(self):
        self.local_dron.takeOff(5, blocking=False, callback=self._local_in_the_air)
        self.local_widgets["takeoff_btn"].config(text="Despegando...", fg="black", bg="yellow")

    def _local_on_ground_land(self):
        takeoff_btn = self.local_widgets["takeoff_btn"]
        takeoff_btn.config(text="On the ground", fg="white", bg="purple")
        self.root.after(1500, lambda: takeoff_btn.config(text="Despegar"))
        self.local_widgets["land_btn"].config(text="Land", fg="white", bg="purple")

    def _local_on_ground_rtl(self):
        takeoff_btn = self.local_widgets["takeoff_btn"]
        self.local_widgets["rtl_btn"].config(text="On the ground", fg="white", bg="purple")
        takeoff_btn.config(text="On the ground", fg="white", bg="purple")
        self.root.after(1500, lambda: takeoff_btn.config(text="Despegar"))

    def _local_land(self):
        self.local_dron.Land(blocking=False, callback=self._local_on_ground_land)
        self.local_widgets["land_btn"].config(text="Landing", fg="white", bg="green")

    def _local_rtl(self):
        self.local_dron.RTL(blocking=False, callback=self._local_on_ground_rtl)
        self.local_widgets["rtl_btn"].config(text="Going back home", fg="white", bg="green")

    def _local_go(self, direction, btn):
        if self.local_previous_btn is not None:
            self.local_previous_btn.config(fg="white", bg="purple")

        self.local_dron.go(direction)
        btn.config(fg="white", bg="green")
        self.local_previous_btn = btn

    def _local_goto_done(self, done_btn):
        done_btn.config(text="On place", fg="white", bg="green")

    def _local_goto(self, lat_entry, lon_entry, alt_entry, goto_btn):
        try:
            lat = float(lat_entry.get())
            lon = float(lon_entry.get())
            alt = float(alt_entry.get())
            goto_btn.config(text="On my way")
            self.local_dron.goto(lat, lon, alt, blocking=False, callback=self._local_goto_done, params=goto_btn)
        except ValueError:
            goto_btn.config(text="Error", bg="red")
            self.root.after(1000, lambda: goto_btn.config(text="Go to", bg="purple"))

    def _local_start_telem(self):
        self.local_dron.send_telemetry_info(self._local_show_telemetry)

    def _local_stop_telem(self):
        self.local_dron.stop_sending_telemetry_info()
        self.local_widgets["alt_show"].config(text="--")
        self.local_widgets["heading_show"].config(text="--")
        self.local_widgets["state_show"].config(text="--")
        self.local_widgets["speed_show"].config(text="--")
        self.local_widgets["mode_show"].config(text="--")

    def _local_change_heading(self, _event):
        self.local_dron.changeHeading(int(self.local_widgets["heading_sldr"].get()))

    def _local_change_speed(self, _event):
        self.local_dron.changeNavSpeed(float(self.local_widgets["speed_sldr"].get()))

    # Global handlers
    def _global_publish(self, topic, payload=None):
        if self.global_client is None:
            return
        if payload is None:
            self.global_client.publish(topic)
        else:
            self.global_client.publish(topic, payload)

    def _global_connect(self):
        self._global_publish("interfazGlobal/autopilotServiceDemo/connect")
        self.global_widgets["connect_btn"].config(text="Conectado", fg="white", bg="green")
        self.global_widgets["speed_sldr"].set(1)

    def _global_takeoff(self):
        self._global_publish("interfazGlobal/autopilotServiceDemo/arm_takeOff")
        self.global_widgets["arm_takeoff_btn"].config(text="Despegando...", fg="black", bg="yellow")

    def _global_land(self):
        self._global_publish("interfazGlobal/autopilotServiceDemo/Land")
        self.global_widgets["land_btn"].config(text="Aterrizando ...", fg="black", bg="yellow")

    def _global_rtl(self):
        self._global_publish("interfazGlobal/autopilotServiceDemo/RTL")
        self.global_widgets["rtl_btn"].config(text="Retornando ...", fg="black", bg="yellow")

    def _global_go(self, direction, btn):
        if self.global_previous_btn is not None:
            self.global_previous_btn.config(fg="white", bg="purple")

        self._global_publish("interfazGlobal/autopilotServiceDemo/go", direction)
        btn.config(fg="white", bg="green")
        self.global_previous_btn = btn

    def _global_start_telem(self):
        self._global_publish("interfazGlobal/autopilotServiceDemo/startTelemetry")

    def _global_stop_telem(self):
        self._global_publish("interfazGlobal/autopilotServiceDemo/stopTelemetry")

    def _global_change_heading(self, _event):
        value = int(self.global_widgets["heading_sldr"].get())
        self._global_publish("interfazGlobal/autopilotServiceDemo/changeHeading", str(value))

    def _global_change_speed(self, _event):
        value = float(self.global_widgets["speed_sldr"].get())
        self._global_publish("interfazGlobal/autopilotServiceDemo/changeNavSpeed", str(value))

    def _global_on_connect(self, _client, _userdata, _flags, rc):
        if rc == 0:
            print("connected OK Returned code=", rc)
        else:
            print("Bad connection Returned code=", rc)

    def _global_show_telemetry(self, telemetry_info):
        self.global_widgets["alt_show"].config(text=round(telemetry_info["alt"], 2))
        self.global_widgets["heading_show"].config(text=round(telemetry_info["heading"], 2))
        self.global_widgets["state_show"].config(text=telemetry_info["state"])

    def _global_reset_buttons(self):
        if not self.global_widgets:
            return
        self.global_widgets["arm_takeoff_btn"].config(text="Armar", fg="white", bg="purple")
        self.global_widgets["land_btn"].config(text="Aterrizar", fg="white", bg="purple")
        self.global_widgets["rtl_btn"].config(text="RTL", fg="white", bg="purple")
        if self.global_previous_btn is not None:
            self.global_previous_btn.config(fg="white", bg="purple")

    def _global_on_message(self, _client, _userdata, message):
        topic = message.topic

        if topic == "Grup2/autopilotServiceDemo/interfazGlobal/telemetryInfo":
            telemetry_info = json.loads(message.payload)
            self._global_show_telemetry(telemetry_info)

        if topic == "Grup2/autopilotServiceDemo/interfazGlobal/connected":
            self.global_widgets["connect_btn"].config(text="Conectado", fg="white", bg="green")

        if topic == "Grup2/autopilotServiceDemo/interfazGlobal/flying":
            self.global_widgets["arm_takeoff_btn"].config(text="En el aire", fg="white", bg="green")

        if topic == "Grup2/autopilotServiceDemo/interfazGlobal/landed":
            self.global_widgets["land_btn"].config(text="En tierra", fg="white", bg="green")
            self.root.after(5000, self._global_reset_buttons)

        if topic == "Grup2/autopilotServiceDemo/interfazGlobal/atHome":
            self.global_widgets["rtl_btn"].config(text="En tierra", fg="white", bg="green")
            self.root.after(5000, self._global_reset_buttons)


if __name__ == "__main__":
    main_root = tk.Tk()
    app = DashboardAllApp(main_root)
    main_root.mainloop()

