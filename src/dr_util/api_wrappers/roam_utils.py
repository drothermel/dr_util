# Copied and adapated from: https://github.com/Roam-Research/backend-sdks/blob/master/python/roam_client/client.py
# Tested manually when added but not yet maintained

import logging
import re
from typing import NoReturn

import requests
from schema import And, Optional, Or, Schema

HTTP_500_ERROR = 500
HTTP_400_ERROR = 400
INVALID_TOK_ERROR = 401
RETRY_ERROR = 503


# Basically ruff wants me to make my own exceptions, do this one day
# ruff: noqa: TRY002, TRY003
class RoamBackendClient:
    def __init__(self, token, graph) -> None:
        self.__token = token
        self.graph = graph
        self.__cache = {}

    def _error_message(self, status_code: int, response_json: str) -> NoReturn:
        if status_code == HTTP_500_ERROR:
            raise Exception("Error (HTTP 500): " + response_json)
        if status_code == HTTP_400_ERROR:
            raise Exception("Error (HTTP 400): " + response_json)
        if status_code == INVALID_TOK_ERROR:
            raise Exception("Invalid token or token doesn't have enough privileges.")
        if status_code == RETRY_ERROR:
            raise Exception(
                "Error (HTTP 503): Your graph is not ready yet for a request,"
                "please retry in a few seconds."
            )
        raise Exception("Unknown Error: " + response_json)

    def __make_request(self, path: str, method: str | None = None) -> tuple[str, str, dict[str, str]]:
        method = "POST" if method is None else method
        base_url = self.__cache.get(self.graph, "https://api.roamresearch.com")
        return (
            base_url + path,
            method,
            {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": "Bearer " + self.__token,
                "x-authorization": "Bearer " + self.__token,
            },
        )

    def call(self, path, method, body):
        url, method, headers = self.__make_request(path, body, method)
        resp = requests.post(url, headers=headers, json=body, allow_redirects=False, timeout=30)
        if resp.is_redirect or resp.is_permanent_redirect:
            if "Location" in resp.headers:
                mtch = re.search(
                    r"https://(peer-\d+).*?:(\d+).*", resp.headers["Location"]
                )
                if mtch is None:
                    raise Exception("TODO")
                peer_n, port = mtch.groups()
                # The redirect url
                self.__cache[self.graph] = (
                    "https://" + peer_n + ".api.roamresearch.com:" + port
                )
                return self.call(path, method, body)
            raise Exception("TODO")
        if not resp.ok:
            logging.info(resp.status_code)
            self._error_message(resp.status_code, resp.json())
        return resp


def q(client: RoamBackendClient, query: str, args=None):
    path = "/api/graph/" + client.graph + "/q"
    body = {"query": query}
    if args is not None:
        body["args"] = args
    resp = client.call(path, "POST", body)
    result = resp.json()
    return result["result"]


def pull(client: RoamBackendClient, pattern: str, eid: str):
    path = "/api/graph/" + client.graph + "/pull"
    body = {"eid": eid, "selector": pattern}
    resp = client.call(path, "POST", body)
    result = resp.json()
    return result["result"]


def pull_many(client: RoamBackendClient, pattern: str, eids: str):
    path = "/api/graph/" + client.graph + "/pull-many"
    body = {"eids": eids, "selector": pattern}
    resp = client.call(path, "POST", body)
    result = resp.json()
    return result["result"]


roam_block_location = Schema({"parent-uid": str, "order": Or(int, str)})

roam_block = Schema(
    {
        "string": str,
        Optional("uid"): str,
        Optional("open"): bool,
        Optional("heading"): int,
        Optional("text-align"): bool,
        Optional("children-view-type"): str,
    }
)

roam_create_block = Schema(
    {
        Optional("action"): And(str, lambda s: s == "create-block"),
        "location": roam_block_location,
        "block": roam_block,
    }
)


def create_block(client: RoamBackendClient, body):
    body["action"] = "create-block"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_create_block.validate(body))
    return resp.status_code


roam_move_block = Schema(
    {
        Optional("action"): And(str, lambda s: s == "move-block"),
        "location": roam_block_location,
        "block": {"uid": str},
    }
)


def move_block(client: RoamBackendClient, body):
    body["action"] = "move-block"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_move_block.validate(body))
    return resp.status_code


roam_update_block = Schema(
    {
        Optional("action"): And(str, lambda s: s == "update-block"),
        "block": {
            Optional("string"): str,
            "uid": str,
            Optional("open"): bool,
            Optional("heading"): int,
            Optional("text-align"): bool,
            Optional("children-view-type"): str,
        },
    }
)


def update_block(client: RoamBackendClient, body):
    body["action"] = "update-block"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_update_block.validate(body))
    return resp.status_code


roam_delete_block = Schema(
    {Optional("action"): And(str, lambda s: s == "delete-block"), "block": {"uid": str}}
)


def delete_block(client: RoamBackendClient, body):
    body["action"] = "delete-block"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_delete_block.validate(body))
    return resp.status_code


roam_create_page = Schema(
    {
        Optional("action"): And(str, lambda s: s == "create-page"),
        "page": {
            Optional("uid"): str,
            "title": str,
            Optional("children-view-type"): str,
        },
    }
)


def create_page(client: RoamBackendClient, body):
    body["action"] = "create-page"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_create_page.validate(body))
    return resp.status_code


roam_update_page = Schema(
    {
        Optional("action"): And(str, lambda s: s == "update-page"),
        "page": {
            "uid": str,
            Optional("title"): str,
            Optional("children-view-type"): str,
        },
    }
)


def update_page(client: RoamBackendClient, body):
    body["action"] = "update-page"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_update_page.validate(body))
    return resp.status_code


roam_delete_page = Schema(
    {Optional("action"): And(str, lambda s: s == "delete-page"), "page": {"uid": str}}
)


def delete_page(client: RoamBackendClient, body):
    body["action"] = "delete-page"
    path = "/api/graph/" + client.graph + "/write"
    resp = client.call(path, "POST", roam_delete_page.validate(body))
    return resp.status_code


init_graph = Schema({"graph": str, "token": str})


def initialize_graph(inp):
    init_graph.validate(inp)
    return RoamBackendClient(inp["token"], inp["graph"])
