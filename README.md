# WMS to Mapproxy
generates a mapproxy configuration file from wms service.

By default it configures the usage of this mapproxy plugin: https://github.com/NINAnor/mapproxy-wms-retry

This will allow to have a stable proxy with auto retry in case the original service is unreliable.

## How to run it
```bash
pipx run --spec git+https://github.com/NINAnor/mapproxy-config-gen-script.git mapproxy-config-gen https://wms.geonorge.no/skwms1/wms.nib-prosjekter
```
