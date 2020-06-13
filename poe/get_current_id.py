import requests as req


def get_next_change_id():
    """get last stash id from poe.ninza
    Args:
    Returns:
        string, next stash id
    """
    url = 'https://poe.ninja/api/Data/GetStats'
    res = req.get(url).json()
    return res['next_change_id']
