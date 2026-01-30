# Module Afficheur LED – Smart Parking (P4)

## Description
Ce module représente l’afficheur LED du système de gestion de parking intelligent.
Il affiche en temps réel le nombre de places disponibles à l’entrée du parking,
à partir des informations reçues des capteurs simulés via le protocole MQTT.

## Rôle du module
- Écoute les états des places de parking publiés par les capteurs (P1).
- Calcule le nombre de places libres.
- Publie un résumé simple destiné aux autres modules.

> Le module est passif (read-only) et ne modifie jamais l’état des places.

## Communication MQTT
- **Broker** : `broker.emqx.io`
- **Abonnement** : `smart_parking_2026/parking/spots/+/status`
- **Publication** : `smart_parking_2026/parking/display/available`
  - Format : `{ "count": <nombre_de_places_libres> }`
