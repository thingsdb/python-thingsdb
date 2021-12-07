import re


rbegin = re.compile(r'^\s*(\/\/.*)?\s*')


def strip_code(code: str):
    """Strip white space and start comment from query code.

    This function now removes only white space and the first line comment
    when starting with // from code.
    """
    return rbegin.sub('', code).rstrip()
