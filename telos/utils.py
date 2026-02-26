import time


def gen_timestamp() -> int:
    """gen_timestamp.
    Generate a timestamp.

    Args:

    Returns:
        int: Timestamp in integer representation. User `str()` to
            transform to string.
    """
    return int(time.time_ns() * 1e6)
