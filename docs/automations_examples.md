# Automazioni di Esempio

Collezione di template di automazione pronti da usare con Claude.

## 1. Controllo Vacanza Intelligente

Attiva modalità vacanza con Claude.

```yaml
automation:
  - id: "claude_vacation_mode"
    alias: "Claude - Modalità Vacanza"
    description: "Attiva modalità vacanza con Claude"
    trigger:
      platform: state
      entity_id: input_boolean.vacation_mode
      to: "on"
    action:
      - service: claude.execute_automation
        data:
          automation_id: "automation.vacation_lights"
      
      - service: claude.call_service
        data:
          service: "climate.set_temperature"
          data: '{"entity_id": "climate.home", "temperature": 18}'
      
      - service: homeassistant.turn_off
        data:
          entity_id: "group.all_lights"
```

## 2. Rientro da Lavoro Automatico

Claude accoglie il ritorno da lavoro.

```yaml
automation:
  - id: "claude_welcome_home"
    alias: "Claude - Benvenuto a Casa"
    trigger:
      platform: state
      entity_id: person.user
      from: "not_home"
      to: "home"
    action:
      - service: claude.send_message
        data:
          message: "L'utente è tornato a casa, attiva modalità accoglienza"
          context: "Ora esatta, temperatura esterna, meteo"
      
      - service: light.turn_on
        data:
          entity_id: light.hallway
          brightness: 255
      
      - service: climate.set_temperature
        data:
          entity_id: climate.home
          temperature: 21
      
      - service: media_player.play_media
        data:
          entity_id: media_player.speakers
          media_content_type: music
          media_content_id: "playlist:welcome_home"
```

## 3. Automazione Vocale

Controlla Casa tramite comandi vocali con Claude.

```yaml
automation:
  - id: "claude_voice_command"
    alias: "Claude - Comando Vocale"
    trigger:
      platform: conversation
      command: "claude"
    action:
      - service: claude.send_message
        data:
          message: "{{ trigger.sentence }}"
          context: "Casa, ora: {{ now() }}, meteo: sunny"
      
      - service: tts.google_translate_say
        data:
          entity_id: media_player.speakers
          message: "Ho capito il comando"
```

## 4. Scena Automatica Serale

Claude gestisce la transizione serale automaticamente.

```yaml
automation:
  - id: "claude_evening_scene"
    alias: "Claude - Scena Serale"
    trigger:
      - platform: sun
        event: sunset
        offset: "-00:30:00"
      - platform: time
        at: "18:00:00"
    action:
      - service: claude.call_service
        data:
          service: "light.turn_on"
          data: '{
            "entity_id": "light.living_room",
            "brightness": 150,
            "color_temp": 454
          }'
      
      - service: climate.set_temperature
        data:
          entity_id: climate.home
          temperature: 20
      
      - service: script.turn_on
        target:
          entity_id: script.evening_routine
```

## 5. Controllo Consumo Energetico

Claude monitora e ottimizza i consumi.

```yaml
automation:
  - id: "claude_energy_optimization"
    alias: "Claude - Ottimizzazione Energia"
    trigger:
      platform: numeric_state
      entity_id: sensor.power_consumption
      above: 3000
    action:
      - service: claude.send_message
        data:
          message: "Consumo energetico alto, ottimizza dispositivi"
          context: "Consumo attuale: {{ states('sensor.power_consumption') }} W"
      
      - service: homeassistant.turn_off
        data:
          entity_id:
            - light.outdoor
            - switch.water_heater
      
      - service: climate.set_temperature
        data:
          entity_id: climate.home
          temperature: 19
```

## 6. Manutenzione Intelligente

Claude ricorda scadenze e manutenzione.

```yaml
automation:
  - id: "claude_maintenance_check"
    alias: "Claude - Controllo Manutenzione"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      - service: claude.send_message
        data:
          message: "Controlla lo stato dei filtri e della manutenzione"
          context: "Ultima manutenzione: {{ state_attr('automation.maintenance', 'last_triggered') }}"
      
      - service: notify.mobile_app
        data:
          title: "Claude - Richiesta Manutenzione"
          message: "È ora di controllare i filtri"
```

## 7. Monitoraggio Sicurezza

Claude monitora sensori di sicurezza.

```yaml
automation:
  - id: "claude_security_check"
    alias: "Claude - Monitoraggio Sicurezza"
    trigger:
      - platform: state
        entity_id: binary_sensor.door_front
        to: "on"
      - platform: state
        entity_id: binary_sensor.window_living_room
        to: "on"
    action:
      - service: claude.send_message
        data:
          message: "Rilevi apertura porta/finestra"
          context: "Dispositivo: {{ trigger.entity_id }}, Ora: {{ now() }}"
      
      - service: camera.snapshot
        target:
          entity_id: camera.front_door
        data:
          filename: "/tmp/snapshot_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
      
      - service: notify.mobile_app
        data:
          title: "Allarme Sicurezza"
          message: "{{ trigger.entity_id }} aperta"
```

## 8. Controllo Piante Intelligente

Claude si ricorda di innaffiare le piante.

```yaml
automation:
  - id: "claude_plant_care"
    alias: "Claude - Cura Piante"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      - service: claude.send_message
        data:
          message: "Controlla sensori umidità piante"
          context: "Umidità soggiorno: {{ states('sensor.plant_humidity_living_room') }}%"
      
      - condition: numeric_state
        entity_id: sensor.plant_humidity_living_room
        below: 30
      
      - service: switch.turn_on
        target:
          entity_id: switch.plant_watering
      
      - service: notify.mobile_app
        data:
          title: "Piante"
          message: "È ora di innaffiare"
```

## 9. Ottimizzazione Comfort

Claude regola automaticamente comfort e benessere.

```yaml
automation:
  - id: "claude_comfort_optimization"
    alias: "Claude - Ottimizzazione Comfort"
    trigger:
      platform: numeric_state
      entity_id: sensor.living_room_temperature
      above: 24
    action:
      - service: claude.send_message
        data:
          message: "Temperatura troppo alta, raffredda"
          context: "Temp: {{ states('sensor.living_room_temperature') }}°C"
      
      - service: climate.set_temperature
        data:
          entity_id: climate.living_room
          temperature: 22
      
      - service: switch.turn_on
        target:
          entity_id: switch.fan_living_room
```

## 10. Automazione Notturna Intelligente

Claude gestisce la giornata verso la sera.

```yaml
automation:
  - id: "claude_night_mode"
    alias: "Claude - Modalità Notte"
    trigger:
      platform: time
      at: "23:00:00"
    action:
      - service: claude.send_message
        data:
          message: "Prepara la casa per la notte"
          context: "Tutti a letto? Controlla sensori movimento"
      
      - service: homeassistant.turn_off
        data:
          entity_id: group.all_lights
      
      - service: lock.lock
        target:
          entity_id: lock.front_door
      
      - service: climate.set_temperature
        data:
          entity_id: climate.home
          temperature: 18
      
      - service: script.turn_on
        target:
          entity_id: script.night_security_check
```

## Tips per Automazioni Efficaci

1. **Usa contesti chiari**: Fornisci a Claude informazioni rilevanti
2. **Testa incrementalmente**: Inizia con automazioni semplici
3. **Aggiungi logging**: Monitora execuzione e errori
4. **Combo di sensori**: Usa più trigger per logica complessa
5. **Fallback**: Prepara azioni alternative se Claude non risponde
6. **Timeout**: Imposta timeout ragionevoli sulle automazioni
7. **Notifiche**: Comunica agli utenti cosa sta succedendo

## Variabili Utili

```yaml
# Data e ora
now() - ora corrente
trigger.entity_id - entità che ha attivato il trigger
states('entity_id') - stato di un'entità
state_attr('entity_id', 'attribute') - attributo di un'entità

# Context per Claude
"Ora: {{ now().strftime('%H:%M') }}"
"Temperatura: {{ states('sensor.temperature') }}°C"
"Meteo: sunny/cloudy/rainy"
```
