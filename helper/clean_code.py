from _ast import Import, ImportFrom, Name, Call, FunctionDef, Attribute, Try
from ast import NodeTransformer, parse, unparse, dump

DEFAULT_PENALTY = 10
IMPORT_PENALTY = DEFAULT_PENALTY
FROM_IMPORT_PENALTY = DEFAULT_PENALTY
BUILTIN_PENALTY = DEFAULT_PENALTY
FUNCTION_PENALTY = DEFAULT_PENALTY
TRY_CLAUSE_PENALTY = DEFAULT_PENALTY

AUTHORIZED_MODULES = {}
UNAUTHORIZED_BUILTINS = {'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException',
                         'BlockingIOError', 'BrokenPipeError', 'BufferError', 'BytesWarning',
                         'ChildProcessError', 'ConnectionAbortedError', 'ConnectionError',
                         'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
                         'EOFError', 'Ellipsis', 'EncodingWarning', 'EnvironmentError',
                         'Exception', 'False', 'FileExistsError', 'FileNotFoundError',
                         'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError',
                         'ImportError', 'ImportWarning', 'IndentationError', 'IndexError',
                         'InterruptedError', 'IsADirectoryError', 'KeyError', 'KeyboardInterrupt',
                         'LookupError', 'MemoryError', 'ModuleNotFoundError', 'NameError', 'None',
                         'NotADirectoryError', 'NotImplemented', 'NotImplementedError', 'OSError',
                         'OverflowError', 'PendingDeprecationWarning', 'PermissionError',
                         'ProcessLookupError', 'RecursionError', 'ReferenceError',
                         'ResourceWarning', 'RuntimeError', 'RuntimeWarning', 'StopAsyncIteration',
                         'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError',
                         'SystemExit', 'TabError', 'TimeoutError', 'True', 'TypeError',
                         'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError',
                         'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning',
                         'ValueError', 'Warning', 'WindowsError', 'ZeroDivisionError', '_',
                         '__build_class__', '__debug__', '__doc__', '__import__', '__loader__',
                         '__name__', '__package__', '__spec__', 'abs', 'aiter', 'all', 'anext',
                         'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
                         'callable', 'chr', 'classmethod', 'compile', 'complex', 'copyright',
                         'credits', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval',
                         'exec', 'execfile', 'exit', 'filter', 'float', 'format', 'frozenset',
                         'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input',
                         'int', 'isinstance', 'issubclass', 'iter', 'len', 'license', 'list',
                         'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct',
                         'open', 'ord', 'pow', 'print', 'property', 'quit', 'range', 'repr',
                         'reversed', 'round', 'runfile', 'set', 'setattr', 'slice', 'sorted',
                         'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'}


def is_authorized(import_: Import | ImportFrom) -> bool:
    """
    Function that checks if the import node is authorized
    """
    unauthorized_modules = [alias.name for alias in import_.names if
                            alias.name not in AUTHORIZED_MODULES]
    return not unauthorized_modules


class ASTCleaner(NodeTransformer):
    """
    AST visitor that deletes unauthorized nodes
    """

    def __init__(self):
        self.unauthorized_imports = list()
        self.unauthorized_from_imports = list()
        self.unauthorized_func_call = list()
        self.unauthorized_method_call = list()
        self.unauthorized_func_def = list()
        self.unauthorized_try_clause = 0
        self.score = 0

    def _visit_import_generic(
            self, node: Import | ImportFrom,
            penalty: int, unauthorized_import_buffer: list
    ) -> Import | ImportFrom | None:
        if not is_authorized(node):
            unauthorized_import_buffer.append(node)
            self.score += penalty
            return None
        return node

    def visit_Import(self, node: Import) -> Import | None:
        """AST visitor that deletes unauthorized imports"""
        return self._visit_import_generic(node, IMPORT_PENALTY,
                                          self.unauthorized_imports)

    def visit_ImportFrom(self, node: ImportFrom) -> ImportFrom | None:
        """AST visitor that deletes unauthorized imports from"""
        return self._visit_import_generic(node, FROM_IMPORT_PENALTY,
                                          self.unauthorized_from_imports)

    def visit_Call(self, node: Call) -> Call | None:
        """AST visitor that deletes unauthorized calls"""
        if isinstance(node.func, Name) and node.func.id in UNAUTHORIZED_BUILTINS:
            self.unauthorized_func_call.append(node)
            self.score -= BUILTIN_PENALTY
            return None
        if isinstance(node.func, Attribute):
            self.unauthorized_method_call.append(node)
            self.score -= BUILTIN_PENALTY
            return None
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef | None:
        """AST visitor that deletes unauthorized functions"""
        if node.name in UNAUTHORIZED_BUILTINS:
            self.unauthorized_func_def.append(node.name)
            self.score -= FUNCTION_PENALTY
            return None
        self.generic_visit(node)
        return node

    def visit_Try(self, node: Try) -> Try | None:
        """AST visitor that deletes unauthorized try clauses"""
        self.unauthorized_try_clause += 1
        self.score -= TRY_CLAUSE_PENALTY
        self.generic_visit(node)

        return None

    def get_analysis(self) -> str:
        result = list()
        if self.unauthorized_imports:
            result.append(f'Unauthorized imports: {", ".join(self.unauthorized_imports)}')
        if self.unauthorized_from_imports:
            result.append(
                f'Unauthorized from imports: {", ".join(self.unauthorized_from_imports)}')
        if self.unauthorized_func_call:
            result.append(
                f'Unauthorized builtin function calls: {", ".join(self.unauthorized_func_call)}')
        if self.unauthorized_method_call:
            result.append(
                f'Unauthorized builtin method calls: {", ".join(self.unauthorized_method_call)}')
        if self.unauthorized_func_def:
            result.append(
                f'Unauthorized functions def: {", ".join(self.unauthorized_func_def)}')
        if self.unauthorized_try_clause:
            result.append(
                f'Unauthorized try clauses: {self.unauthorized_try_clause}')
        return '; '.join(result)


def ast_clean(code: str) -> tuple[str, int, str]:
    """
    Function that prints the AST of the module
    """
    try:
        original_node = parse(code)
        # print(dump(original_node, indent=4))
        cleaner = ASTCleaner()
        cleaned_node = cleaner.visit(original_node)
    except Exception as e:
        return "", -142857, 'AST CRASH'
    return unparse(cleaned_node), cleaner.score, cleaner.get_analysis()
