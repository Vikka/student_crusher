class list_(list):

    def __init__(self, it):
        if not it:
            super().__init__(it)
            return
        first = it[0]
        for i in it[1:-1]:
            if not isinstance(i, type(first)):
                raise ValueError("All elements must be of the same type")

        super().__init__(it)

    def __add__(self, other):
        raise Exception("Forbidden use of '+'", self, other)

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
