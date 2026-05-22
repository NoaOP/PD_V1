# VERSIÓ FINAL

## Introducció
comentar que hi ha modo pilot y modo espectador

## Pestanya de control
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

## PESTANYA DE VISUALITZACIÓ DEL MAPA
La pestanya de mapa és l’apartat principal des d’on l’usuari pot visualitzar la posició del dron i utilitzar-lo com a eina de dibuix sobre una zona geogràfica. Aquesta secció mostra un mapa interactiu amb la ubicació del dron.
A la part superior de la pestanya es troben les eines principals de dibuix:

**· Pintar:** activa el mode de dibuix perquè el moviment del dron quedi representat sobre el mapa.

**· Netejar:** elimina el dibuix o la trajectòria mostrada, permetent començar de nou.

**· Imatge:** es realitza una captura de pantalla del mapa que es descarrega al dispositiu directament amb el nom "DronLab Paint EETAC", la data i l'hora.

El mapa permet veure la posició GPS del dron en temps real i seguir el seu desplaçament mentre es mou. D’aquesta manera, l’usuari pot comprovar visualment si el dron està seguint correctament la trajectòria desitjada i si el dibuix generat coincideix amb el resultat esperat.
A més, aquesta pestanya incorpora controls manuals addicionals, com un joystick de moviment i botons per modificar l’altitud del dron. Això permet fer petits ajustos directament des del mapa sense haver de tornar a la pestanya de control. També es mostra un missatge d’estat que indica si el dron està preparat per volar o si encara s’ha d’iniciar el vol.


## PESTANYA DE LA ZONA DE JOCS
La pestanya de jocs permet a l’usuari iniciar un repte interactiu. L’objectiu principal del joc és controlar el dron manualment i aconseguir passar per sobre de tots els punts que formen la figura seleccionada abans que s’acabi el temps del cronòmetre.

Abans d’iniciar el repte, l’usuari pot seleccionar una de les figures disponibles. Aquestes figures estan organitzades segons el nivell de dificultat:

**· Quadrat:** figura més senzilla.

**· Cercle:** figura de dificultat intermèdia.

**· Estrella:** figura més complexa.

Un cop seleccionada la figura, l’usuari pot prémer el botó Iniciar Repte. A partir d’aquest moment, comença el compte enrere i apareixen els punts que formen la figura. 
Si s'acaba el temps i no s'ha pogut completar el repte apareix a la pantalla el següent missatge:


