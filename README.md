# WMS to Mapproxy
generates a mapproxy configuration file from wms service.

By default it configures the usage of this mapproxy plugin: https://github.com/NINAnor/mapproxy-wms-retry

This will allow to have a stable proxy with auto retry in case the original service is unreliable.

## How to run it
```bash
pdm install
pdm run python src/main.py URL_OF_THE_WMS
```
