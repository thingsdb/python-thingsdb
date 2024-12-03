import re

_VALID_NAME = re.compile(r'^[A-Za-z_][0-9A-Za-z_]{0,254}$')


def is_name(s: str) -> bool:
    return bool(_VALID_NAME.match(s))
