import json
import logging
import os
import shutil
import urllib
from encodings import utf_8
from string import Template

import requests
from flatten_json import flatten
from requests.adapters import HTTPAdapter, Retry


def call_api_v1(
    host: str,
    endpoint: str,
    method: str,
    api_key: str,
    json_data: dict = None,
    ca_path: str = "",
) -> requests.Response:
    url = urllib.parse.urljoin(host, endpoint)
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {"Content-Type": "application/json"}
    resp = None
    try:
        if json_data != None:
            resp = s.request(
                method=method.upper(),
                url=url,
                auth=(api_key, ""),
                headers=headers,
                json=json_data,
                verify=ca_path if ca_path != "" else True,
            )
        else:
            resp = s.request(
                method=method.upper(),
                url=url,
                auth=(api_key, ""),
                headers=headers,
                verify=ca_path if ca_path != "" else True,
            )
        resp.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        return resp
    except requests.exceptions.RequestException as e:
        logging.warning(f"Error: {e}")
        if resp != None and "application/json" in resp.headers.get("content-type"):
            logging.error("Error response from API: %s", resp.json())
        raise


def call_api_v2(
    host: str,
    endpoint: str,
    method: str,
    user_token: str,
    json_data: dict = None,
    ca_path: str = "",
) -> requests.Response:
    url = urllib.parse.urljoin(host, endpoint)
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(user_token),
    }
    resp = None
    try:
        if json_data != None:
            resp = s.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=json_data,
                verify=ca_path if ca_path != "" else True,
            )
        else:
            resp = s.request(
                method=method.upper(),
                url=url,
                headers=headers,
                verify=ca_path if ca_path != "" else True,
            )
        resp.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        return resp
    except requests.exceptions.RequestException as e:
        logging.warning(f"Error: {e}")
        if resp != None and "application/json" in resp.headers.get("content-type"):
            logging.error("Error response from API: %s", resp.json())
        raise


def download_file(url: str, filepath: str, ca_path: str = ""):
    with requests.get(url, stream=True, verify=ca_path if ca_path != "" else True) as r:
        with open(filepath, "wb") as f:
            shutil.copyfileobj(r.raw, f)


def extract_fields(json_data, field_map):
    output = {}
    for old_field, new_field in field_map.items():
        try:
            value = json_data[old_field]
        except KeyError:
            continue
        output[new_field] = value
    return output


def read_json_file(file_path):
    with open(file_path, "r", encoding=utf_8.getregentry().name) as f:
        json_data = json.load(f)
    return json_data


def write_json_file(file_path, json_data):
    with open(file_path, "w", encoding=utf_8.getregentry().name) as f:
        json.dump(json_data, f)
    # Set file permissions to 600 (read and write only for the owner)
    os.chmod(file_path, 0o600)


def flatten_json_data(json_data):
    return flatten(json_data, ".")


def get_best_runtime(json_list, edition, editor, kernel, short_version, full_version):
    # Best match with all five criteria matching
    for json_obj in json_list:
        if (
            "kernel" in json_obj
            and "edition" in json_obj
            and "editor" in json_obj
            and "shortVersion" in json_obj
            and "fullVersion" in json_obj
        ):
            if (
                json_obj["kernel"] == kernel
                and json_obj["edition"] == edition
                and json_obj["editor"] == editor
                and json_obj["shortVersion"] == short_version
                and json_obj["fullVersion"] == full_version
            ):
                if "imageIdentifier" in json_obj:
                    return json_obj["imageIdentifier"]

    # Best match with four criteria matching
    for json_obj in json_list:
        if (
            "kernel" in json_obj
            and "edition" in json_obj
            and "editor" in json_obj
            and "shortVersion" in json_obj
        ):
            if (
                json_obj["kernel"] == kernel
                and json_obj["edition"] == edition
                and json_obj["editor"] == editor
                and json_obj["shortVersion"] == short_version
            ):
                if "imageIdentifier" in json_obj:
                    return json_obj["imageIdentifier"]

    # If not Atleast three criterias are matching
    for json_obj in json_list:
        if "kernel" in json_obj and "edition" in json_obj and "editor" in json_obj:
            if (
                json_obj["kernel"] == kernel
                and json_obj["edition"] == edition
                and json_obj["editor"] == editor
            ):
                if "imageIdentifier" in json_obj:
                    return json_obj["imageIdentifier"]

    # If not atleast two criteria kernel and editor are matching
    for json_obj in json_list:
        if "kernel" in json_obj and "edition" in json_obj:
            if json_obj["kernel"] == kernel and json_obj["editor"] == editor:
                if "imageIdentifier" in json_obj:
                    return json_obj["imageIdentifier"]

    # If not atleast kernel is matching
    for json_obj in json_list:
        if "kernel" in json_obj:
            if json_obj["kernel"] == kernel:
                if "imageIdentifier" in json_obj:
                    return json_obj["imageIdentifier"]

    return None


def find_runtime(runtime_list, runtime_id: int):
    for runtime in runtime_list:
        if "id" in runtime and runtime["id"] == runtime_id:
            return {
                "runtime_kernel": runtime["kernel"],
                "runtime_edition": runtime["edition"],
                "runtime_editor": runtime["editor"],
                "runtime_fullversion": runtime["fullVersion"],
                "runtime_shortversion": runtime["shortVersion"],
            }
    return None


def get_absolute_path(path: str) -> str:
    if path.startswith("~"):
        return path.replace("~", os.path.expanduser("~"), 1)
    return os.path.abspath(path=path)
