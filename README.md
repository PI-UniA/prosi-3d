![License](https://img.shields.io/github/license/pzimbrod/prosi-3d)
![Build Status](https://img.shields.io/github/actions/workflow/status/pzimbrod/prosi-3d/build)
[![Documentation Status](https://readthedocs.org/projects/prosi-3d/badge/?version=latest)](https://prosi-3d.readthedocs.io/en/latest/?badge=latest)
![Issues](https://img.shields.io/github/issues/pzimbrod/prosi-3d)
![PRs](https://img.shields.io/github/issues-pr/pzimbrod/prosi-3d)

# ProSi-3D: Robust and reliable process monitoring for Laser Powder Bed Fusion

This repo contains the source for a adaptable and configurable process monotoring system, (mostly) based on `Python`.
We also supply config files to run the package within a Docker container.

## Installation

### Requirements

The package deps are all listed in a `.yml` File in the `docker-env/` directory.
To install them using conda:

```bash
conda create --name prosi3d --file docker-env/environment.yml
```

### Using `tox`

For now, you can use the package by invoking the `tox` build system:

```bash
tox -e build
```
### Using `setuptools`

Alternatively, you can use the Python package `setuptools` to build the local package:

```bash
python setup.py develop
```

### Using Docker

Lastly, you can build and run the Docker container that comes along with the package:

```bash
docker build . -t prosi3d:latest
```

Run the container in a terminal:

```bash
docker run --rm -ti prosi3d:latest
```

## Usage/Examples

After Installation, you can import and use the package in Python.
Say, you want to process a data stream that comprises several acoustic sensors.
You can then read the data from a HDF file and create their respective features easily and uniformly:

```python
from prosi3d.sensors.acousticair import Accousticair
from prosi3d.sensors.acousticplatform import Accousticplatform
from prosi3d.sensors.recoater import Recoater

def test_analysis_loop():
    hdf_name = 'data/ch4raw_00593.h5'

    acc = Accousticair()
    acc_p = Accousticplatform()
    acc_r = Recoater()

    sensors = [acc,acc_p,acc_r]

    for sensor in sensors:
        sensor.get_data(hdf_name)
        sensor.process()
        sensor.plot_test()
        sensor.write()
```


## Contributing

Contributions are always welcome!

See `contributing.md` for ways to get started.

Please adhere to this project's `code of conduct`.


## Authors

- [@pzimbrod](https://pzimbrod.github.io)
- [@bjoernri](https://github.com/bjoernri)
- [@anna-lenastolze](https://github.com/anna-lenastolze)


## Acknowledgements

This project is kindly funded by the [German Bavarian Ministry of Economic Affairs, Regional Development and Energy](https://www.stmwi.bayern.de/en/).
## License

[MIT](https://choosealicense.com/licenses/mit/)
