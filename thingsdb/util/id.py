def id(val):
    if isinstance(val, str) and val.startswith('room:'):
        try:
            id = int(val[5:])
            return id
        except Exception:
            return None
    return val.get('#')


if __name__ == '__main__':
    print(id('room:123'))
    print(id('room:nil'))
    print(id({'#': 123}))
    print(id({}))
