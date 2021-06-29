# Interne Coding Guidelines zur Ausarbeitung des ProSi-3D Überwachungstools

## Python

### Allgemeines

Im Allgemeinen sollten die Richtlinien des [Python Enhancement Proposals (PEP)](https://www.python.org/dev/peps/) eingehalten werden. Insbesondere sind die Richtlinien in [PEP8](https://www.python.org/dev/peps/pep-0008/) relevant.

Zusätzlich ist das Python Modul ```autopep8``` in das Docker-Image eingebunden, das Code versucht, automatisch nach PEP8 Standard zu formatieren. Das funktioniert allerdings nicht immer, daher sollte von Vornherein auf Konformität geachtet werden. Zusätzlich kann es hilfreich sein, ein entsprechendes Plugin für den eigenen Editor zu installieren. Diese sind bspw. für Atom und VS Code verfügbar.

### Hierarchie

Die Algorithmen zur Datenverarbeitung sind hierarchisch in Klassen organisiert. Dabei existieren Basisklassen ([Abstract Base Classes / ABC](https://docs.python.org/3/library/abc.html)), die die Grundoperationen über virtuelle Methoden spezifizieren. Diese Methoden müssen beim Erben dieser Klassen neu und applikationsspezifisch definiert werden, sonst wird ein Fehler ausgegeben.
Dadurch wird vermieden, dass die implementierten Algorithmen unterschiedliche Syntax haben und das Aufrufen der Methoden nicht einheitlich ist.

Ein Beispiel für die Klassenstruktur wäre:

```
.
└── Data Model (ABC)
   ├── Classifier (ABC)
   │     ├── kNN
   │     ├── CNN
   │     └── Naive Bayes
   ├── Cluster (ABC)
   │     ├── k-Means
   │     ├── MeanShift
   │     └── Spectral Cluster
   └── Regressor (ABC)
```

Bei der Definition eines k-Nearest-Neighbor Algorithmuss müssen also in diesem Beispiel sowohl die Methoden in der Elternklasse ```Classifier``` als auch in ```Data Model``` definiert sein. Weitere, anwendungsspezifische Methoden können jederzeit ergänzt werden.

Beim Erstellen neuer Klassen muss die jeweilige Basisklasse am Anfang via ```from ... import ...``` Statement mit dem absoluten Pfad eingebunden werden.

### Scope

Die eingeführten Klassen arbeiten sowohl mit öffentlichen Attributen (public), als auch mit privaten (private). Die Top-Level Methoden in den obersten Basisklassen sind öffentlich. Über diese werden die verarbeiteten Daten nach außen kommuniziert.

Attribute von Downstream Klassen, die eine spezielle Funktionalität implementieren, sollten als privat deklariert sein. Dafür wird ein dem Namen des Attributs vorangestellter Unterstrich hinzugefügt:

Falsch:
```python
    class myClass(myAbstractClass):
        def myFunc:
            pass
```

Richtig:
```python
    class myClass(myAbstractClass):
        def _myFunc:
            pass
```

## Dokumentation

Die Dokumentation für dieses Projekt wird mithilfe von Sphinx generiert. Im Zuge dessen beinhaltet das Docker Image das entsprechende Python-Package ```sphinx```. 

Daher sollte geschriebener Code mit Docstrings versehen werden, damit die Kommentare korrekt von Sphinx eingelesen werden können:

Falsch:
```python
    class myClass: # Neuer Algorithmus
        pass
```

Richtig:
```python
    """ Neuer Algorithmus """
    class myClass:
        pass
```