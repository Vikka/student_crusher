from _ast import Import, ImportFrom, Name, Call, FunctionDef, Attribute, Try, Break
from ast import NodeTransformer, parse, unparse, dump

from helper.report import Report

DEFAULT_PENALTY = 10
IMPORT_PENALTY = DEFAULT_PENALTY
FROM_IMPORT_PENALTY = DEFAULT_PENALTY
FUNC_CALL_PENALTY = DEFAULT_PENALTY
METHOD_CALL_PENALTY = DEFAULT_PENALTY
FUNC_DEF_PENALTY = DEFAULT_PENALTY
TRY_CLAUSE_PENALTY = DEFAULT_PENALTY

AUTHORIZED_MODULES = {}
AUTHORIZED_BUILTINS = {'print', }
FORBIDDEN_BUILTINS = {'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException',
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
                         'open', 'ord', 'pow', 'property', 'quit', 'range', 'repr',
                         'reversed', 'round', 'runfile', 'set', 'setattr', 'slice', 'sorted',
                         'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'}


def is_authorized(import_: Import | ImportFrom) -> bool:
    """
    Function that checks if the import node is authorized
    """
    forbidden_modules = [alias.name for alias in import_.names if
                            alias.name not in AUTHORIZED_MODULES]
    return not forbidden_modules


class ASTCleaner(NodeTransformer):
    """
    AST visitor that deletes forbidden nodes
    """

    def __init__(self, report: Report):
        self.report = report

        self.forbidden_imports = list()
        self.forbidden_from_imports = list()
        self.forbidden_func_call = list()
        self.forbidden_method_call = list()
        self.forbidden_func_def = list()
        self.forbidden_try_clause = 0
        self.forbidden_break_statement = 0
        self.score = 0

    @staticmethod
    def _visit_import_generic(node: Import | ImportFrom, forbidden_import_buffer: list
                              ) -> Import | ImportFrom | None:
        if not is_authorized(node):
            forbidden_import_buffer.append(node)
            return None
        return node

    def visit_Import(self, node: Import) -> Import | None:
        """AST visitor that deletes forbidden imports"""
        return self._visit_import_generic(node, self.forbidden_imports)

    def visit_ImportFrom(self, node: ImportFrom) -> ImportFrom | None:
        """AST visitor that deletes forbidden imports from"""
        return self._visit_import_generic(node, self.forbidden_from_imports)

    def visit_Call(self, node: Call) -> Call | None:
        """AST visitor that deletes forbidden calls"""
        if isinstance(node.func, Name) and node.func.id in FORBIDDEN_BUILTINS:
            # self.forbidden_func_call.append(node.func.id)
            return None
        if isinstance(node.func, Attribute):
            # self.forbidden_method_call.append(node.func.value.id)
            return None
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef | None:
        """AST visitor that deletes forbidden functions"""
        if node.name in FORBIDDEN_BUILTINS:
            self.forbidden_func_def.append(node.name)
            return None
        self.generic_visit(node)
        return node

    def visit_Try(self, node: Try) -> Try | None:
        """AST visitor that deletes forbidden try clauses"""
        self.forbidden_try_clause += 1
        self.generic_visit(node)
        return None
    
    def visit_Break(self, node: Break) -> Break | None:
        """AST visitor that deletes forbidden break statements"""
        self.forbidden_break_statement += 1
        self.score -= 1
        return None

    @staticmethod
    def _fill_report(report: Report, buffer: list, msg: str) -> None:
        report.add_malus_note(f'{msg} {", ".join(buffer)}', len(buffer))

    def fill_report(self) -> None:
        if self.forbidden_imports:
            self._fill_report(self.report, self.forbidden_imports,
                              'Forbidden imports:')
        if self.forbidden_from_imports:
            self._fill_report(self.report, self.forbidden_from_imports,
                              'Forbidden imports from:')
        if self.forbidden_func_call:
            self._fill_report(self.report, self.forbidden_func_call,
                              'Forbidden function calls:')
        if self.forbidden_method_call:
            self._fill_report(self.report, self.forbidden_method_call,
                              'Forbidden method calls:')
        if self.forbidden_func_def:
            self._fill_report(self.report, self.forbidden_func_def, 
                              'Forbidden function definitions:')
        if self.forbidden_try_clause:
            self.report.add_malus_note('Forbidden try clauses: '
                                       f'{self.forbidden_try_clause}',
                                       self.forbidden_try_clause)
        if self.forbidden_break_statement:
            self.report.add_malus_note('Forbidden break statements: '
                                       f'{self.forbidden_break_statement}',
                                       self.forbidden_break_statement)


def ast_clean(code: str, report: Report) -> tuple[str, Report]:
    """
    Function that prints the AST of the module
    """
    try:
        original_node = parse(code)
    except Exception as e:
        report.add_malus_note(f'Parse error: {e}', 1)
        return "", report
    # print(dump(original_node, indent=4))
    cleaner = ASTCleaner(report)
    cleaned_node = cleaner.visit(original_node)
    # print(dump(cleaned_node, indent=4))
    cleaner.fill_report()
    try:
        return unparse(cleaned_node), report
    except Exception as e:
        report.add_malus_note(f'Unparse error: {e}', 1)
        return "", report
