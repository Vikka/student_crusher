class list_(list):
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

