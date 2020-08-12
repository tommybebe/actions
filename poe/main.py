import datetime
from get_current_id import get_next_change_id
from get_stash import get_stashes
from set_data import Setter, get_list

if __name__ == "__main__":
    initial_id = get_next_change_id()
    get_stashes(initial_id, 60 * 5)
    setter = Setter()
    items = get_list()
    for item in items:
        setter.to_gcs(item)
    if len(items) > 0:
        setter.to_bigquery()

    setter.clear()
    print(initial_id, " / ", datetime.datetime.now(), "/ done")
