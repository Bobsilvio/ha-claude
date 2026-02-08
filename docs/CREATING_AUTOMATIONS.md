# Creating Automations with Claude

**NEW FEATURE!** You can now have Claude create automations automatically.

## Overview

Instead of manually creating automations, you can use Claude to:
- **Tell Claude what you want** (e.g., "Turn on lights at sunset")
- **Claude creates the automation** dynamically
- **Automation is saved** to `automations.yaml`
- **No manual YAML editing needed**

## Syntax

### Claude Service: `claude.create_automation`

```yaml
service: claude.create_automation
data:
  automation_name: "Turn on lights at sunset"
  description: "Automatically turn on living room lights when sun sets"
  trigger: '{"platform": "sun", "event": "sunset"}'
  condition: '{"condition": "state", "entity_id": "binary_sensor.people_home", "state": "on"}'
  action: '{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 200}}'
```

## Example 1: Simple - Lights at Sunset

```yaml
automation:
  - id: "claude_create_lights_sunset"
    alias: "Claude - Create Lights Sunset"
    trigger:
      platform: numeric_state
      entity_id: sensor.time
      above: 10
    action:
      - service: claude.create_automation
        data:
          automation_name: "Sunset lights"
          description: "Turn on lights when sun sets"
          trigger: '{"platform": "sun", "event": "sunset"}'
          action: '[{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 200, "color_temp": 454}}]'
```

## Example 2: Advanced - Motion Sensor

```yaml
service: claude.create_automation
data:
  automation_name: "Motion detection lights"
  description: "Turn on lights when motion detected in hallway"
  trigger: '{"platform": "state", "entity_id": "binary_sensor.hallway_motion", "to": "on"}'
  condition: '{"condition": "time", "after": "21:00:00", "before": "06:00:00"}'
  action: |
    [
      {"service": "light.turn_on", "target": {"entity_id": "light.hallway"}, "data": {"brightness": 100}},
      {"delay": "00:02:00"},
      {"service": "light.turn_off", "target": {"entity_id": "light.hallway"}}
    ]
```

## Example 3: Complex - Temperature Control

```yaml
service: claude.create_automation
data:
  automation_name: "Auto temperature control"
  description: "Adjust temperature based on time of day"
  trigger: '{"platform": "time", "at": "07:00:00"}'
  action: |
    [
      {"service": "climate.set_temperature", "target": {"entity_id": "climate.living_room"}, "data": {"temperature": 21}},
      {"service": "notify.mobile_app", "data": {"title": "Temperature", "message": "Morning temperature set to 21°C"}}
    ]
```

## Parameter Details

| Parameter | Required | Format | Example |
|-----------|----------|--------|---------|
| automation_name | ✅ Yes | String | "Turn on lights at sunset" |
| description | ⚠️ Optional | String | "Lights turn on automatically" |
| trigger | ✅ Yes | JSON | `{"platform": "sun", "event": "sunset"}` |
| condition | ⚠️ Optional | JSON | `{"condition": "state", "entity_id": "..."}` |
| action | ✅ Yes | JSON Array | `[{service: ...}, {service: ...}]` |

## Trigger Examples

### Time-based
```json
{"platform": "time", "at": "10:30:00"}
```

### Sun
```json
{"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
```

### State
```json
{"platform": "state", "entity_id": "light.living_room", "to": "on"}
```

### Numeric State
```json
{"platform": "numeric_state", "entity_id": "sensor.temperature", "above": 25}
```

### Webhook
```json
{"platform": "webhook", "webhook_id": "my_webhook"}
```

## Condition Examples

### State Condition
```json
{"condition": "state", "entity_id": "binary_sensor.people_home", "state": "on"}
```

### Time Range
```json
{"condition": "time", "after": "22:00:00", "before": "06:00:00"}
```

### Numeric Range
```json
{"condition": "numeric_state", "entity_id": "sensor.humidity", "below": 30}
```

## Action Examples

### Turn on lights
```json
[{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}]
```

### Call multiple services
```json
[
  {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}},
  {"service": "media_player.play_media", "target": {"entity_id": "media_player.speakers"}, "data": {"media_content_id": "playlist:welcome"}},
  {"service": "climate.set_temperature", "target": {"entity_id": "climate.home"}, "data": {"temperature": 21}}
]
```

### Delay
```json
[
  {"service": "light.turn_on", "target": {"entity_id": "light.bedroom"}},
  {"delay": "00:05:00"},
  {"service": "light.turn_off", "target": {"entity_id": "light.bedroom"}}
]
```

## Use Cases

### 1. Create Scheduled Scene
```yaml
automation:
  - id: "create_morning_routine"
    trigger:
      platform: time
      at: "06:00:00"
    action:
      - service: claude.create_automation
        data:
          automation_name: "Morning routine"
          trigger: '{"platform": "time", "at": "06:30:00"}'
          action: '[{"service": "light.turn_on", "target": {"entity_id": "group.bedroom"}}, {"service": "media_player.play_media", "target": {"entity_id": "media_player.speakers"}, "data": {"media_content_id": "playlist:morning"}}]'
```

### 2. Create Energy Saving
```yaml
- service: claude.create_automation
  data:
    automation_name: "Night energy saving"
    trigger: '{"platform": "sun", "event": "sunset"}'
    action: '[{"service": "switch.turn_off", "target": {"entity_id": "group.all_lights"}}, {"service": "climate.set_temperature", "target": {"entity_id": "climate.home"}, "data": {"temperature": 18}}]'
```

### 3. Create Alert on Condition
```yaml
- service: claude.create_automation
  data:
    automation_name: "High humidity alert"
    trigger: '{"platform": "numeric_state", "entity_id": "sensor.bathroom_humidity", "above": 75}'
    action: '[{"service": "notify.mobile_app", "data": {"title": "Humidity Alert", "message": "Bathroom humidity is high"}}, {"service": "switch.turn_on", "target": {"entity_id": "switch.bathroom_fan"}}]'
```

## Tips & Tricks

### 1. Use Quotes Correctly
```yaml
# ❌ Wrong - JSON not escaped
trigger: {"platform": "time"}

# ✅ Correct - JSON as string
trigger: '{"platform": "time"}'
```

### 2. Multi-line Actions
```yaml
action: |
  [
    {"service": "light.turn_on", "target": {"entity_id": "light.a"}},
    {"service": "light.turn_on", "target": {"entity_id": "light.b"}},
    {"service": "light.turn_on", "target": {"entity_id": "light.c"}}
  ]
```

### 3. Variable Interpolation
```yaml
- service: claude.create_automation
  data:
    automation_name: "Auto-created at {{ now() }}"
    trigger: '{"platform": "time", "at": "{{ states(''input_text.automation_time'') }}"}'
    action: '...'
```

## Troubleshooting

### Automation not created?
1. Check Home Assistant logs: `Settings → System → Logs`
2. Verify JSON syntax is valid
3. Ensure `automations.yaml` is writable

### Automation created but doesn't work?
1. Check trigger/condition/action configuration
2. Use Developer Tools → Services to test manually
3. Enable debug logging for Claude integration

### JSON Parse Error?
Ensure you're escaping quotes:
```yaml
# ✅ Correct
action: '{"service": "light.turn_on"}'

# ❌ Wrong
action: {"service": "light.turn_on"}
```

## Advanced

### Create from Template
```yaml
template:
  - service: claude.create_automation
    data:
      automation_name: "{{ trigger.entity_id }} alarm"
      trigger: '{"platform": "numeric_state", "entity_id": "{{ trigger.entity_id }}", "above": 30}'
      action: '[{"service": "notify.mobile_app", "data": {"title": "Alert", "message": "{{ trigger.entity_id }} exceeded threshold"}}]'
```

### Create from Claude AI
You can tell Claude to create automations dynamically:

```
User: "Claude, create an automation that turns on lights when I arrive home"

Claude creates:
  automation_name: "Welcome home lights"
  trigger: binary_sensor.front_door motion
  action: light.turn_on (living_room)
```

---

**New possibilities with dynamic automation creation! 🚀**
