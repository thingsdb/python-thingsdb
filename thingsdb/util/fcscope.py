from .cnscope import cnscope


def fcscope(scope: str) -> str:
    if scope.startswith("@collection:"):
        return scope

    cn = cnscope(scope)
    return f'@collection:{cn}'
