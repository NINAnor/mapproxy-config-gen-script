#!/usr/bin/env python3

import functools
import types
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
    max_time=60,
)
def load_map(url, version) -> WebMapService:
    wms = WebMapService(url, version=version)

    if len(wms.contents) == 1:
        raise FailedFetch()

    return wms


def visit_layer(layer):
    result = {
        "name": layer.name or layer.title,
        "title": layer.title,
    }
    if layer.layers:
        result["layers"] = list(map(visit_layer, layer.layers))
    else:
        result["sources"] = [slugify(layer.name)]
    return result


def get_sources(layer, url):
    if layer.layers:
        result = {}
        for child_layer in layer.layers:
            result.update(get_sources(child_layer, url))
        return result
    else:
        result = {
            "type": "wms_retry",
            "retry": {"error_message": "Overforbruk"},
            "req": {
                "url": url + "?",
                "layers": layer.name,
                "transparent": True,
            },
        }
        bbox = layer.boundingBoxWGS84
        if bbox:
            result["coverage"] = {
                "bbox": list(bbox),
                "srs": "EPSG:4326",
            }
        return {slugify(layer.name): result}


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

    get_sources_with_url = functools.partial(get_sources, url=url)

    layers = list(map(visit_layer, wms.contents.values()))
    sources = get_sources_with_url(types.SimpleNamespace(layers=wms.contents.values()))

    with output.open("w") as f:
        yaml.dump(
            {
                "services": {
                    "demo": None,
                    "wms": {"md": {"title": layers[0]["title"]}},
                },
                "sources": sources,
                "layers": layers[0]["layers"],
            },
            f,
            encoding="utf-8",
            allow_unicode=True,
        )


if __name__ == "__main__":
    generate_mapproxy_config()
