=============
Installation
=============


Requirements
-------------

The package deps are all listed in a `.yml` File in the `docker-env/` directory.
To install them using conda:

::
    conda create --name prosi3d --file docker-env/environment.yml

Using ``tox``
--------------

For now, you can use the package by invoking the ``tox`` build system:

::
    tox -e build

Using ``setuptools``
---------------------

Alternatively, you can use the Python package ``setuptools`` to build the local package:

::
    python setup.py develop

Using Docker
-------------

Lastly, you can build and run the Docker container that comes along with the package:

::
    docker build . -t prosi3d:latest

Run the container in a terminal:

::
    docker run --rm -ti prosi3d:latest