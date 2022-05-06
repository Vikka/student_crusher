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
        raise Exception("Forbidden use of '+' on a list")

    def __iadd__(self, other):
        raise Exception("Forbidden use of '+= on a list'")

    def __eq__(self, *args, **kwargs):
        raise Exception("Forbidden use of '== on a list'")

    def __ge__(self, *args, **kwargs):
        raise Exception("Forbidden use of '>= on a list'")

    def __le__(self, *args, **kwargs):
        raise Exception("Forbidden use of '<= on a list'")

    def __gt__(self, *args, **kwargs):
        raise Exception("Forbidden use of '>' on a list")

    def __lt__(self, *args, **kwargs):
        raise Exception("Forbidden use of '<' on a list")

    def __ne__(self, other):
        raise Exception("Forbidden use of '!= on a list'", self, other)

    def __imul__(self, *args, **kwargs):
        raise Exception("Forbidden use of '*= on a list'")

    def __mul__(self, other):
        return self.__class__(super().__mul__(other))

