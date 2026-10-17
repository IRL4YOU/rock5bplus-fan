# Änderungen

## 1.2.0 – 17. Oktober 2026

Wärmezone des Kernels im Betrieb ausgeschaltet.

- Die Kühlsteuerung des Kernels stellt den Lüfter sonst zurück und erzeugt dabei dauernd Systemmeldungen (spürbare Zusatzlast). Jetzt ist die Wärmezone im Betrieb aus; ab 80 °C schaltet sie sich als Sicherung (Drosselung) wieder ein, unter 76 °C wieder aus. Beim Beenden ist sie wieder an.
- Die Kühlschwelle des Kernels wird auf 84 °C gesetzt, damit er nicht vor der eigenen Regelung eingreift.
- Fünfzehn Tests (zwei neue für die Wärmezone).

## 1.1.0 – 2. Oktober 2026

Stufenlose, geglättete Kurve statt Stufen; behebt das ständige An- und Ausgehen des Lüfters.

- Kurve von 45 °C (PWM 50) bis 70 °C (PWM 255), Temperatur über etwa 20 Sekunden geglättet, langsame Drehzahländerung
  (höchstens +10 nach oben, −2 nach unten je Durchlauf). Aus unter 42 °C, ein ab 45 °C. Notfall: ab 68 °C sofort 255.
- Der Sollwert wird viermal pro Sekunde neu geschrieben, weil die Kernel-Kühlsteuerung dasselbe Kühlgerät sonst zwischendurch
  zurückstellt (auf der geprüften Box bis auf PWM 0).
- Anlaufimpuls, Fehlerbehandlung, Installer und Dienstdatei unverändert.
- Dreizehn Tests (statt zehn), angepasst an die neue Kurve. Download-Anleitung zeigt auf den Zweig `main`, bis eine Release-Marke existiert.

## 1.0.0 – 6. September 2026

Erste eigenständige Veröffentlichung der ROCK-5B-Plus-Lüftersteuerung.

- 2 °C Abkühlhysterese verhindert häufiges Umschalten nahe den Schaltgrenzen.
- Hochregeln weiterhin bei 40/48/55/65 °C; Abkühlgrenzen unter 38/46/53/63 °C.
- Dynamische Gerätezuordnung, Anlaufimpuls und Fehlerbehandlung bleiben erhalten.
- Installer sichert Vorgängerdateien und stoppt einen aktiven eigenen Dienst vor dem Austausch.
- Deutsche Anleitung und zehn automatisierte Tests enthalten.
- Auf einer ROCK 5B Plus installiert und laufender Dienst geprüft; Grenzen siehe TESTSTAND.md.
