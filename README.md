> Aplicació web per controlar un dron en temps real, amb funcions de dibuix al mapa, control per veu, vídeo en directe i mode espectador sincronitzat.
Autors: Eric Sánchez, Noa Oliva, Elsa Milà i Mònica García  
Escola d'Enginyeria de Telecomunicació i Aeroespacial de Castelldefels (EETAC) — UPC  

---
Descripció del projecte
Aquest projecte és una WebApp completa de control de drons desenvolupada en HTML, CSS i JavaScript (frontend) i Python/Flask (backend). Permet controlar un dron real o simulat des del navegador, amb dos modes d'accés:
Mode Pilot — control total del dron, dibuix de trajectòries i configuració
Mode Espectador — visualització en temps real del vol sense capacitat de control
La comunicació amb el dron es fa a través de MQTT (ordres i telemetria) i WebRTC (vídeo en directe).
---
Requisits previs
Maquinari
Dron compatible amb MAVLink (ex. Ardupilot) o accés al simulador SITL (Mission Planer)
Portàtil connectat a la xarxa del DroneLab o Internet (per al broker extern)
Programari
Python 3.9 o superior
Accés al broker MQTT: `dronseetac.upc.edu:8000` o un similar
---
Instal·lació
1. Clonar el repositori
```bash
git clone https://github.com/NoaOP/PD_V1.git
cd PD_V1/V3/ProyectoDeDrones
```
2. Instal·lar les dependències
```bash
pip install flask
pip install paho-mqtt==1.6.1
pip install opencv-python
pip install aiortc
pip install av
```
4. Llibreria del dron (DronLink)
Assegura't que la carpeta `dronLink` amb la classe `Dron` és accessible des del directori del projecte. Aquesta llibreria forma part del material del curs de l'EETAC.
---
Configuració
Els paràmetres de connexió es poden sobreescriure amb variables d'entorn:
Variable	Valor per defecte	Descripció
`MQTT_BROKER_HOST`	`dronseetac.upc.edu`	Adreça del broker MQTT
`MQTT_BROKER_PORT`	`8000`	Port del broker
`MQTT_USERNAME`	`dronsEETAC`	Usuari del broker
`MQTT_PASSWORD`	`mimara1456.`	Contrasenya del broker
`MAVPROXY_AUTOPILOT_ENDPOINT`	`udp:127.0.0.1:14552`	Endpoint MAVProxy
`MAVPROXY_AUTOPILOT_BAUD`	`115200`	Velocitat de connexió
---
Execució
Cal llançar els serveis en terminals separades:
Terminal 1 — Servidor web
```bash
python serverMQTT.py
```
La WebApp estarà disponible a `http://localhost:5002`
Terminal 2 — Servei del pilot automàtic
```bash
python AutopilotService.py
```
Terminal 3 — Servei de càmera (opcional, per al vídeo en directe)
```bash
python CameraService.py
```
> Per usar el **simulador** en lloc del dron real, selecciona "Connectar (Simulador)" des de la pestanya Control. Cal tenir SITL en execució a `tcp:127.0.0.1:5763`.
Mode espectador — des de qualsevol dispositiu a la mateixa xarxa:
```
http://<IP-del-portàtil>:5002/spectator
```

---
Llicència
Projecte acadèmic de l'EETAC (UPC). 
