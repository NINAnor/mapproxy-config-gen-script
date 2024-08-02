#!/usr/bin/env python3

from pathlib import Path

import backoff
import click
import requests
import yaml
from owslib.wms import WebMapService
from slugify import slugify


class FailedFetch(Exception):
    pass


@backoff.on_exception(
    backoff.expo,
    (FailedFetch, requests.exceptions.Timeout, requests.exceptions.ConnectionError),
)
def load_map(url, version) -> WebMapService:
    wms = WebMapService(url, version=version)

    if len(wms.contents) == 1:
        raise FailedFetch()

    return wms


@click.command()
@click.argument("url")
@click.option(
    "--output",
    default=Path("mapproxy.yaml"),
    type=click.Path(dir_okay=False, writable=True),
    callback=lambda ctx, param, value: Path(value),
)
@click.option("--version", default="1.1.1")
def generate_mapproxy_config(url, output: Path, version):
    wms = load_map(url, version=version)

    sources = {}
    layers = []

    for layer_name in wms.contents:
        layer = wms[layer_name]
        slug = slugify(layer_name)
        sources[slug] = {
            "type": "wms_retry",
            "retry": {"error_message": "Overforbruk"},
            "req": {
                "url": url + "?",
                "layers": layer_name,
                "transparent": True,
            },
        }
        bbox = layer.boundingBoxWGS84
        if bbox:
            sources[slug]["coverage"] = {
                "bbox": list(bbox),
                "srs": "EPSG:4326",
            }
        layers.append({"name": layer_name, "title": layer_name, "sources": [slug]})

    with output.open("w") as f:
        yaml.dump(
            {
                "services": {"demo": {}, "wms": {}},
                "sources": sources,
                "layers": layers,
            },
            f,
            encoding="utf-8",
            allow_unicode=True,
        )


if __name__ == "__main__":
    generate_mapproxy_config()
