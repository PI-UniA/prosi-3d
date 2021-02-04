# Interne Coding Guidelines zur Ausarbeitung des ProSi-3D Überwachungstools

## Python

Im Allgemeinen sollten die Richtlinien des [https://www.python.org/dev/peps/](Python Enhancement Proposals (PEP)) eingehalten werden. Insbesondere sind die Richtlinien in [https://www.python.org/dev/peps/pep-0008/](PEP8) relevant.

Zusätzlich ist das Python Modul ```autopep8``` in das Docker-Image eingebunden, das Code versucht, automatisch nach PEP8 Standard zu formatieren. Das funktioniert allerdings nicht immer, daher sollte von Vornherein auf Konformität geachtet werden. Zusätzlich kann es hilfreich sein, ein entsprechendes Plugin für den eigenen Editor zu installieren. Diese sind bspw. für Atom und VS Code verfügbar.

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