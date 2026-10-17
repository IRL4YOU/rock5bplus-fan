#!/bin/bash
# ROCK 5B Plus: gleichmaessige Luefterkurve. Temperatur wird geglaettet (ca. 20 s), die Drehzahl folgt
# stufenlos (50 bis 255 von 45 bis 70 Grad, leise Auslegung) und aendert sich nur langsam. Unter 42 Grad aus, ab 45 Grad an.
# Notfall: ab 68 Grad (ungeglaettet) oder bei Fehlern volle Leistung.
set -euo pipefail
shopt -s nullglob
fan_paths=()
for device in /sys/class/hwmon/hwmon*; do
  [[ $(cat "$device/name") == pwmfan ]] || continue
  [[ $(readlink -f "$device/device") == /sys/devices/platform/pwm-fan ]] || continue
  [[ -w $device/pwm1 ]] && fan_paths+=("$device/pwm1")
done
[[ ${#fan_paths[@]} == 1 ]] || { echo 'Luefter nicht eindeutig gefunden' >&2; exit 1; }
pwm=${fan_paths[0]}
failsafe() { printf '255\n' > "$pwm" || true; }
trap failsafe EXIT
trap 'exit 0' TERM INT
sensor_paths=()
for device in /sys/class/thermal/thermal_zone*; do
  [[ $(cat "$device/type") == soc-thermal ]] && sensor_paths+=("$device/temp")
done
[[ ${#sensor_paths[@]} == 1 ]] || { echo 'SoC-Sensor nicht eindeutig gefunden' >&2; exit 1; }
sensor=${sensor_paths[0]}
echo "Luefterregelung (stufenlos) gestartet: $pwm; Sensor $sensor"
# Die Kuehlsteuerung des Kernels wuerde denselben Luefter sonst stufenweise zurueckstellen und erzeugt dabei dauernd Systemmeldungen.
# Darum ist die Waermezone im Betrieb ausgeschaltet. Ab 80 Grad schaltet sie sich als Sicherung (Drosselung) wieder ein, unter 76 Grad wieder aus.
ZONE=/sys/class/thermal/thermal_zone0
echo 84000 > $ZONE/trip_point_0_temp 2>/dev/null || true
echo step_wise > $ZONE/policy 2>/dev/null || true
zmode=disabled; echo disabled > $ZONE/mode 2>/dev/null || true
trap 'echo enabled > $ZONE/mode 2>/dev/null; failsafe' EXIT
printf '255\n' > "$pwm"; sleep 1
avg=-1; cur=255
while true; do
  t=$(cat "$sensor")
  [[ $t =~ ^[0-9]+$ ]] && ((t > 0 && t < 150000)) || { echo 'Ungueltiger Temperaturwert: volle Luefterleistung' >&2; exit 1; }
  if ((avg < 0)); then avg=$t; else avg=$(( (avg * 9 + t) / 10 )); fi
  if ((t >= 80000)); then want_mode=enabled; elif ((t < 76000)); then want_mode=disabled; else want_mode=$zmode; fi
  if [[ $want_mode != "$zmode" ]]; then zmode=$want_mode; echo "$zmode" > $ZONE/mode 2>/dev/null || true; fi
  if ((t >= 68000)); then
    nxt=255
  else
    if ((avg >= 45000 || (cur > 0 && avg >= 42000))); then
      x=$avg; ((x < 45000)) && x=45000; ((x > 70000)) && x=70000
      want=$(( 50 + (x - 45000) * 205 / 25000 ))
    else
      want=0
    fi
    if ((want == 0)); then
      if ((cur > 50)); then nxt=$((cur - 3)); ((nxt < 50)) && nxt=50; else nxt=0; fi
    elif ((cur == 0)); then
      printf '255\n' > "$pwm"; sleep 1; nxt=$want       # kurzer Anlaufstoss nur nach Stillstand
    elif ((want > cur)); then
      nxt=$((cur + 10)); ((nxt > want)) && nxt=$want
    elif ((want < cur)); then
      nxt=$((cur - 2)); ((nxt < want)) && nxt=$want
    else
      nxt=$cur
    fi
  fi
  cur=$nxt
  # Der Kernel hat eine eigene Kuehlsteuerung fuer denselben Luefter und stellt die Stufe zwischendurch zurueck
  # (daher frueher das An/Aus). Deshalb den Sollwert mehrmals pro Sekunde neu setzen: Rueckstellungen dauern so nur Bruchteile.
  for _ in 1 2 3 4 5 6 7 8; do
    printf '%s\n' "$cur" > "$pwm"
    sleep 0.25
  done
done
