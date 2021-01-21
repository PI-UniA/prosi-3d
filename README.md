# Offizielles Repository des StMWi Forschungsprojektes ProSi-3D - Prozesssicheres Laserstrahlschmelzen

## Einführung
Dieses Repository beinhaltet den im Forschungsprojekt erarbeiteten Code sowie die Konfigurationsdateien, um diesen in einem Docker Container laufen zu lassen. Dies dient dazu, um die Paketabhängigkeiten für jede Plattform aufzulösen und auf dem Client keine Konflikte mit bestehenden Python-Installationen zu erzeugen.

## Einrichten der Umgebung
Im Hauptverzeichnis befindet sich das `Dockerfile`, das die Konfiguration des Containers beschreibt. Die Basis ist eine Anaconda Installation mit Python 3. Die Abhängigkeiten sind in `env/environment.yml` zu finden. Sind weitere gewünscht, können diese hier einfach ergänzt werden.

Um den Container (einmalig) lokal zu erstellen, muss folgender Befehl im Hauptverzeichnis dieses Repositories in einem Terminal (Linux / OS X) oder der PowerShell ausgeführt werden:

`docker build .`

Danach kann der Container jederzeit mit einem interaktiven Terminal gestartet werden:

`docker run -ti prosi3d`

Ansonsten funktioniert auch jede andere Anaconda Installation basierend auf Python 3.8, die die Abhängigkeiten in `env/environment.yml` enthält.

## ToDo

- [x] Virtual Environment
- [ ] Python-Grundstruktur
- [ ] Datenvorverarbeitung
- [ ] Statistische Auswertung
- [ ] Machine Learning Auswertung
- [ ] User Frontend