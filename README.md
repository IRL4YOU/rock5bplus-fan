# ROCK 5B+ Lüftersteuerung

Temperaturabhängige Lüftersteuerung von IRL4YOU für den **Radxa ROCK 5B Plus** mit Linux und systemd. Eigenständiges Shell-Skript mit Autostart, stufenloser geglätteter Kurve, Anlaufimpuls und Fehlerbehandlung. Unabhängiges Projekt, kein offizielles Radxa- oder BELABOX-Produkt.

Die Version 1.1.0 ersetzt die Stufenkurve durch eine stufenlose, geglättete Kurve und setzt den Wert mehrmals pro Sekunde neu, weil die Kernel-Kühlsteuerung sonst dazwischenfunkt (Lüfter ging dauernd an und aus). [Prüfstand und Grenzen](TESTSTAND.md).

Version 1.2.0: Die Wärmezone des Kernels ist im Betrieb ausgeschaltet (ab 80 °C schaltet sie sich als Sicherung wieder ein), weil sie sonst dauernd Systemmeldungen erzeugt und gegen die Regelung arbeitet.

**Sprache / Language:** [Deutsch](#rock-5b-lüftersteuerung) · [English below](#english--rock-5b-fan-controller)

## Regelung

| SoC-Temperatur (geglättet) | PWM (0–255) |
|---|---:|
| unter 42 °C | 0 (aus) |
| 42 bis unter 45 °C | ein laufender Lüfter läuft mit PWM 50 weiter, ein stehender bleibt aus |
| 45 °C | 50 |
| 57,5 °C | 152 |
| 70 °C und mehr | 255 |
| ungeglättet ab 68 °C | sofort 255 (Notfall) |

Zwischen 45 und 70 °C steigt die Kurve gleichmäßig von 50 auf 255. Die Temperatur wird alle zwei Sekunden gelesen und über etwa 20 Sekunden geglättet. Die Drehzahl folgt langsam: höchstens +10 je Durchlauf nach oben, höchstens −2 nach unten (−3 beim Ausblenden unter 42 °C). Beim Start sowie beim Wechsel von aus zu an wird der Lüfter eine Sekunde voll angesteuert. Die Gerätezuordnung erfolgt über `pwmfan`, Plattformpfad `pwm-fan` und Sensor `soc-thermal`, ohne feste `hwmon`-Nummer.

**Warum der Sollwert mehrmals pro Sekunde gesetzt wird:** Auf der geprüften Box (Kernel `5.10.160-belabox`) hat die Kernel-Kühlsteuerung ein eigenes Kühlgerät für denselben Lüfter und stellt dessen Stufe zwischendurch zurück, bis hinunter auf PWM 0. Mit einer Stufenkurve, die nur alle fünf Sekunden schreibt, hörte man deshalb den Lüfter dauernd an- und ausgehen. Das Skript schreibt den Sollwert viermal pro Sekunde neu; Rückstellungen dauern dadurch nur Bruchteile einer Sekunde und die Drehzahl bleibt gleichmäßig.

Nach erfolgreicher Lüfterzuordnung fordert das Skript bei fehlenden/ungültigen Sensordaten, sonstigem regulärem Fehlerende und beim Stoppen PWM 255 an. systemd startet den unerwartet beendeten Dienst nach zehn Sekunden erneut. Es entstehen keine Temperatur-Messreihen; Start und Fehler erscheinen im Journal.

## Voraussetzungen

- Radxa ROCK 5B Plus mit passendem angeschlossenem PWM-Lüfter.
- Linux mit Bash, systemd, Coreutils und passender Gerätezuordnung in `/sys`.
- Praktisch geprüft: Ubuntu 22.04.5 mit `5.10.160-belabox #167`. Andere Images sind nicht praktisch geprüft.
- Root-Rechte über `sudo`, Zugriff auf die Box und keine zweite eigene Lüftersteuerung.

Die Erkennung eines PWM-Geräts beweist nicht, dass tatsächlich ein Lüfter angeschlossen ist. Vor Ort prüfen, dass er sich dreht. Der geprüfte Aufbau liefert keine Drehzahlmessung.

## Download und Installation

### Direkt auf der Box herunterladen (empfohlen)

Per SSH oder lokaler Konsole auf der Box anmelden. Die folgenden Befehle laufen **auf der Box**. Internetzugang, `wget` und `tar` werden benötigt. Falls `wget` auf Ubuntu fehlt, zuerst `sudo apt-get install wget ca-certificates` ausführen.

Dieser Weg lädt den aktuellen Stand des Zweigs `main` (Version 1.2.0). Eine feste Version mit Prüfsumme wird mit einer Release-Marke veröffentlicht; bis dahin den Inhalt vor der Installation selbst ansehen. Jeden Block einzeln ausführen und bei einer Fehlermeldung anhalten.

**1. In einen neuen temporären Ordner herunterladen:**

```bash
FAN_DOWNLOAD_DIR=$(mktemp -d /var/tmp/rock5bplus-fan-download-XXXXXX)
cd "$FAN_DOWNLOAD_DIR"
wget --https-only \
  --output-document=rock5bplus-fan-main.tar.gz \
  https://github.com/IRL4YOU/rock5bplus-fan/archive/refs/heads/main.tar.gz
```

**2. Entpacken und Syntax prüfen:**

```bash
tar -xzf rock5bplus-fan-main.tar.gz
cd rock5bplus-fan-main
bash -n rock5bplus-fan.sh install.sh
```

Anschließend mit **Installation starten** unten fortfahren. Der Download führt noch kein Skript aus.

### Alternative: über einen anderen Rechner kopieren

Im Bereich [Repository](https://github.com/IRL4YOU/rock5bplus-fan) über „Code → Download ZIP“ den aktuellen Stand herunterladen und entpacken. Den entpackten Ordner auf die Box kopieren; `BOX-IP` ersetzen:

```bash
scp -r rock5bplus-fan-main user@BOX-IP:/home/user/
ssh user@BOX-IP
```

Auf der Box:

```bash
cd /home/user/rock5bplus-fan-main
bash -n rock5bplus-fan.sh install.sh
```

### Installation starten

Der Installer stoppt eine aktive Vorgängerversion vor dem Dateiaustausch. Andere eigene Lüfterdienste vorab identifizieren und gezielt deaktivieren; der Installer erkennt diese nicht automatisch.

```bash
sudo bash install.sh
systemctl is-active rock5bplus-fan.service
systemctl is-enabled rock5bplus-fan.service
journalctl -u rock5bplus-fan.service -n 15 --no-pager
```

Erwartet: `active`, `enabled`, keine Neustartschleife und tatsächliche Lüfterdrehung oberhalb 45 °C. Der Installer sichert vorhandene Paketdateien im angezeigten `/var/tmp/belabox-fan-backup-*`-Ordner. Er installiert ausschließlich das Skript und den Dienst. Er verändert keine SSH-Einstellungen und startet die Box nicht neu.

Nach einem selbst veranlassten Neustart dieselben Prüfungen wiederholen. Bei Fehlern das Journal lesen; die Installationsmeldung allein ersetzt keinen Funktionstest. Der Installer stellt bei Fehlern frühere Dateien nicht automatisch wieder her.

## Stoppen und Rückweg

```bash
sudo systemctl disable --now rock5bplus-fan.service
```

Beim regulären Stoppen wird volle Leistung angefordert. Soll eine zuvor vorhandene Version zurückkehren, ausschließlich die beiden passenden Dateien aus der beim Installieren angezeigten Sicherung an ihre ursprünglichen Orte zurückkopieren, danach `sudo systemctl daemon-reload` und `sudo systemctl enable --now rock5bplus-fan.service` ausführen. Nur eine Regelung gleichzeitig betreiben. Bei einer Erstinstallation ist keine Vorgängerversion in der Sicherung enthalten.

## Grenzen und mögliche Anpassung

Ein- und Ausschaltgrenze liegen mit 45 °C (ein) und 42 °C (aus) auseinander, die Temperatur wird zusätzlich geglättet. So pendelt der Lüfter nicht um eine Grenze. Ein einzelner kurzer Temperaturausschlag hebt die Drehzahl höchstens um 10 an. Ab 68 °C (ungeglättet) wird sofort volle Leistung gesetzt. Die Eckwerte stehen als Zahlen im Skript (`45000`, `42000`, `70000`, `68000`, `50`, `255`) und lassen sich dort anpassen; danach `python3 -B test_fan.py` ausführen.

PWM ist die Ansteuerung, keine gemessene Drehzahl. Blockierter Lüfter, defekte Stromversorgung, verlorener Schreibzugriff, `SIGKILL` oder ein vollständiger Kernelstillstand sind durch das Skript nicht abgesichert. Die Fehlerbehandlung fordert volle Leistung an, garantiert deren Umsetzung aber nicht.

Die Kernel-Temperaturschwellen werden nicht verändert; der Kernel regelt den Lüfter erst ab seinen eigenen Schwellen mit. Das wiederholte Schreiben des Sollwerts verhindert nicht, dass der Kernel den Lüfter bei Überhitzung hochsetzt. Keine pauschale Überhitzungsschutz- oder Sommerbetriebsgarantie.

## Tests und Quellen

```bash
python3 -B test_fan.py
```

Die Tests laufen ohne Root und ohne echte Hardware auf einer isolierten Simulation der Geräteschnittstellen. Sie ersetzen keine thermischen Lasttests.

Schnittstellenreferenz: [Linux pwm-fan](https://www.kernel.org/doc/html/latest/hwmon/pwm-fan.html), [Linux-5.10-Treiberquelle](https://github.com/torvalds/linux/blob/v5.10/drivers/hwmon/pwm-fan.c). Es wird kein Linux-Treibercode mitgeliefert.

Fehlerberichte über [GitHub Issues](https://github.com/IRL4YOU/rock5bplus-fan/issues), mit Board, Betriebssystem und relevanter Fehlermeldung. Keine Zugangsdaten oder vollständigen privaten Konfigurationen einstellen.

## Lizenz

[MIT-Lizenz](LICENSE), Copyright 2026 IRL4YOU.

---

# English — ROCK 5B+ Fan Controller

[Zurück zu Deutsch](#rock-5b-lüftersteuerung) · [English as a separate page](README.en.md)

Temperature-based fan control by IRL4YOU for the **Radxa ROCK 5B Plus** running Linux and systemd. A standalone shell script with automatic startup, a continuous smoothed curve, a startup boost and error handling. This is an independent project, not an official Radxa or BELABOX product.

Version 1.1.0 replaces the stepped curve with a continuous, smoothed curve and rewrites the setpoint several times per second, because the kernel's own cooling control otherwise interferes (the fan kept switching on and off). See [Test status and limitations](#test-status-and-limitations).

Version 1.2.0: the kernel's thermal zone is switched off while the controller runs (it comes back on at 80 °C as a safety net), because it otherwise generates constant system messages and works against the controller.

## Fan control

| SoC temperature (smoothed) | PWM (0–255) |
|---|---:|
| Below 42 °C | 0 (off) |
| 42 to below 45 °C | a running fan continues at PWM 50; a stopped fan stays off |
| 45 °C | 50 |
| 57.5 °C | 152 |
| 70 °C and above | 255 |
| Unsmoothed 68 °C and above | 255 immediately (emergency) |

Between 45 and 70 °C the curve rises evenly from 50 to 255. The temperature is read every two seconds and smoothed over about 20 seconds. The speed follows slowly: at most +10 per cycle upwards and −2 downwards (−3 when fading out below 42 °C). At startup, and whenever the fan switches from off to on, full power is requested for one second. The controller identifies the fan using `pwmfan`, the `pwm-fan` platform path and the `soc-thermal` sensor, without relying on a fixed `hwmon` number.

**Why the setpoint is written several times per second:** On the tested board (kernel `5.10.160-belabox`) the kernel thermal framework has its own cooling device for the same fan and periodically lowers its level, down to PWM 0. With a stepped curve that wrote only every five seconds, the fan was heard switching on and off constantly. The script rewrites the setpoint four times per second; resets therefore last only fractions of a second and the speed stays even.

After identifying the fan, the script requests PWM 255 if sensor readings are missing or invalid, on other normal error exits, and when stopped. systemd restarts the service after ten seconds if it exits unexpectedly. The controller does not record temperature time series; startup and error messages appear in the journal.

## Requirements

- Radxa ROCK 5B Plus with a suitable PWM fan connected.
- Linux with Bash, systemd, Coreutils and the expected device interfaces in `/sys`.
- Tested on Ubuntu 22.04.5 with `5.10.160-belabox #167`. Other images have not been tested on hardware.
- Root privileges via `sudo`, access to the board and no second custom fan controller running.

Detecting a PWM device does not prove that a physical fan is connected. Check that the fan actually spins. The tested setup does not provide an RPM measurement.

## Download and installation

### Download directly on the board (recommended)

Log in to the board over SSH or through a local console. Run the following commands **on the board**. You need Internet access, `wget` and `tar`. If `wget` is missing on Ubuntu, first run `sudo apt-get install wget ca-certificates`.

These instructions download the current state of the `main` branch (version 1.2.0). A fixed version with a checksum will be published with a release tag; until then, inspect the contents yourself before installing. Run each block separately and stop if any command reports an error.

**1. Download into a new temporary directory:**

```bash
FAN_DOWNLOAD_DIR=$(mktemp -d /var/tmp/rock5bplus-fan-download-XXXXXX)
cd "$FAN_DOWNLOAD_DIR"
wget --https-only \
  --output-document=rock5bplus-fan-main.tar.gz \
  https://github.com/IRL4YOU/rock5bplus-fan/archive/refs/heads/main.tar.gz
```

**2. Extract and check shell syntax:**

```bash
tar -xzf rock5bplus-fan-main.tar.gz
cd rock5bplus-fan-main
bash -n rock5bplus-fan.sh install.sh
```

Continue with **Run the installer** below. Downloading the archive does not execute its scripts.

### Alternative: copy from another computer

Download the current state from the [repository](https://github.com/IRL4YOU/rock5bplus-fan) via “Code → Download ZIP” and extract it. Copy the extracted folder to the board, replacing `BOX-IP` with its address:

```bash
scp -r rock5bplus-fan-main user@BOX-IP:/home/user/
ssh user@BOX-IP
```

On the board:

```bash
cd /home/user/rock5bplus-fan-main
bash -n rock5bplus-fan.sh install.sh
```

### Run the installer

The installer stops an active previous version of this service before replacing its files. Identify and disable any other custom fan services first; the installer does not detect them automatically.

```bash
sudo bash install.sh
systemctl is-active rock5bplus-fan.service
systemctl is-enabled rock5bplus-fan.service
journalctl -u rock5bplus-fan.service -n 15 --no-pager
```

Expected results: `active`, `enabled`, no restart loop, and the physical fan spinning above 45 °C. The installer backs up existing package files in the displayed `/var/tmp/belabox-fan-backup-*` directory. It installs only the controller script and service. It does not change SSH settings or reboot the board.

Repeat these checks after a reboot that you initiate yourself. If anything fails, read the journal; an installation success message alone is not a functional test. The installer does not automatically restore previous files on failure.

Some script messages are in German: `LUEFTER_INSTALLATION_ERFOLGREICH` means “fan installation successful”; `Luefter nicht eindeutig gefunden` means “fan could not be identified uniquely”.

## Stopping and restoring a previous version

```bash
sudo systemctl disable --now rock5bplus-fan.service
```

A normal stop requests full fan power. To restore a previous version, copy only the two matching files from the backup shown during installation to their original locations, then run `sudo systemctl daemon-reload` and `sudo systemctl enable --now rock5bplus-fan.service`. Run only one controller at a time. On a first installation, the backup contains no previous version.

## Limits and adjustment

The switch-on limit (45 °C) and switch-off limit (42 °C) are 3 °C apart and the temperature is smoothed as well, so the fan does not oscillate around a limit. A single short temperature spike raises the speed by at most 10. At 68 °C (unsmoothed) full power is set immediately. The key values are plain numbers in the script (`45000`, `42000`, `70000`, `68000`, `50`, `255`) and can be adjusted there; afterwards run `python3 -B test_fan.py`.

PWM is a control value, not measured fan speed. The script cannot protect against a blocked fan, failed power supply, loss of write access, `SIGKILL` or a complete kernel freeze. Error handling requests full power but cannot guarantee that it is applied.

Kernel temperature thresholds are not modified; the kernel only joins in at its own thresholds. Rewriting the setpoint does not prevent the kernel from raising the fan on overheating. This is not a blanket guarantee against overheating or for operation in summer conditions.

## Tests and references

```bash
python3 -B test_fan.py
```

The tests run without root privileges or physical hardware, using isolated simulated device interfaces. They do not replace thermal load tests.

Interface references: [Linux pwm-fan](https://www.kernel.org/doc/html/latest/hwmon/pwm-fan.html), [Linux 5.10 driver source](https://github.com/torvalds/linux/blob/v5.10/drivers/hwmon/pwm-fan.c). No Linux driver code is distributed in this package.

Report problems through [GitHub Issues](https://github.com/IRL4YOU/rock5bplus-fan/issues), including the board, operating system and relevant error message. Do not include credentials or complete private configuration files.

## Test status and limitations

As of 17 October 2026 (version 1.2.0):

- Fifteen automated tests passed on macOS (new: thermal zone off while running, back on at 80 °C with hysteresis down to 76 °C, reset on exit): steady temperatures settle on the curve, full power from 68 °C, emergency jump, no stop once running between 42 and 45 °C, switch-off below 42 °C and no oscillation up to 45 °C, switch-on with startup boost, gradual changes (+10/−3 at most per cycle), a single spike is smoothed, invalid/missing/unreadable sensor data, missing/ambiguous fan identification. The tests ran only against simulated device interfaces, not on the board.
- Shell syntax checked. The script runs on a ROCK 5B Plus (kernel `5.10.160-belabox`) since 2 October 2026; there, the PWM read-back of an intermediate version showed no zero values in a 40-second measurement (before: repeated resets to 0). The quiet curve of this version was observed only briefly.
- Version 1.2.0 runs on a ROCK 5B Plus (kernel `5.10.160-belabox`) and restarted by itself after an unplanned reboot of the board; the thermal zone was off afterwards. The additional system load from the kernel messages was gone.
- The operator reports a more even and quieter fan. This is a perception, not a measurement; no RPM sensor is available.
- No thermal endurance, summer-condition or enclosure comparison tests. No board reboot with this version was exercised on purpose (the one mentioned was unplanned). The installer and service unit are unchanged from 1.0.0.

The German record and script checksums are in [TESTSTAND.md](TESTSTAND.md).

## License

[MIT License](LICENSE), Copyright 2026 IRL4YOU.
