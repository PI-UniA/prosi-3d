# Offizielles Repository des StMWi Forschungsprojektes ProSi-3D - Prozesssicheres Laserstrahlschmelzen

## Einführung
Dieses Repository beinhaltet den im Forschungsprojekt erarbeiteten Code sowie die Konfigurationsdateien, um diesen in einem Docker Container laufen zu lassen. Dies dient dazu, um die Paketabhängigkeiten für jede Plattform aufzulösen und auf dem Client keine Konflikte mit bestehenden Python-Installationen zu erzeugen.

## Einrichten der API Umgebung
Im Hauptverzeichnis befindet sich das `Dockerfile`, das die Konfiguration des Containers beschreibt. Die Basis ist eine Anaconda Installation mit Python 3. Die Abhängigkeiten sind in `env/environment.yml` zu finden. Sind weitere gewünscht, können diese hier einfach ergänzt werden.

Um den Container (einmalig) lokal zu erstellen, muss folgender Befehl im Hauptverzeichnis dieses Repositories in einem Terminal (Linux / OS X) oder der PowerShell ausgeführt werden:

```bash
docker build . -t prosi3d:latest
```

Danach kann der Container jederzeit mit einem interaktiven Terminal gestartet werden:

```bash
docker run --rm -ti prosi3d
```
Für die Entwicklungsumgebung [VS Code](https://code.visualstudio.com) steht auch eine auf Docker basierende Entwicklungsumgebung als Remote Container zur Verfügung.

Ansonsten funktioniert auch jede andere Anaconda Installation basierend auf Python 3.8, die die Abhängigkeiten in `env/environment.yml` enthält.

## Einrichten der Frontend Umgebung

Das Frontend kommuniziert eigenständig mit der API und kann im Browser unter `localhost:5005` adressiert werden. Der Stack basiert auf dem Open Source Git Repository "[django-dashboard-black](https://github.com/app-generator/django-dashboard-black)" von Appseed. Die Installation läuft vollständig in Docker ab und nutzt u.a. Django und NGINX, um die Web-Services zur Verfügung zu stellen.

Um die Umgebung zu starten, müssen die einzelnen Docker-Services in der Kommandozeile assembliert und ausgeführt werden:

```bash
$ sudo docker-compose pull && sudo docker-compose build && sudo docker-compose up -d
```

Alternativ kann auch eine lokale Installation wie in der [README-Datei](dashboard/README.md) beschrieben durchgeführt werden. Danach läuft der Service im Hintergrund und der Zugriff über den Browser ist möglich.

## Builds und Hinweise für Developer

Das Package arbeitet mit `tox`. Damit lassen sich Builds einfach automatisch erzeugen, Tests automatisiert durchführen und die Dokumentation generieren lassen.
Die jeweiligen Pipelines sind in der Datei `tox.ini` definiert. Um beispielsweise den dort definierten Workflow zur Erstellung der Dokumentation auszuführen, muss folgendes in ein Terminal eingegeben werden:

```bash
tox -e docs
```

Die generierten HTML-Dateien sind dann im Ordner `docs/_build/html` zu finden.

Um mit den Dateien ad hoc zu arbeiten, sollte mithilfe von `setuptools` eine Dev-Version des Pakets erstellt werden.
Das geht, indem man in einem Terminal im Hauptverzeichnis die Setup-Datei aufruft:

```bash
python setup.py develop
```

Das Paket verhält sich dann wie ein normal installiertes. Es können also alle Klassen, Methoden und Objekte durch Import des Pakets `prosi3d` geladen werden