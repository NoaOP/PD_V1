
## Drone Paint WebApp ✈️ 🖌️

## Introducció
Aquest projecte té com a objectiu utilitzar el dron com si fos una eina de dibuix, semblant a una eina de Paint, permetent crear trajectòries, figures i formes directament des d’una WebApp. A través de la web, l’usuari pot controlar el moviment del dron, configurar l’estil del traç i visualitzar en temps real el recorregut que s’està generant.

La WebApp està dividida en dos modes principals: el mode pilot i el mode espectador. El mode pilot està pensat per a la persona encarregada de controlar el dron i realitzar els dibuixos. Des d’aquest mode es poden executar les accions principals, com connectar el dron, enlairar-lo, moure’l, modificar la trajectòria, canviar els paràmetres del dibuix i utilitzar les diferents eines disponibles.

D’altra banda, el mode espectador està destinat a aquells usuaris que només volen observar el que s’està dibuixant, sense intervenir en el control del dron. Aquest mode mostra informació bàsica del vol, com l’altitud i el heading, així com la posició del dron en temps real sobre el mapa. D’aquesta manera, qualsevol espectador pot seguir l’evolució del dibuix mentre el pilot executa els moviments.

<p align="center">
<img style="width:auto; height:250px" alt="image" src="https://github.com/user-attachments/assets/cf1fada8-595a-4dd9-b3ab-d95e9df37d2a" />
</p>




## Pestanya de control 🛫 🛬 🏠
La pestanya de control és l’apartat principal des d’on l’usuari pot manejar el dron de manera manual. Aquesta secció permet establir la connexió amb el dron, ja sigui mitjançant MAVProxy o a través del simulador, i executar les accions bàsiques necessàries abans d’iniciar qualsevol operació de dibuix.

Des d’aquesta pestanya es poden realitzar les funcions següents:

· Connectar el dron mitjançant MAVProxy

· Connectar el dron en mode simulador

· Enlairar el dron introduint l’altura desitjada en metres

· Aterrar el dron de manera segura

· Activar el mode RTL perquè el dron torni al punt d’origen

· Utilitzar el control per veu per executar ordres bàsiques

· Modificar el heading del dron mitjançant un control lliscant

· Ajustar la velocitat de navegació del dron

· Desplaçar el dron manualment en diferents direccions

· Moure el dron respecte al seu propi sistema de referència

· Controlar el moviment vertical del dron, tant cap amunt com cap avall

· Aturar el moviment del dron en qualsevol moment

· Visualitzar l’altitud actual del dron

Els controls de moviment estan organitzats en diferents blocs. El primer bloc permet moure el dron segons les direccions cardinals, com nord, sud, est i oest. El segon bloc permet controlar el moviment respecte a l’orientació pròpia del dron, amb ordres com endavant, enrere, esquerra i dreta. Finalment, el tercer bloc permet modificar l’altitud mitjançant els comandaments d’amunt i avall. També proporciona funcions de seguretat importants, com aturar el moviment, aterrar el dron o fer-lo tornar automàticament al punt inicial mitjançant el mode RTL.

<p align="center">
<img style="width:auto; height:250px" alt="WhatsApp Image 2026-05-20 at 12 31 44" src="https://github.com/user-attachments/assets/17b23ee7-a257-4973-99fc-2bad805e947f" />
</p>

El funcionament de tots els botons d’aquesta pestanya es mostra en el següent vídeo: https://drive.google.com/file/d/1jQzbDifgyQAil2ZV8xtg16v4lMq-rJpo/view?usp=sharing


## PESTANYA DE VISUALITZACIÓ DEL MAPA 🗺️
La pestanya de mapa és l’apartat principal des d’on l’usuari pot visualitzar la posició del dron i utilitzar-lo com a eina de dibuix sobre una zona geogràfica. Aquesta secció mostra un mapa interactiu amb la ubicació del dron.
A la part superior de la pestanya es troben les eines principals de dibuix:

🎨 **· Pintar:** Activa el mode de dibuix perquè el moviment del dron quedi representat sobre el mapa.

🧽 **· Netejar:** Elimina el dibuix o la trajectòria mostrada, permetent començar de nou.

🖼️ **· Imatge:** Es realitza una captura de pantalla del mapa que es descarrega al dispositiu directament amb el nom "DronLab Paint EETAC", la data i l'hora.

El mapa permet veure la posició GPS del dron en temps real i seguir el seu desplaçament mentre es mou. D’aquesta manera, l’usuari pot comprovar visualment si el dron està seguint correctament la trajectòria desitjada i si el dibuix generat coincideix amb el resultat esperat.
A més, aquesta pestanya incorpora controls manuals addicionals, com un joystick de moviment i botons per modificar l’altitud del dron. Això permet fer petits ajustos directament des del mapa sense haver de tornar a la pestanya de control. També es mostra un missatge d’estat que indica si el dron està preparat per volar o si encara s’ha d’iniciar el vol.

<p align="center">
<img style="width:auto; height:250px" alt="WhatsApp Image 2026-05-20 at 12 47 03" src="https://github.com/user-attachments/assets/19f32c19-d8b7-4c2e-8865-514875708120" />
</p>

Al vídeo es mostra el funcionament de la pestanya del mapa: https://drive.google.com/file/d/1dLVnobGKilXHOhRfDpDGO3DoDueqvain/view?usp=drive_link


## PESTANYA DE LA ZONA DE JOCS 🎮
La pestanya de jocs permet a l’usuari iniciar un repte interactiu. L’objectiu principal del joc és controlar el dron manualment i aconseguir passar per sobre de tots els punts que formen la figura seleccionada abans que s’acabi el temps del cronòmetre.

<p align="center">
<img style="width:auto; height:200px" alt="Captura de pantalla 2026-05-22 202222" src="https://github.com/user-attachments/assets/04b21590-fb43-40f7-b673-d714ef37fe1c" />
</p>

Abans d’iniciar el repte, l’usuari pot seleccionar una de les figures disponibles. Aquestes figures estan organitzades segons el nivell de dificultat:

⬛ **· Quadrat:** Figura més senzilla.

⭕ **· Cercle:** Figura de dificultat intermèdia.

⭐ **· Estrella:** Figura més complexa.

Un cop seleccionada la figura, l’usuari pot prémer el botó Iniciar Repte. A partir d’aquest moment, comença el compte enrere i apareixen els punts que formen la figura. 
Si s'acaba el temps i no s'ha pogut completar el repte apareix a la pantalla el següent missatge:


<p align="center">
<img style="width:auto; height:200px" alt="Captura de pantalla 2026-05-22 200200" src="https://github.com/user-attachments/assets/05bbf568-8f97-4a3c-a6d2-3b514d65b397" />
</p>

Al vídeo es mostra el funcionament de la pestanya del joc: https://drive.google.com/file/d/13PNzchkuPIf_yUq4CWBE7A46mC6Pyrc3/view?usp=drive_link

## PESTANYA CONFIGURACIÓ ⚙️

La pestanya de configuració permet personalitzar l’aspecte del dibuix que es genera sobre el mapa. Aquesta secció està pensada perquè l’usuari pugui modificar diferents paràmetres visuals de la trajectòria abans o durant l’ús del dron com a eina de dibuix.

En primer lloc, l’usuari pot seleccionar el color de la trajectòria. Aquest color serà el que s’utilitzarà per representar el recorregut del dron sobre el mapa, de manera que el moviment del dron quedarà dibuixat amb l’estil escollit. També es pot modificar el gruix del traç mitjançant un control lliscant, permetent obtenir línies més fines o més gruixudes.


<p align="center">
<img style="width:auto; height:200px" alt="Captura de pantalla 2026-05-23 200901" src="https://github.com/user-attachments/assets/14c8af3c-6199-4e64-b906-a5e5a13b54d2" />
</p>


A més, aquesta pestanya permet canviar el format de la línia. D’aquesta manera, el dibuix no només es limita a una línia contínua, sinó que també es poden aplicar diferents estils visuals a la trajectòria. Entre les opcions disponibles hi ha funcions com esborrar el dibuix, activar una línia temporal de 10 segons, aplicar un efecte d’arc de Sant Martí o utilitzar un efecte de purpurina. A la següent imatge es veu com alguns dels estils de línia es mostren més curts al desplegable. Això és degut a que el format de la WebApp està especialment dissenyat per utilitzar-se mitjançant un dispositiu mòbil. 

<p align="center">
<img style="width:auto; height:200px" alt="Captura de pantalla 2026-05-23 201004" src="https://github.com/user-attachments/assets/a93befd9-bc4f-4d68-9293-f06485cc90a3" />
</p>



<p align="center">
<img style="width:auto; height:100px" alt="Captura de pantalla 2026-05-23 201717" src="https://github.com/user-attachments/assets/b5af75be-dfc9-4450-bee4-3e9d9295813e" />
</p>

Finalment, la pestanya també incorpora un apartat de geometria, des d’on l’usuari pot seleccionar figures predefinides com un triangle, un quadrat, una rodona o un cor. Aquestes opcions permeten generar formes de manera més directa, sense haver de dibuixar tota la trajectòria manualment.

<p align="center">
<img style="width:auto; height:150px" alt="Captura de pantalla 2026-05-23 201704" src="https://github.com/user-attachments/assets/c91f88d1-cf0c-41d0-aa7d-744673d903ec" />
</p>

S’inclouen diverses eines avançades de dibuix amb el dron. Una d’aquestes funcions és l’opció d’emplenar una zona. Aquesta eina permet definir una plantilla sobre el mapa i, posteriorment, fer que el dron generi una trajectòria interna per cobrir l’àrea seleccionada.

Per utilitzar aquesta funcionalitat, l’usuari pot dibuixar una plantilla, eliminar-la si vol tornar a començar, o executar l’opció d’emplenar. A més, es poden ajustar alguns paràmetres de la plantilla, com l’altitud de vol i la separació entre passades. L’altitud determina a quina altura es realitzarà el recorregut, mentre que la separació entre passades defineix la distància entre les línies internes que el dron seguirà per cobrir la zona.

Aquesta pestanya també incorpora una eina per escriure text amb el dron. L’usuari pot introduir una paraula al camp de text i el sistema genera la trajectòria necessària perquè el dron pugui representar aquest text mitjançant el seu moviment.


<p align="center">
<img style="width:auto; height:250px" alt="image" src="https://github.com/user-attachments/assets/6f23e6c1-aa9d-4ef9-b30a-759ec0a170b2" />
</p>

Als vídeos es poden veure les diferents eines disponibles a l'apartat de la configuració:

Vídeo de colors i gruix de línia: https://drive.google.com/file/d/1OzQmmWnxNWDJlxVlszBcS8xodk6dLjkw/view?usp=drive_link

Vídeo dels diferents tipus de línia: https://drive.google.com/file/d/1uBbtL5OwYlqatU9EomBpfwJXjgGXycPP/view?usp=drive_link

Vídeo del botó arcoiris, purpurina, línia temporal i esborrar: https://drive.google.com/file/d/1u2n-m7qtvx1kvoVbk1jLdP4nZwr9yF6t/view?usp=drive_link

Vídeo de la geometria: https://drive.google.com/file/d/1zM0WzfDYu4xbzFK7c07Xn1_GtyXHTjl_/view?usp=drive_link

Vídeo del botó d’emplenar zona: https://drive.google.com/file/d/1CcGdElXrPAkbjJyaM6wHj_Jh67IWrBc_/view?usp=drive_link

Vídeo del teclat: https://drive.google.com/file/d/1GgdGvlbP6SfUhsEflIQF9nQhHvlRvofl/view?usp=drive_link



## PESTANYA DE VÍDEO 📹

La pestanya de vídeo està preparada per permetre la transmissió d’imatge en temps real des del dron. Aquesta secció inclou els botons per iniciar i detenir el vídeo, així com una zona central on es mostraria la imatge capturada per la càmera. La seva finalitat és que, si en un futur s’instal·la una càmera al dron, l’usuari pugui visualitzar directament des de la WebApp el que el dron està captant durant el vol.
Aquesta pestanya podria ser especialment útil durant les operacions de dibuix, ja que permetria supervisar l’entorn del dron en temps real i comprovar visualment que el moviment s’està executant correctament.


<p align="center">
<img style="width:auto; height:250px" alt="image" src="https://github.com/user-attachments/assets/7b933dfa-6e22-4635-bbe0-cb901de95435" />
</p>


## DEMOSTRACIÓ DE LA WEBAPP 🎬


<p align="center">
  <a href="https://drive.google.com/file/d/1Wr10YXfl4sSoYk8w0_654i7Tzaq7Ito0/view?usp=drive_link" target="_blank">
    <img src="https://github.com/user-attachments/assets/fb97b1d6-3cc1-46e3-9f06-914acfb265c1"
         alt="Vídeo de demostració"
         height="250">
  </a>
</p>

<p align="center">
  <em>Fes clic a la imatge per veure la demostració final de la WebApp.</em>
</p>



