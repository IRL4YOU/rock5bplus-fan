# Prüfstand – Version 1.2.0

Stand: 17. Oktober 2026.

## Abgeschlossen

- Fünfzehn automatisierte Tests auf macOS bestanden (zusätzlich: Wärmezone im Betrieb aus, ab 80 °C wieder an mit Hysterese bis 76 °C, beim Beenden zurückgesetzt): Beharrungswerte auf der Kurve (45, 50, 57,5, 62, 67,999 °C), volle Leistung ab 70 °C, Notfall ab 68 °C ohne Rampe, kein Ausgehen zwischen 42 und 45 °C bei laufendem Lüfter, Ausschalten unter 42 °C ohne Pendeln bis 45 °C, Einschalten mit Anlaufimpuls, langsame Änderungen (+10/−3 je Durchlauf), Einzelspitze geglättet, ungültige/fehlende/unlesbare Sensordaten, fehlende und mehrdeutige Lüfterzuordnung.
- Tests verwenden isolierte temporäre Geräteschnittstellen mit simulierter Zeit; keine Manipulation echter Sensoren. Sie liefen nur auf macOS, nicht auf der Box.
- Bash-Syntax geprüft. Das Skript läuft seit 2. Oktober 2026 auf einer ROCK 5B Plus; PWM-Rücklesen einer Zwischenversion: in 40 Sekunden keine Nullwerte (vorher wiederholte Rückstellung auf 0). Die leise Kurve dieser Version wurde nur kurz beobachtet.
- Version 1.2.0 läuft auf einer ROCK 5B Plus (Kernel `5.10.160-belabox`) und startete nach einem ungeplanten Neustart der Box von selbst wieder; die Wärmezone stand danach auf aus. Die zusätzliche Systemlast durch die Kernel-Meldungen war danach nicht mehr vorhanden.
- Betreiber berichtet einen gleichmäßigeren und leiseren Lüfter. Das ist ein Eindruck, keine Messung.

Umgebung: Radxa ROCK 5B Plus, Ubuntu 22.04.5, Kernel `5.10.160-belabox #167`.

## Noch nicht nachgewiesen

- Kein thermischer Dauerlast-, Sommer- oder Gehäusevergleichstest; die Kurve wurde nur bei etwa 46 bis 51 °C unter Last beobachtet.
- Kein Drehzahlsensor: PWM-Rücklesen bestätigt die Ansteuerung, nicht die mechanische Drehung.
- Kein absichtlich veranlasster Box-Neustart mit dieser Version (der erwähnte war ungeplant). Installer und Dienstdatei sind gegenüber 1.0.0 unverändert.
- Das mehrfache Schreiben pro Sekunde ist auf einer Box mit Kernel `5.10.160-belabox` beobachtet; auf anderen Kerneln nicht geprüft.

## Paketprüfsummen

```text
670c5c2e4b5374dc9fd375c595380dc2104dc3247d066fe66ef0bad82d073c23  rock5bplus-fan.sh
a72ca4ec9e959b62b7b5e395bc75dbf44738afd4090cd6336b33353ba98fd3dd  rock5bplus-fan.service
a3ce9910577009b0065933a92029298f9174776573ec41d3f532fc0e1fda64fe  install.sh
```
