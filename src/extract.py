"""
extract.py - EXTRACT.

Descubre los datasets turísticos de Open Data Euskadi a partir del
catálogo, extrae la URL de descarga real de cada uno y guarda los JSON
crudos en data/raw/.

Notas de la fuente (documentadas en el notebook original):
- Open Data Euskadi NO tiene API REST estándar para estos datasets.
- El catálogo sí es navegable por tipo (ds_recursos_turisticos).
- Cada dataset tiene su página /catalogo/-/SLUG/ con el enlace al JSON.
"""

import json
import re
import ssl
import time
import urllib.request
import logging

import certifi

from .config import CATALOG_QUERY_URL, RAW_DIR

logger = logging.getLogger(__name__)

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
_SSL_CTX.minimum_version = ssl.TLSVersion.TLSv1_2
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Txoko-Bootcamp/1.0)"}


def _fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=timeout) as r:
        return r.read()


def descubrir_slugs():
    """Lista los slugs de datasets turísticos desde el catálogo."""
    html = _fetch(CATALOG_QUERY_URL).decode("latin-1", errors="replace")
    slugs = sorted(set(re.findall(r"/catalogo/-/([a-z0-9-]+)/", html)))
    logger.info("Datasets turísticos encontrados en el catálogo: %d", len(slugs))
    return slugs


def resolver_urls_json(slugs):
    """Para cada slug, extrae la URL real del JSON de su página de catálogo."""
    dataset_urls = {}
    for slug in slugs:
        url = f"https://opendata.euskadi.eus/catalogo/-/{slug}/"
        try:
            html_page = _fetch(url, timeout=8).decode("latin-1", errors="replace")
            json_urls = re.findall(
                r"https?://opendata\.euskadi\.eus/contenidos/[^\s\"'<>]+\.json",
                html_page,
            )
            if json_urls:
                dataset_urls[slug] = json_urls[0]
                logger.info("OK  %s", slug)
            else:
                logger.warning("Sin JSON descargable: %s", slug)
        except Exception as e:
            logger.warning("Fallo al resolver %s: %s", slug, type(e).__name__)
        time.sleep(0.1)  # cortesía al servidor
    logger.info("URLs de descarga: %d / %d", len(dataset_urls), len(slugs))
    return dataset_urls


def _slug_a_fname(slug):
    fname = slug.replace("-", "_")
    fname = re.sub(r"_de_euskadi$", "", fname)
    fname = re.sub(r"_de_las_tres_capitales.*", "", fname)
    return fname


def descargar_jsons(dataset_urls):
    """Descarga cada JSON validando que sea JSON real y lo guarda en raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    resultados = {}
    for slug, url in dataset_urls.items():
        fname = _slug_a_fname(slug)
        try:
            data = _fetch(url, timeout=10)
            # Validación: Open Data devuelve a veces HTML de error en vez de 404.
            if data[:1] not in (b"[", b"{"):
                resultados[fname] = {"status": "ERROR", "motivo": "no es JSON"}
                logger.warning("Respuesta no-JSON: %s", fname)
                continue
            parsed = json.loads(data)
            n = len(parsed) if isinstance(parsed, list) else 1
            (RAW_DIR / f"{fname}.json").write_bytes(data)
            resultados[fname] = {"status": "OK", "n_registros": n}
            logger.info("Descargado %-45s %4d registros", fname, n)
        except Exception as e:
            resultados[fname] = {"status": "ERROR", "motivo": str(e)}
            logger.warning("Fallo al descargar %s: %s", fname, e)

    ok = sum(1 for v in resultados.values() if v["status"] == "OK")
    logger.info("Descargados %d / %d datasets", ok, len(resultados))
    return resultados


def run():
    """Pipeline de extracción completo: catálogo -> JSONs en data/raw/."""
    slugs = descubrir_slugs()
    dataset_urls = resolver_urls_json(slugs)
    return descargar_jsons(dataset_urls)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()
