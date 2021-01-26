# Offizielles Repository des StMWi Forschungsprojektes ProSi-3D - Prozesssicheres Laserstrahlschmelzen

## Einführung
Dieses Repository beinhaltet den im Forschungsprojekt erarbeiteten Code sowie die Konfigurationsdateien, um diesen in einem Docker Container laufen zu lassen. Dies dient dazu, um die Paketabhängigkeiten für jede Plattform aufzulösen und auf dem Client keine Konflikte mit bestehenden Python-Installationen zu erzeugen.

## Einrichten der API Umgebung
Im Hauptverzeichnis befindet sich das `Dockerfile`, das die Konfiguration des Containers beschreibt. Die Basis ist eine Anaconda Installation mit Python 3. Die Abhängigkeiten sind in `env/environment.yml` zu finden. Sind weitere gewünscht, können diese hier einfach ergänzt werden.

Um den Container (einmalig) lokal zu erstellen, muss folgender Befehl im Hauptverzeichnis dieses Repositories in einem Terminal (Linux / OS X) oder der PowerShell ausgeführt werden:

`docker build .`

Danach kann der Container jederzeit mit einem interaktiven Terminal gestartet werden:

`docker run -ti prosi3d`

Ansonsten funktioniert auch jede andere Anaconda Installation basierend auf Python 3.8, die die Abhängigkeiten in `env/environment.yml` enthält.

## Einrichten der Frontend Umgebung

Das Frontend kommuniziert eigenständig mit der API und kann im Browser unter `localhost:5005` adressiert werden. Der Stack basiert auf dem Open Source Git Repository "[django-dashboard-black](https://github.com/app-generator/django-dashboard-black)" von Appseed. Die Installation läuft vollständig in Docker ab und nutzt u.a. Django und NGINX, um die Web-Services zur Verfügung zu stellen.

Um die Umgebung zu starten, müssen die einzelnen Docker-Services in der Kommandozeile assembliert und ausgeführt werden:

```bash
$ sudo docker-compose pull && sudo docker-compose build && sudo docker-compose up -d
```

Alternativ kann auch eine lokale Installation wie in der [README-Datei](dashboard/README.md) beschrieben durchgeführt werden. Danach läuft der Service im Hintergrund und der Zugriff über den Browser ist möglich.

## ToDo

- [x] Virtual Environment
- [ ] Python-Grundstruktur
- [ ] Datenvorverarbeitung
- [ ] Statistische Auswertung
- [ ] Machine Learning Auswertung
- [ ] User Frontend