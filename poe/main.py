import datetime
from get_current_id import get_next_change_id
from get_stash import get_stashes
from set_data import Setter, get_list

if __name__ == "__main__":
    initial_id = get_next_change_id()
    get_stashes(initial_id, 60*5)
    setter = Setter()

    for item in get_list():
        setter.to_gcs(item)

    setter.to_bigquery()
    print(initial_id, ' / ', datetime.datetime.now(), '/ done')
