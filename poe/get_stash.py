import json
import time
import datetime
import requests as req
from pathlib import Path


def now():
    _now = datetime.datetime.now()
    _now = _now.strftime("%Y-%m-%d %H:%M:%S")
    return _now


def get_data(uuid=""):
    endpoint = "http://api.pathofexile.com/public-stash-tabs"
    res = req.get(f"{endpoint}?id={uuid}")
    try:
        res_json = res.json()
        _next_id = res_json["next_change_id"]
        _stashes = res_json["stashes"]
    except Exception:
        print(res.status_code)
        print(res.text)
    return _next_id, _stashes


def prep(d):
    _now = now()
    if "items" in d:
        d["ts"] = _now
        for i, item in enumerate(d["items"]):
            if "properties" in item:
                for j, prop in enumerate(item["properties"]):
                    if type(d["items"][i]["properties"][j]["values"]) == list:
                        if len(d["items"][i]["properties"][j]["values"]) == 0:
                            d["items"][i]["properties"][j]["values"] = None
                        elif type(d["items"][i]["properties"][j]["values"][0]) == list:
                            d["items"][i]["properties"][j]["values"] = d["items"][i][
                                "properties"
                            ][j]["values"][0][0]
                        else:
                            d["items"][i]["properties"][j]["values"] = d["items"][i][
                                "properties"
                            ][j]["values"][0]
    return d


def save_to_local(uuid, data):
    Path("./temp").mkdir(parents=True, exist_ok=True)
    with open(f"./temp/{uuid}.jsonl", "w") as outfile:
        for entry in data:
            json.dump(entry, outfile)
            outfile.write("\n")


def _execute(_next_id):
    """actual request, request>save>return id
    Args:
        _next_id: stash id
    Returns:
        _next_id's next id
    """
    _next_id, stashes = get_data(_next_id)
    data = list(
        filter(
            lambda x: x["league"] in ("Delirium", "Harvest") and x["public"] is True,
            stashes,
        )
    )
    data = list(map(prep, data))
    if len(data) > 0:
        save_to_local(_next_id, data)
    return _next_id


def get_stashes(initial_id, timeout=5):
    """loop request until timeout
    Args:
        initial_id: first stash id
        timeout:
    Returns:
    """
    next_id = initial_id
    timeout_start = time.time()
    success_delay = 1
    fail_delay = 3
    while time.time() < timeout_start + timeout:
        _next_id = None
        try:
            _next_id = _execute(next_id)
            time.sleep(success_delay)
        except Exception:
            print(f"request failed at {next_id}")
            time.sleep(fail_delay)
            fail_delay += 1
        next_id = _next_id or next_id
