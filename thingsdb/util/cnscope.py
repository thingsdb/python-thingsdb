import re

_VALID_NAME = re.compile(r'^[A-Za-z_][0-9A-Za-z_]{0,254}')


def cnscope(scope):
    """Returns the collection name from a scope name.

    Eexamples:
        cnscope('//Stuff') -> 'Stuff'
        cnscope('@collection:Stuff') -> 'Stuff'
    """

    if ':' in scope:
        name = scope.split(':')[-1]
    elif '/' in scope:
        name = scope.split('/')[-1]
    else:
        name = ''

    if _VALID_NAME.match(name):
        return name

    raise ValueError(f'invalid (collection) scope name: {scope}')


if __name__ == '__main__':
    assert cnscope('//stuff') == 'stuff'
    assert cnscope('/collection/stuff') == 'stuff'
    assert cnscope('@:stuff') == 'stuff'
    print('OK')
