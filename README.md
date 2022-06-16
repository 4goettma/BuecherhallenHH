#### buecherhallen.py

Kleines Skript, welches die Liste der vom Kunden ausgeliehenen Medien farblich hervorgehoben und mit Warnungen ergänzt im Terminal darstellen kann.

Verglichen mit einem manuellen Aufruf der Seite im Webbrowser werden keine zusätzlichen Requests an den Server gesendet, jedoch unnötiger Datenverkehr eingespart und die Privatsphäre des Nutzer erhöht (es erfolgt kein Aufruf von Tracking-Skripten und Multimedia-Elementen).

Es wird keine Gewährleistung für fehlerhaft dargestellte Informationen übernommen, welche z.B. in Verspätungsgebühren für zu spät zurückgegebene Medien resultieren könnten!

```
Verwendung: ./buecherhallen.py [[Nummer der Kundenkarte] [Passwort/PIN]] [--renew] [--no-confirm]
Es können mehrere Konten mit einem Aufruf abgefragt werden, indem mehrere Zugangsdaten-Paare angegeben werden!

Optionen:
  --help        Diese Gebrauchsanweisung anzeigen.
  --renew       Bei fälligen Medien nachfragen, ob diese verlängert werden sollen.
  --no-confirm  Automatische Verlängerung nicht vom Nutzer bestätigen lassen, für unbeaufsichtigten Einsatz gedacht.
```