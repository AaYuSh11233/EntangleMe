import urllib
from urllib.parse import urljoin

from classiq.interface.server import routes

import classiq

QUERY_START_MARK = "?"
VERSION_QUERY_PARAM = "version"
LOGIN_QUERY_PARAM = "login"


def client_ide_base_url() -> str:
    client = classiq._internals.client.client()
    return str(client.config.ide)


def circuit_page_search_params(circuit_version: str) -> str:
    return urllib.parse.urlencode(
        {
            LOGIN_QUERY_PARAM: True,
            VERSION_QUERY_PARAM: circuit_version,
        }
    )


def circuit_page_uri(circuit_id: str, circuit_version: str, include_query: bool) -> str:
    url = urljoin(f"{routes.ANALYZER_CIRCUIT_PAGE}/", circuit_id)
    if include_query:
        query_string = circuit_page_search_params(circuit_version)
        url += QUERY_START_MARK + query_string
    return url
