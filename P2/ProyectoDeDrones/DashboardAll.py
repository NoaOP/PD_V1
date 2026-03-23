import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import atexit
from tkinter import messagebox


import paho.mqtt.client as mqtt
from dronLink.Dron import Dron




import cv2
import numpy as np
import torch
from aiortc import MediaStreamTrack, RTCPeerConnection
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
from PIL import Image, ImageTk


try:
   import tkintermapview
   MAP_DEPS_OK = True
except Exception:
   tkintermapview = None
   MAP_DEPS_OK = False


try:
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

# Subset de COCO disponible para deteccion simultanea en local y global.
COCO_SUBSET = [
   ("Persona", 0),
   ("Perro", 16),
   ("Banana", 46),
   ("Naranja", 49),
   ("Pizza", 53),
   ("Pastel", 55),
   ("Reloj", 74),
]
COCO_ID_TO_LABEL = {obj_id: label for label, obj_id in COCO_SUBSET}

if os.name == "nt":
   import ctypes


   _MUTEX_ALREADY_EXISTS = 183
   _single_instance_mutex = None


   def _acquire_single_instance_lock():
       global _single_instance_mutex
       if _single_instance_mutex:
           return True


       mutex_name = "Global\\DashboardAll_P2_LocalModeLock"
       mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
       if not mutex_handle:
           return True


       if ctypes.windll.kernel32.GetLastError() == _MUTEX_ALREADY_EXISTS:
           ctypes.windll.kernel32.CloseHandle(mutex_handle)
           return False


       _single_instance_mutex = mutex_handle
       return True


   def _release_single_instance_lock():
       global _single_instance_mutex
       if _single_instance_mutex:
           ctypes.windll.kernel32.CloseHandle(_single_instance_mutex)
           _single_instance_mutex = None
else:
   def _acquire_single_instance_lock():
       return True


   def _release_single_instance_lock():
       return




class LocalDetector:
   def __init__(self):
       self.model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
       self.model.eval()


   def detect(self, frame, object_ids):
       if not object_ids:
           return []
       img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       results = self.model(img_rgb)
       detections = []
       for *box, _conf, cls in results.xyxy[0]:
           class_id = int(cls.item())
           if class_id in object_ids:
               x1, y1, x2, y2 = map(int, box)
               detections.append((class_id, (x1, y1, x2, y2)))
       return detections


class LocalVideoReceiver:
   def __init__(self, object_getter, stop_event, window_title):
       self.object_getter = object_getter
       self.stop_event = stop_event
       self.window_title = window_title
       self.detector = LocalDetector()

   async def handle_track(self, track):
       frame_count = 0
       detections = []

       while not self.stop_event.is_set():
           try:
               frame = await asyncio.wait_for(track.recv(), timeout=5.0)
               frame_count += 1

               if isinstance(frame, VideoFrame):
                   frame = frame.to_ndarray(format="bgr24")
               elif not isinstance(frame, np.ndarray):
                   continue

               selected_ids = set(self.object_getter())
               if selected_ids and frame_count % 8 == 0:
                   detections = self.detector.detect(frame, selected_ids)
               elif not selected_ids:
                   detections = []

               for class_id, (x1, y1, x2, y2) in detections:
                   label = COCO_ID_TO_LABEL.get(class_id, str(class_id))
                   cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                   cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

               cv2.imshow(self.window_title, frame)
               if cv2.waitKey(1) & 0xFF == ord("q"):
                   self.stop_event.set()
                   break
           except asyncio.TimeoutError:
               continue
           except Exception:
               break




class DashboardAllApp:
   def __init__(self, root, start_mode="local", owns_local_lock=False):
       self.root = root
       self.root.title("Dashboard All (Local / Global)")
       self.root.protocol("WM_DELETE_WINDOW", self._on_close)


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
       self.local_selected_objects = set()
       self.local_detect_vars = {}

       self.global_video_thread = None
       self.global_video_stop_event = threading.Event()
       self.global_selected_objects = set()
       self.global_detect_vars = {}

       self.local_color = "purple"
       self.global_color = "cadetblue"


       self.base_dir = os.path.dirname(os.path.abspath(__file__))
       self.autopilot_process = None
       self.camera_process = None
       self.autopilot_status = False
       self.camera_status = False
       self.status_poll_job = None
       self.local_lock_owned = bool(owns_local_lock)


       self.map_widget = None
       self.map_marker = None
       self.map_status_label = None
       self.last_local_telemetry = None
       self.last_global_telemetry = None
       self.global_map_target = None
       self.global_mqtt_connected = False


       self._build_shell()
       self.switch_mode(start_mode)
       self._schedule_service_monitor()
       #self.icon_image = ImageTk.PhotoImage(Image.open(os.path.join(self.base_dir, "DronPng.png")).resize((30, 30)))

       icon_path = os.path.join(self.base_dir, "DronPng.png")
       try:
           self.base_dron_image = Image.open(icon_path).resize((30, 30))
       except FileNotFoundError:
           print(f"Error: No se encontró el icono en {icon_path}")
           self.base_dron_image = None  # Manejo de error si no hay imagen





       self.current_rotated_icon = None
       self.drone_path_positions = []
       self.map_path_line = None



   def _build_shell(self):
       self.root.rowconfigure(1, weight=1)
       self.root.columnconfigure(0, weight=1)


       header = tk.Frame(self.root)
       header.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=8, pady=8)
       header.columnconfigure(0, weight=1)
       header.columnconfigure(1, weight=1)
       header.columnconfigure(2, weight=1)


       self.local_mode_btn = tk.Button(header, text="Mode Local", bg=self.local_color, fg="white", command=lambda: self.switch_mode("local"))
       self.local_mode_btn.grid(row=0, column=0, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)


       self.global_mode_btn = tk.Button(header, text="Mode Global", bg=self.local_color, fg="white", command=lambda: self.switch_mode("global"))
       self.global_mode_btn.grid(row=0, column=1, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)


       self.mode_label = tk.Label(header, text="")
       self.mode_label.grid(row=0, column=2, padx=4, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)


       self.content_frame = tk.Frame(self.root)
       self.content_frame.grid(row=1, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=8, pady=8)
       self.content_frame.rowconfigure(0, weight=1)
       self.content_frame.columnconfigure(0, weight=1)


   def _run_on_ui_thread(self, callback, *args, **kwargs):
       self.root.after(0, lambda: callback(*args, **kwargs))


   def _reset_map(self):
       self.map_widget = None
       self.map_marker = None
       self.map_status_label = None


   def _extract_lat_lon(self, telemetry_info):
       lat = telemetry_info.get("lat", telemetry_info.get("latitude"))
       lon = telemetry_info.get("lon", telemetry_info.get("longitude"))
       try:
           return float(lat), float(lon)
       except (TypeError, ValueError):
           return None, None


   def _build_map_section(self, parent):
       map_frame = tk.LabelFrame(parent, text="Mapa geolocalitzat")
       map_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       map_frame.rowconfigure(0, weight=1)
       map_frame.columnconfigure(0, weight=1)


       if MAP_DEPS_OK:
           self.map_widget = tkintermapview.TkinterMapView(map_frame, corner_radius=0)
           self.map_widget.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
           self.map_widget.set_zoom(16)
           self.map_widget.set_position(41.2756, 1.9872)
           self.map_widget.add_left_click_map_command(self._on_map_click)
           self.map_status_label = tk.Label(map_frame, text="Click al mapa per enviar el dron")
           self.map_status_label.grid(row=1, column=0, padx=5, pady=4, sticky=tk.W)
       else:
           self.map_widget = None
           self.map_status_label = tk.Label(
               map_frame,
               text="Instala tkintermapview per veure el mapa (pip install tkintermapview)",
               anchor="w",
               justify=tk.LEFT,
           )
           self.map_status_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


   def _get_target_altitude(self):
       telem = self.last_local_telemetry if self.mode == "local" else self.last_global_telemetry
       try:
           alt = float(telem.get("alt", 0)) if telem else 0.0
       except (TypeError, ValueError, AttributeError):
           alt = 0.0
       return max(alt, 3.0)


   def _on_map_click(self, coordinates):
       if not coordinates or len(coordinates) != 2:
           return


       lat, lon = coordinates
       alt = self._get_target_altitude()


       if self.mode == "local":
           lat_entry = self.local_widgets.get("goto_lat_entry")
           lon_entry = self.local_widgets.get("goto_lon_entry")
           alt_entry = self.local_widgets.get("goto_alt_entry")
           goto_btn = self.local_widgets.get("goto_btn")


           if lat_entry is None or lon_entry is None or alt_entry is None or goto_btn is None:
               self._safe_widget_config(self.map_status_label, text="Go To local no disponible")
               return


           lat_entry.delete(0, tk.END)
           lat_entry.insert(0, f"{lat:.7f}")


           lon_entry.delete(0, tk.END)
           lon_entry.insert(0, f"{lon:.7f}")


           # Per defecte, manté l'altitud actual del dron si hi ha telemetria.
           if self.last_local_telemetry is not None:
               try:
                   current_alt = float(self.last_local_telemetry.get("alt", alt))
                   alt_entry.delete(0, tk.END)
                   alt_entry.insert(0, f"{current_alt:.2f}")
               except (TypeError, ValueError):
                   pass


           self._local_goto(lat_entry, lon_entry, alt_entry, goto_btn)
           self._safe_widget_config(self.map_status_label, text=f"Go to local: {lat:.6f}, {lon:.6f}")
           return


       if self.mode == "global":
           if not self._global_autopilot_available():
               self._safe_widget_config(self.map_status_label, text="Autopilot global tancat")
               return
           self.global_map_target = (float(lat), float(lon))
           self._safe_widget_config(self.map_status_label, text=f"Objectiu global: {lat:.6f}, {lon:.6f}")


   def _get_global_go_direction(self, current_lat, current_lon, target_lat, target_lon):
       lat_err = target_lat - current_lat
       lon_err = target_lon - current_lon
       eps = 0.000015  # ~1.5 m tolerance


       if abs(lat_err) <= eps and abs(lon_err) <= eps:
           return "Stop", True


       ns = "North" if lat_err > eps else ("South" if lat_err < -eps else "")
       ew = "East" if lon_err > eps else ("West" if lon_err < -eps else "")


       if ns and ew:
           return f"{ns}{ew}", False
       if ns:
           return ns, False
       if ew:
           return ew, False
       return "Stop", False




   def _update_map_from_telemetry(self, telemetry_info):
       if self.map_widget is None:
           return

       lat, lon = self._extract_lat_lon(telemetry_info)
       heading = telemetry_info.get("heading", 0)

       if lat is None or lon is None:
           return

       self.map_widget.delete_all_marker()

       self.drone_path_positions.append((lat, lon))
       if len(self.drone_path_positions) > 1:
           if self.map_path_line is not None:
               self.map_path_line.delete()
           self.map_path_line = self.map_widget.set_path(self.drone_path_positions,color="blue")

       if self.base_dron_image:
           pil_rotated = self.base_dron_image.rotate(-heading, expand=True)
           self.current_rotated_icon = ImageTk.PhotoImage(pil_rotated)

       self.map_marker = self.map_widget.set_marker(lat,lon,icon=self.current_rotated_icon)

       self.map_widget.set_position(lat, lon)


   def _drive_global_to_map_target(self, telemetry_info):
       if self.global_map_target is None:
           return


       lat, lon = self._extract_lat_lon(telemetry_info)
       if lat is None or lon is None:
           return


       if telemetry_info.get("state") != "flying":
           self._safe_widget_config(self.map_status_label, text="Objectiu guardat, esperant vol")
           return


       target_lat, target_lon = self.global_map_target
       direction, reached = self._get_global_go_direction(lat, lon, target_lat, target_lon)


       if reached:
           self._global_publish("interfazGlobal/autopilotServiceDemo/go", "Stop")
           self.global_map_target = None
           self._safe_widget_config(self.map_status_label, text="Objectiu assolit")
           return


       self._global_publish("interfazGlobal/autopilotServiceDemo/go", direction)
       self._safe_widget_config(self.map_status_label, text=f"Anant cap a objectiu ({direction})")


   def _safe_widget_config(self, widget, **kwargs):
       if widget is None:
           return False
       try:
           if int(widget.winfo_exists()) != 1:
               return False
           widget.config(**kwargs)
           return True
       except tk.TclError:
           return False


   def _refresh_service_status_labels(self):
       local_info_label = self.local_widgets.get("services_info_label") if self.local_widgets else None
       if not self._safe_widget_config(
           local_info_label,
           text=f"Autopilot: {'OBERT' if self.autopilot_status else 'TANCAT'} | Camera: {'OBERT' if self.camera_status else 'TANCAT'}",
           fg="green" if (self.autopilot_status or self.camera_status) else "red",
       ) and self.local_widgets:
           self.local_widgets["services_info_label"] = None


       global_autopilot_status = self.global_widgets.get("autopilot_status_label") if self.global_widgets else None
       if not self._safe_widget_config(
           global_autopilot_status,
           text=f"Autopilot: {'OBERT' if self.autopilot_status else 'TANCAT'}",
           fg="green" if self.autopilot_status else "red",
       ) and self.global_widgets:
           self.global_widgets["autopilot_status_label"] = None


       global_camera_status = self.global_widgets.get("camera_status_label") if self.global_widgets else None
       if not self._safe_widget_config(
           global_camera_status,
           text=f"Camera: {'OBERT' if self.camera_status else 'TANCAT'}",
           fg="green" if self.camera_status else "red",
       ) and self.global_widgets:
           self.global_widgets["camera_status_label"] = None


   def _is_script_running(self, script_name):
       if os.name != "nt":
           return False


       # Read process command-lines to detect services started outside this app.
       ps_command = (
           "(Get-CimInstance Win32_Process | "
           f"Where-Object {{ $_.CommandLine -like '*{script_name}*' }} | "
           "Measure-Object).Count"
       )


       try:
           creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
           result = subprocess.run(
               ["powershell", "-NoProfile", "-Command", ps_command],
               capture_output=True,
               text=True,
               timeout=2,
               creationflags=creationflags,
           )
           count_text = result.stdout.strip().splitlines()
           count = int(count_text[-1]) if count_text else 0
           return count > 0
       except Exception:
           return False


   def _is_camera_port_open(self):
       try:
           with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
               sock.settimeout(0.3)
               return sock.connect_ex(("127.0.0.1", 9999)) == 0
       except Exception:
           return False


   def _update_service_status_from_system(self):
       # Track only processes launched/owned by this dashboard to avoid false positives.
       autopilot_on = self.autopilot_process is not None and self.autopilot_process.poll() is None
       camera_on = self.camera_process is not None and self.camera_process.poll() is None
       self._set_service_status(autopilot_on, camera_on)


   def _schedule_service_monitor(self):
       self._update_service_status_from_system()
       self.status_poll_job = self.root.after(3000, self._schedule_service_monitor)


   def _manual_start_autopilot(self):
       self.autopilot_process, _ = self._start_service_process("AutopilotService.py", self.autopilot_process, show_console=True)
       self._update_service_status_from_system()


   def _manual_start_camera(self):
       self.camera_process, _ = self._start_service_process("CameraService.py", self.camera_process, show_console=True)
       self._update_service_status_from_system()


   def _set_service_status(self, autopilot_on=None, camera_on=None):
       if autopilot_on is not None:
           self.autopilot_status = bool(autopilot_on)
       if camera_on is not None:
           self.camera_status = bool(camera_on)
       self._refresh_service_status_labels()


   def switch_mode(self, mode):
       if self.mode == mode:
           return


       # Local mode is exclusive across processes.
       if mode == "local" and not self.local_lock_owned:
           if not _acquire_single_instance_lock():
               messagebox.showwarning("Mode local ocupat", "Ja hi ha una instancia en mode local oberta.")
               return
           self.local_lock_owned = True


       previous_mode = self.mode
       self._cleanup_mode()


       if previous_mode == "local" and mode != "local" and self.local_lock_owned:
           _release_single_instance_lock()
           self.local_lock_owned = False


       self.mode = mode


       # Drop stale widget references before creating the new view.
       self.local_widgets = {}
       self.global_widgets = {}


       for widget in self.content_frame.winfo_children():
           widget.destroy()


       if mode == "local":
           self.mode_label.config(text="Actiu: Local")
           self.local_mode_btn.config(bg=self.local_color, fg="white")
           self.global_mode_btn.config(bg=self.global_color, fg="black")
           self._build_local_view()
           self._start_local_services()
       else:
           self.mode_label.config(text="Actiu: Global")
           self.local_mode_btn.config(bg=self.local_color, fg="white")
           self.global_mode_btn.config(bg=self.global_color, fg="white")
           self._build_global_view()
           self._update_service_status_from_system()


   def _cleanup_mode(self):
       if self.mode == "local":
           if self.local_dron is not None:
               try:
                   self.local_dron.stop_sending_telemetry_info()
               except Exception:
                   pass
           self._stop_local_video()
           self._stop_local_services()

       if self.mode == "global":
           self._stop_global_video()
           # Limpiar telemetría local si estaba activa
           if self.local_dron is not None:
               try:
                   self.local_dron.stop_sending_telemetry_info()
               except Exception:
                   pass


           if self.global_client is not None:
               try:
                   self.global_client.disconnect()
               except Exception:
                   pass
               try:
                   self.global_client.loop_stop(force=False)
               except (KeyboardInterrupt, Exception):
                   pass
               self.global_client = None


   def _start_service_process(self, script_name, current_process, show_console=False):
       if current_process is not None and current_process.poll() is None:
           return current_process, True


       script_path = os.path.join(self.base_dir, script_name)
       if not os.path.exists(script_path):
           return None, False


       try:
           if os.name == "nt":
               creationflags = subprocess.CREATE_NEW_CONSOLE if show_console else subprocess.CREATE_NO_WINDOW
           else:
               creationflags = 0


           process = subprocess.Popen(
               [sys.executable, "-u", script_path],
               cwd=self.base_dir,
               stdout=None if show_console else subprocess.DEVNULL,
               stderr=None if show_console else subprocess.DEVNULL,
               creationflags=creationflags,
           )
           time.sleep(0.8)
           if process.poll() is not None:
               return None, False
           return process, True
       except Exception:
           return None, False


   def _start_local_services(self):
       failed_services = []


       self.autopilot_process, autopilot_ok = self._start_service_process("AutopilotService.py", self.autopilot_process)
       if not autopilot_ok:
           failed_services.append("autopilot")


       self.camera_process, camera_ok = self._start_service_process("CameraService.py", self.camera_process)
       if not camera_ok:
           failed_services.append("camera")


       self._update_service_status_from_system()


       if failed_services:
           self.mode_label.config(text=f"Actiu: Local (error: {', '.join(failed_services)})")


   def _stop_process(self, process):
       if process is None:
           return
       if process.poll() is not None:
           return


       try:
           process.terminate()
           process.wait(timeout=1)
       except Exception:
           try:
               process.kill()
               process.wait(timeout=1)
           except Exception:
               pass


   def _stop_local_services(self):
       self._stop_process(self.autopilot_process)
       self._stop_process(self.camera_process)
       self.autopilot_process = None
       self.camera_process = None
       self._update_service_status_from_system()


   def _on_close(self):
       if self.status_poll_job is not None:
           try:
               self.root.after_cancel(self.status_poll_job)
           except Exception:
               pass
           self.status_poll_job = None


       self._cleanup_mode()
       self._stop_local_services()


       if self.local_lock_owned:
           _release_single_instance_lock()
           self.local_lock_owned = False


       self.root.destroy()


   def _build_local_view(self):
       # Limpiar telemetría global si estaba activa abans de canviar a mode local
       if self.global_client is not None:
           try:
               self.global_client.disconnect()
           except Exception:
               pass
           try:
               self.global_client.loop_stop(force=False)
           except Exception:
               pass
           self.global_client = None


       self.local_dron = Dron()
       self.local_previous_btn = None
       self.local_widgets = {}
       self._reset_map()


       panel = tk.Frame(self.content_frame)
       panel.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)


       panel.rowconfigure(0, weight=1)
       panel.columnconfigure(0, weight=1)
       panel.columnconfigure(1, weight=1)
       panel.columnconfigure(2, weight=2)


       # LEFT COLUMN: Controls and Telemetry
       left_panel = tk.Frame(panel)
       left_panel.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=5, pady=5)
       for idx in range(10):
           left_panel.rowconfigure(idx, weight=0)
       left_panel.columnconfigure(0, weight=1)


       connect_btn = tk.Button(left_panel, text="Conectar", bg=self.local_color, fg="white", command=self._local_connect)
       connect_btn.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       arm_btn = tk.Button(left_panel, text="Armar", bg=self.local_color, fg="white", command=self._local_arm)
       arm_btn.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       takeoff_btn = tk.Button(left_panel, text="Despegar", bg=self.local_color, fg="white", command=self._local_takeoff)
       takeoff_btn.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       land_btn = tk.Button(left_panel, text="Aterrizar", bg=self.local_color, fg="white", command=self._local_land)
       land_btn.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       rtl_btn = tk.Button(left_panel, text="RTL", bg=self.local_color, fg="white", command=self._local_rtl)
       rtl_btn.grid(row=4, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       heading_sldr = tk.Scale(left_panel, label="Grados:", resolution=5, from_=0, to=360, tickinterval=45, orient=tk.HORIZONTAL)
       heading_sldr.grid(row=5, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       heading_sldr.bind("<ButtonRelease-1>", self._local_change_heading)


       speed_sldr = tk.Scale(left_panel, label="Velocidad (m/s):", resolution=1, from_=0, to=20, tickinterval=5, orient=tk.HORIZONTAL)
       speed_sldr.grid(row=6, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       speed_sldr.bind("<ButtonRelease-1>", self._local_change_speed)


       start_telem_btn = tk.Button(left_panel, text="Empezar telemetria", bg=self.local_color, fg="white", command=self._local_start_telem)
       start_telem_btn.grid(row=7, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       stop_telem_btn = tk.Button(left_panel, text="Parar telemetria", bg=self.local_color, fg="white", command=self._local_stop_telem)
       stop_telem_btn.grid(row=8, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       telemetry_frame = tk.LabelFrame(left_panel, text="Telemetria")
       telemetry_frame.grid(row=9, column=0, padx=5, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)
       self._build_local_telemetry(telemetry_frame)


       # RIGHT COLUMN: Navigation, GoTo, Video and Detection
       right_panel = tk.Frame(panel)
       right_panel.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W, padx=5, pady=5)
       right_panel.rowconfigure(0, weight=0)
       right_panel.rowconfigure(1, weight=0)
       right_panel.rowconfigure(2, weight=0)
       right_panel.rowconfigure(3, weight=0)
       right_panel.rowconfigure(4, weight=0)
       right_panel.columnconfigure(0, weight=1)


       nav_frame = tk.LabelFrame(right_panel, text="Navegacion")
       nav_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       self._build_nav_buttons(nav_frame, self._local_go)


       goto_frame = tk.LabelFrame(right_panel, text="Go To")
       goto_frame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       goto_frame.columnconfigure(0, weight=1)
       goto_frame.columnconfigure(1, weight=1)


       lat_label = tk.Label(goto_frame, text="Lat")
       lat_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.W)
       lat_entry = tk.Entry(goto_frame, width=10)
       lat_entry.grid(row=0, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.E + tk.W)


       lon_label = tk.Label(goto_frame, text="Lon")
       lon_label.grid(row=1, column=0, padx=3, pady=3, sticky=tk.W)
       lon_entry = tk.Entry(goto_frame, width=10)
       lon_entry.grid(row=1, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.E + tk.W)


       alt_label = tk.Label(goto_frame, text="Alt")
       alt_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.W)
       alt_entry = tk.Entry(goto_frame, width=10)
       alt_entry.grid(row=2, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.E + tk.W)


       goto_btn = tk.Button(goto_frame, text="Go to", bg=self.local_color, fg="white", command=lambda: self._local_goto(lat_entry, lon_entry, alt_entry, goto_btn))
       goto_btn.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       video_btn = tk.Button(right_panel, text="Recibir video por WebRTC", bg=self.local_color, fg="white", command=self._local_start_video)
       video_btn.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       detect_frame = tk.LabelFrame(right_panel, text="Deteccion de objects")
       detect_frame.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       for idx in range(4):
           detect_frame.columnconfigure(idx, weight=1)

       self.local_detect_vars = {}
       for idx, (label, object_id) in enumerate(COCO_SUBSET):
           var = tk.IntVar(value=0)
           self.local_detect_vars[object_id] = var
           tk.Checkbutton(detect_frame, text=label, variable=var, anchor="w").grid(
               row=idx // 4,
               column=idx % 4,
               padx=2,
               pady=2,
               sticky=tk.N + tk.S + tk.E + tk.W,
           )

       tk.Button(
           detect_frame,
           text="Sin deteccion",
           bg=self.local_color,
           fg="white",
           command=lambda: self._clear_detection_selection("local"),
       ).grid(row=(len(COCO_SUBSET) // 4) + 1, column=0, columnspan=4, padx=2, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

       services_info_label = tk.Label(right_panel, text="", anchor="w")
       services_info_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       map_panel = tk.Frame(panel)
       map_panel.grid(row=0, column=2, sticky=tk.N + tk.S + tk.E + tk.W, padx=5, pady=5)
       map_panel.rowconfigure(0, weight=1)
       map_panel.columnconfigure(0, weight=1)
       self._build_map_section(map_panel)


       self.local_widgets = {
           "connect_btn": connect_btn,
           "arm_btn": arm_btn,
           "takeoff_btn": takeoff_btn,
           "land_btn": land_btn,
           "rtl_btn": rtl_btn,
           "heading_sldr": heading_sldr,
           "speed_sldr": speed_sldr,
           "goto_lat_entry": lat_entry,
           "goto_lon_entry": lon_entry,
           "goto_alt_entry": alt_entry,
           "goto_btn": goto_btn,
           "alt_show": self.local_widgets.get("alt_show"),
           "heading_show": self.local_widgets.get("heading_show"),
           "state_show": self.local_widgets.get("state_show"),
           "speed_show": self.local_widgets.get("speed_show"),
           "mode_show": self.local_widgets.get("mode_show"),
           "video_btn": video_btn,
           "services_info_label": services_info_label,
       }
       self._refresh_service_status_labels()


   def _build_global_view(self):
       self.global_previous_btn = None
       self.global_widgets = {}
       self._reset_map()


       # Limpiar telemetría local si estaba activa abans de canviar a mode global
       if self.local_dron is not None:
           try:
               self.local_dron.stop_sending_telemetry_info()
           except Exception:
               pass


       self.global_client = mqtt.Client("InterfazGlobal", transport="websockets")
       self.global_client.username_pw_set("dronsEETAC", "mimara1456.")
       self.global_client.on_message = self._global_on_message
       self.global_client.on_connect = self._global_on_connect
       self.global_client.connect("dronseetac.upc.edu", 8000)
       self.global_client.subscribe("Grup2/autopilotServiceDemo/interfazGlobal/#")
       self.global_client.loop_start()


       panel = tk.Frame(self.content_frame)
       panel.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)


       panel.rowconfigure(0, weight=1)
       panel.columnconfigure(0, weight=1)
       panel.columnconfigure(1, weight=1)
       panel.columnconfigure(2, weight=2)


       # LEFT COLUMN: Controls and Telemetry
       left_panel = tk.Frame(panel)
       left_panel.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=5, pady=5)
       for idx in range(10):
           left_panel.rowconfigure(idx, weight=0)
       left_panel.columnconfigure(0, weight=1)


       connect_btn = tk.Button(left_panel, text="Conectar", bg=self.global_color, fg="white", command=self._global_connect)
       connect_btn.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       arm_takeoff_btn = tk.Button(left_panel, text="Despegar", bg=self.global_color, fg="white", command=self._global_takeoff)
       arm_takeoff_btn.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       land_btn = tk.Button(left_panel, text="Aterrizar", bg=self.global_color, fg="white", command=self._global_land)
       land_btn.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       rtl_btn = tk.Button(left_panel, text="RTL", bg=self.global_color, fg="white", command=self._global_rtl)
       rtl_btn.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       heading_sldr = tk.Scale(left_panel, label="Grados:", resolution=5, from_=0, to=360, tickinterval=45, orient=tk.HORIZONTAL)
       heading_sldr.grid(row=4, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       heading_sldr.bind("<ButtonRelease-1>", self._global_change_heading)


       speed_sldr = tk.Scale(left_panel, label="Velocidad (m/s):", resolution=1, from_=0, to=20, tickinterval=5, orient=tk.HORIZONTAL)
       speed_sldr.grid(row=5, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       speed_sldr.bind("<ButtonRelease-1>", self._global_change_speed)


       start_telem_btn = tk.Button(left_panel, text="Empezar telemetria", bg=self.global_color, fg="white", command=self._global_start_telem)
       start_telem_btn.grid(row=6, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       stop_telem_btn = tk.Button(left_panel, text="Parar telemetria", bg=self.global_color, fg="white", command=self._global_stop_telem)
       stop_telem_btn.grid(row=7, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       telemetry_frame = tk.LabelFrame(left_panel, text="Telemetria")
       telemetry_frame.grid(row=8, column=0, padx=5, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)
       self._build_global_telemetry(telemetry_frame)


       # RIGHT COLUMN: Navigation, Services, Video and Detection
       right_panel = tk.Frame(panel)
       right_panel.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W, padx=5, pady=5)
       right_panel.rowconfigure(0, weight=0)
       right_panel.rowconfigure(1, weight=0)
       right_panel.rowconfigure(2, weight=0)
       right_panel.rowconfigure(3, weight=0)
       right_panel.columnconfigure(0, weight=1)


       nav_frame = tk.LabelFrame(right_panel, text="Navegacion")
       nav_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       self._build_nav_buttons(nav_frame, self._global_go)


       services_frame = tk.LabelFrame(right_panel, text="Serveis manuals (Global)")
       services_frame.grid(row=1, column=0, padx=5, pady=8, sticky=tk.N + tk.S + tk.E + tk.W)
       services_frame.columnconfigure(0, weight=1)
       services_frame.columnconfigure(1, weight=1)


       open_autopilot_btn = tk.Button(
           services_frame,
           text="Obrir AutopilotService",
           bg=self.global_color,
           fg="white",
           command=self._manual_start_autopilot,
       )
       open_autopilot_btn.grid(row=0, column=0, padx=5, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)


       open_camera_btn = tk.Button(
           services_frame,
           text="Obrir CameraService",
           bg=self.global_color,
           fg="white",
           command=self._manual_start_camera,
       )
       open_camera_btn.grid(row=0, column=1, padx=5, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)


       autopilot_status_label = tk.Label(services_frame, text="Autopilot: TANCAT", fg="red")
       autopilot_status_label.grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)


       camera_status_label = tk.Label(services_frame, text="Camera: TANCAT", fg="red")
       camera_status_label.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)


       global_video_btn = tk.Button(
           right_panel,
           text="Recibir video por WebRTC",
           bg=self.global_color,
           fg="white",
           command=self._global_start_video,
       )
       global_video_btn.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


       global_detect_frame = tk.LabelFrame(right_panel, text="Deteccion de objects")
       global_detect_frame.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
       for idx in range(4):
           global_detect_frame.columnconfigure(idx, weight=1)

       self.global_detect_vars = {}
       for idx, (label, object_id) in enumerate(COCO_SUBSET):
           var = tk.IntVar(value=0)
           self.global_detect_vars[object_id] = var
           tk.Checkbutton(global_detect_frame, text=label, variable=var, anchor="w").grid(
               row=idx // 4,
               column=idx % 4,
               padx=2,
               pady=2,
               sticky=tk.N + tk.S + tk.E + tk.W,
           )

       tk.Button(
           global_detect_frame,
           text="Sin deteccion",
           bg=self.global_color,
           fg="white",
           command=lambda: self._clear_detection_selection("global"),
       ).grid(row=(len(COCO_SUBSET) // 4) + 1, column=0, columnspan=4, padx=2, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

       map_panel = tk.Frame(panel)
       map_panel.grid(row=0, column=2, sticky=tk.N + tk.S + tk.E + tk.W, padx=5, pady=5)
       map_panel.rowconfigure(0, weight=1)
       map_panel.columnconfigure(0, weight=1)
       self._build_map_section(map_panel)


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
           "open_autopilot_btn": open_autopilot_btn,
           "open_camera_btn": open_camera_btn,
           "autopilot_status_label": autopilot_status_label,
           "camera_status_label": camera_status_label,
           "video_btn": global_video_btn,
       }
       self._refresh_service_status_labels()


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
           button_color = self.global_color if self.mode == "global" else self.local_color
           btn = tk.Button(nav_frame, text=text, bg=button_color, fg="white")
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


   # Local/Global camera and detection
   def _local_set_object(self, object_id):
       # Compatibilitat: toggle simple per mantenir crides existents.
       if object_id is None:
           self._clear_detection_selection("local")
           return
       if object_id in self.local_selected_objects:
           self.local_selected_objects.remove(object_id)
       else:
           self.local_selected_objects.add(object_id)
       if object_id in self.local_detect_vars:
           self.local_detect_vars[object_id].set(1 if object_id in self.local_selected_objects else 0)

   def _global_set_object(self, object_id):
       if object_id is None:
           self._clear_detection_selection("global")
           return
       if object_id in self.global_selected_objects:
           self.global_selected_objects.remove(object_id)
       else:
           self.global_selected_objects.add(object_id)
       if object_id in self.global_detect_vars:
           self.global_detect_vars[object_id].set(1 if object_id in self.global_selected_objects else 0)

   def _clear_detection_selection(self, mode):
       if mode == "local":
           for var in self.local_detect_vars.values():
               var.set(0)
           self.local_selected_objects.clear()
       else:
           for var in self.global_detect_vars.values():
               var.set(0)
           self.global_selected_objects.clear()

   def _get_selected_object_ids(self, mode):
       vars_map = self.local_detect_vars if mode == "local" else self.global_detect_vars
       selected = {obj_id for obj_id, var in vars_map.items() if var.get() == 1}
       if mode == "local":
           self.local_selected_objects = selected
       else:
           self.global_selected_objects = selected
       return selected

   def _local_start_video(self):
       self._start_video("local")

   def _global_start_video(self):
       self._start_video("global")

   def _start_video(self, mode):
       if not VIDEO_DEPS_OK:
           widgets = self.local_widgets if mode == "local" else self.global_widgets
           color = self.local_color if mode == "local" else self.global_color
           if widgets.get("video_btn") is not None:
               widgets["video_btn"].config(text="Faltan deps video", bg="red", fg="white")
               widgets["video_btn"].after(1500, lambda: widgets["video_btn"].config(text="Recibir video por WebRTC", bg=color, fg="white"))
           return

       if mode == "local":
           if self.local_video_thread is not None and self.local_video_thread.is_alive():
               self.local_widgets["video_btn"].config(text="Video activo", bg="green", fg="white")
               return
           self.local_video_stop_event = threading.Event()
           self.local_video_thread = threading.Thread(target=self._local_video_thread_runner, daemon=True)
           self.local_video_thread.start()
           self.local_widgets["video_btn"].config(text="Video activo", bg="green", fg="white")
       else:
           if self.global_video_thread is not None and self.global_video_thread.is_alive():
               self.global_widgets["video_btn"].config(text="Video activo", bg="green", fg="white")
               return
           self.global_video_stop_event = threading.Event()
           self.global_video_thread = threading.Thread(target=self._global_video_thread_runner, daemon=True)
           self.global_video_thread.start()
           self.global_widgets["video_btn"].config(text="Video activo", bg="green", fg="white")

   def _local_video_thread_runner(self):
       try:
           asyncio.run(self._video_receiver("local"))
       finally:
           try:
               cv2.destroyAllWindows()
           except Exception:
               pass

   def _global_video_thread_runner(self):
       try:
           asyncio.run(self._video_receiver("global"))
       finally:
           try:
               cv2.destroyAllWindows()
           except Exception:
               pass

   async def _video_receiver(self, mode):

       try:
            signaling = TcpSocketSignaling("localhost", 9999)
            pc = RTCPeerConnection()
            stop_event = self.local_video_stop_event if mode == "local" else self.global_video_stop_event
            window_title = "Local Camera" if mode == "local" else "Global Camera"
            receiver = LocalVideoReceiver(lambda: self._get_selected_object_ids(mode), stop_event, window_title)

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

                while not stop_event.is_set() and pc.connectionState != "connected":
                    await asyncio.sleep(0.1)

                while not stop_event.is_set():
                    await asyncio.sleep(0.2)
            except Exception:
                pass
            finally:
                try:
                    await pc.close()
                except Exception:
                    pass

       except Exception as e:
         print(f"DEBUG VIDEO: Error conectando al signal: {e}")



   def _stop_local_video(self):
       self.local_video_stop_event.set()
       try:
           cv2.destroyWindow("Local Camera")
       except Exception:
           pass
       if self.local_widgets.get("video_btn") is not None:
           self.local_widgets["video_btn"].config(text="Recibir video por WebRTC", bg=self.local_color, fg="white")

   def _stop_global_video(self):
       self.global_video_stop_event.set()
       try:
           cv2.destroyWindow("Global Camera")
       except Exception:
           pass
       if self.global_widgets.get("video_btn") is not None:
           self.global_widgets["video_btn"].config(text="Recibir video por WebRTC", bg=self.global_color, fg="white")

   # Local handlers
   def _local_show_telemetry(self, telemetry_info):
       # Solo procesar si estamos en modo local y los widgets existen
       if self.mode != "local" or not self.local_widgets:
           return
       self.last_local_telemetry = telemetry_info
       if self.local_widgets.get("alt_show") is not None:
           self.local_widgets["alt_show"].config(text=round(telemetry_info["alt"], 2))
       if self.local_widgets.get("heading_show") is not None:
           self.local_widgets["heading_show"].config(text=round(telemetry_info["heading"], 2))
       if self.local_widgets.get("state_show") is not None:
           self.local_widgets["state_show"].config(text=telemetry_info["state"])
       if self.local_widgets.get("speed_show") is not None:
           self.local_widgets["speed_show"].config(text=round(telemetry_info["groundSpeed"], 2))
       if self.local_widgets.get("mode_show") is not None:
           self.local_widgets["mode_show"].config(text=telemetry_info["flightMode"])
       self._update_map_from_telemetry(telemetry_info)


   def _local_connect(self):
       # Create a fresh Dron instance just before connecting, exactly like P1
       self.local_dron = Dron()
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
       takeoff_btn.config(text="On the ground", fg="white", bg=self.local_color)
       self.root.after(1500, lambda: takeoff_btn.config(text="Despegar"))
       self.local_widgets["land_btn"].config(text="Land", fg="white", bg=self.local_color)


   def _local_on_ground_rtl(self):
       takeoff_btn = self.local_widgets["takeoff_btn"]
       self.local_widgets["rtl_btn"].config(text="On the ground", fg="white", bg=self.local_color)
       takeoff_btn.config(text="On the ground", fg="white", bg=self.local_color)
       self.root.after(1500, lambda: takeoff_btn.config(text="Despegar"))


   def _local_land(self):
       self.local_dron.Land(blocking=False, callback=self._local_on_ground_land)
       self.local_widgets["land_btn"].config(text="Landing", fg="white", bg="green")


   def _local_rtl(self):
       self.local_dron.RTL(blocking=False, callback=self._local_on_ground_rtl)
       self.local_widgets["rtl_btn"].config(text="Going back home", fg="white", bg="green")


   def _local_go(self, direction, btn):
       if self.local_previous_btn is not None:
           self.local_previous_btn.config(fg="white", bg=self.local_color)


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
           self.root.after(1000, lambda: goto_btn.config(text="Go to", bg=self.local_color))


   def _local_start_telem(self):
       self.local_dron.send_telemetry_info(lambda telemetry: self._run_on_ui_thread(self._local_show_telemetry, telemetry))


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


   def _global_autopilot_available(self):
       self._update_service_status_from_system()
       return self.autopilot_status


   def _global_connect(self):
       if not self._global_autopilot_available():
           self._safe_widget_config(self.global_widgets.get("connect_btn"), text="Autopilot tancat", fg="white", bg="red")
           return
       self._global_publish("interfazGlobal/autopilotServiceDemo/connect")
       self.global_widgets["connect_btn"].config(text="Conectado", fg="white", bg="green")
       self.global_widgets["speed_sldr"].set(1)


   def _global_takeoff(self):
       if not self._global_autopilot_available():
           self._safe_widget_config(self.global_widgets.get("arm_takeoff_btn"), text="Autopilot tancat", fg="white", bg="red")
           return
       self._global_publish("interfazGlobal/autopilotServiceDemo/arm_takeOff")
       self.global_widgets["arm_takeoff_btn"].config(text="Despegando...", fg="black", bg="yellow")


   def _global_land(self):
       if not self._global_autopilot_available():
           self._safe_widget_config(self.global_widgets.get("land_btn"), text="Autopilot tancat", fg="white", bg="red")
           return
       self._global_publish("interfazGlobal/autopilotServiceDemo/Land")
       self.global_widgets["land_btn"].config(text="Aterrizando ...", fg="black", bg="yellow")


   def _global_rtl(self):
       if not self._global_autopilot_available():
           self._safe_widget_config(self.global_widgets.get("rtl_btn"), text="Autopilot tancat", fg="white", bg="red")
           return
       self._global_publish("interfazGlobal/autopilotServiceDemo/RTL")
       self.global_widgets["rtl_btn"].config(text="Retornando ...", fg="black", bg="yellow")


   def _global_go(self, direction, btn):
       if not self._global_autopilot_available():
           return
       if self.global_previous_btn is not None:
           self.global_previous_btn.config(fg="white", bg=self.global_color)


       self._global_publish("interfazGlobal/autopilotServiceDemo/go", direction)
       btn.config(fg="white", bg="green")
       self.global_previous_btn = btn


   def _global_start_telem(self):
       self._global_publish("interfazGlobal/autopilotServiceDemo/startTelemetry")


   def _global_stop_telem(self):
       self._global_publish("interfazGlobal/autopilotServiceDemo/stopTelemetry")
       if self.global_widgets.get("alt_show") is not None:
           self.global_widgets["alt_show"].config(text="--")
       if self.global_widgets.get("heading_show") is not None:
           self.global_widgets["heading_show"].config(text="--")
       if self.global_widgets.get("state_show") is not None:
           self.global_widgets["state_show"].config(text="--")


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
       self.last_global_telemetry = telemetry_info
       if not self.global_widgets:
           return
       if self.global_widgets.get("alt_show") is not None:
           self.global_widgets["alt_show"].config(text=round(telemetry_info.get("alt", 0), 2))
       if self.global_widgets.get("heading_show") is not None:
           self.global_widgets["heading_show"].config(text=round(telemetry_info.get("heading", 0), 2))
       if self.global_widgets.get("state_show") is not None:
           self.global_widgets["state_show"].config(text=telemetry_info.get("state", "--"))
       self._update_map_from_telemetry(telemetry_info)
       self._drive_global_to_map_target(telemetry_info)


   def _global_reset_buttons(self):
       if not self.global_widgets:
           return
       self.global_widgets["arm_takeoff_btn"].config(text="Armar", fg="white", bg=self.global_color)
       self.global_widgets["land_btn"].config(text="Aterrizar", fg="white", bg=self.global_color)
       self.global_widgets["rtl_btn"].config(text="RTL", fg="white", bg=self.global_color)
       if self.global_previous_btn is not None:
           self.global_previous_btn.config(fg="white", bg=self.global_color)


   def _global_on_message(self, _client, _userdata, message):
       topic = message.topic


       if topic == "Grup2/autopilotServiceDemo/interfazGlobal/telemetryInfo":
           telemetry_info = json.loads(message.payload)
           self._run_on_ui_thread(self._global_show_telemetry, telemetry_info)


       if topic == "Grup2/autopilotServiceDemo/interfazGlobal/connected":
           self._run_on_ui_thread(self.global_widgets["connect_btn"].config, text="Conectado", fg="white", bg="green")


       if topic == "Grup2/autopilotServiceDemo/interfazGlobal/flying":
           self._run_on_ui_thread(self.global_widgets["arm_takeoff_btn"].config, text="En el aire", fg="white", bg="green")


       if topic == "Grup2/autopilotServiceDemo/interfazGlobal/landed":
           self._run_on_ui_thread(self.global_widgets["land_btn"].config, text="En tierra", fg="white", bg="green")
           self.root.after(5000, self._global_reset_buttons)


       if topic == "Grup2/autopilotServiceDemo/interfazGlobal/atHome":
           self._run_on_ui_thread(self.global_widgets["rtl_btn"].config, text="En tierra", fg="white", bg="green")
           self.root.after(5000, self._global_reset_buttons)




if __name__ == "__main__":
   parser = argparse.ArgumentParser(add_help=True)
   parser.add_argument("--mode", choices=["local", "global"], default="local")
   args = parser.parse_args()


   owns_local_lock = False
   if args.mode == "local":
       if not _acquire_single_instance_lock():
           warning_root = tk.Tk()
           warning_root.withdraw()
           messagebox.showwarning("Dashboard ja obert", "Ja hi ha una instancia del DashboardAll en Local oberta.")
           warning_root.destroy()
           sys.exit(0)
       owns_local_lock = True


   atexit.register(_release_single_instance_lock)


   main_root = tk.Tk()
   app = DashboardAllApp(main_root, start_mode=args.mode, owns_local_lock=owns_local_lock)
   main_root.mainloop()



