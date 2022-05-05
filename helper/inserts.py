class _list(list):
    def __add__(self, other):
        raise Exception("Forbidden use of '+'")

    def __iadd__(self, other):
        raise Exception("Forbidden use of '+='")

    def __eq__(self, *args, **kwargs):
        raise Exception("Forbidden use of '=='")

    def __ge__(self, *args, **kwargs):
        raise Exception("Forbidden use of '>='")

    def __le__(self, *args, **kwargs):
        raise Exception("Forbidden use of '<='")

    def __gt__(self, *args, **kwargs):
        raise Exception("Forbidden use of '>'")

    def __lt__(self, *args, **kwargs):
        raise Exception("Forbidden use of '<'")

    def __ne__(self, *args, **kwargs):
        raise Exception("Forbidden use of '!='")

    def __imul__(self, *args, **kwargs):
        raise Exception("Forbidden use of '*='")
