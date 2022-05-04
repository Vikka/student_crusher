from _ast import Import, ImportFrom, Name, Call, FunctionDef, Attribute, Try, Break, Expr, Assign, \
    Continue, For, ListComp, GeneratorExp, DictComp, SetComp, Yield, YieldFrom, Raise
from ast import NodeTransformer, parse, unparse, dump

from helper.report import Report

AUTHORIZED_MODULES = set()
AUTHORIZED_BUILTINS = set()
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
                      'open', 'ord', 'pow', 'print', 'property', 'quit', 'range', 'repr',
                      'reversed', 'round', 'runfile', 'set', 'setattr', 'slice', 'sorted',
                      'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'} \
                     - AUTHORIZED_BUILTINS


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
        self.forbidden_func_calls = list()
        self.forbidden_method_calls = list()
        self.forbidden_func_definitions = list()
        self.forbidden_try_clauses = 0
        self.forbidden_break_statements = 0
        self.forbidden_continue_statements = 0
        self.forbidden_names = list()
        self.forbidden_for_loops = 0
        self.forbidden_list_comprehensions = 0
        self.forbidden_dict_comprehensions = 0
        self.forbidden_set_comprehensions = 0
        self.forbidden_generator_expressions = 0
        self.forbidden_yield_statements = 0
        self.forbidden_yield_from_statements = 0
        self.forbidden_raise_statements = 0

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
            self.forbidden_func_calls.append(node.func.id)
            return None
        if isinstance(node.func, Attribute):
            self.forbidden_method_calls.append(node.value.id)
            return None
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef | None:
        """AST visitor that deletes forbidden functions"""
        if node.name in FORBIDDEN_BUILTINS:
            self.forbidden_func_definitions.append(node.name)
            return None
        self.generic_visit(node)
        return node

    def visit_Try(self, node: Try) -> Try | None:
        """AST visitor that deletes forbidden try clauses"""
        self.forbidden_try_clauses += 1
        return None

    def visit_Break(self, node: Break) -> Break | None:
        """AST visitor that deletes forbidden break statements"""
        self.forbidden_break_statements += 1
        return None

    def visit_Continue(self, node: Continue) -> Continue | None:
        """AST visitor that deletes forbidden continue statements"""
        self.forbidden_continue_statements += 1
        return None

    def visit_Expr(self, node: Expr) -> Expr | None:
        """AST visitor that deletes forbidden expressions"""
        self.generic_visit(node)
        if not hasattr(node, 'value'):
            return None
        return node

    def visit_Name(self, node: Name) -> Name | None:
        """AST visitor that deletes forbidden names"""
        if node.id in FORBIDDEN_BUILTINS:
            self.forbidden_names.append(node.id)
            return None
        self.generic_visit(node)
        return node

    def visit_Assign(self, node: Assign) -> Assign | None:
        self.generic_visit(node)
        if not hasattr(node, 'value'):
            return None
        return node

    def visit_For(self, node: For) -> For | None:
        """AST visitor that deletes forbidden for loops"""
        self.forbidden_for_loops += 1
        return None

    def visit_ListComp(self, node: ListComp) -> ListComp | None:
        """AST visitor that deletes forbidden list comprehensions"""
        self.forbidden_list_comprehensions += 1
        return None

    def visit_DictComp(self, node: DictComp) -> DictComp | None:
        """AST visitor that deletes forbidden dict comprehensions"""
        self.forbidden_dict_comprehensions += 1
        return None

    def visit_SetComp(self, node: SetComp) -> SetComp | None:
        """AST visitor that deletes forbidden set comprehensions"""
        self.forbidden_set_comprehensions += 1
        return None

    def visit_GeneratorExp(self, node: GeneratorExp) -> GeneratorExp | None:
        """AST visitor that deletes forbidden generator expressions"""
        self.forbidden_generator_expressions += 1
        return None

    def visit_Yield(self, node: Yield) -> Yield | None:
        """AST visitor that deletes forbidden yield statements"""
        self.forbidden_yield_statements += 1
        return None

    def visit_YieldFrom(self, node: YieldFrom) -> YieldFrom | None:
        """AST visitor that deletes forbidden yield from statements"""
        self.forbidden_yield_from_statements += 1
        return None

    def visit_Raise(self, node: Raise) -> Raise | None:
        """AST visitor that deletes forbidden raise statements"""
        self.forbidden_raise_statements += 1
        return None

    @staticmethod
    def _fill_report(report: Report, buffer: list, msg: str) -> None:
        report.add_malus_note(f'{msg} {", ".join(set(buffer))}', len(buffer))

    def fill_report(self) -> None:
        if self.forbidden_imports:
            self._fill_report(self.report, self.forbidden_imports,
                              'Forbidden imports:')
        if self.forbidden_from_imports:
            self._fill_report(self.report, self.forbidden_from_imports,
                              'Forbidden imports from:')
        if self.forbidden_func_calls:
            self._fill_report(self.report, self.forbidden_func_calls,
                              'Forbidden function calls:')
        if self.forbidden_method_calls:
            self._fill_report(self.report, self.forbidden_method_calls,
                              'Forbidden method calls:')
        if self.forbidden_func_definitions:
            self._fill_report(self.report, self.forbidden_func_definitions,
                              'Forbidden function definitions:')
        if self.forbidden_try_clauses:
            self.report.add_malus_note('Forbidden try clauses: '
                                       f'{self.forbidden_try_clauses}',
                                       self.forbidden_try_clauses)
        if self.forbidden_break_statements:
            self.report.add_malus_note('Forbidden break statements: '
                                       f'{self.forbidden_break_statements}',
                                       self.forbidden_break_statements)
        if self.forbidden_continue_statements:
            self.report.add_malus_note('Forbidden continue statements: '
                                       f'{self.forbidden_continue_statements}',
                                       self.forbidden_continue_statements)
        if self.forbidden_names:
            self._fill_report(self.report, self.forbidden_names,
                              'Forbidden names:')
        if self.forbidden_for_loops:
            self.report.add_malus_note('Forbidden for loops: '
                                       f'{self.forbidden_for_loops}',
                                       self.forbidden_for_loops)
        if self.forbidden_list_comprehensions:
            self.report.add_malus_note('Forbidden list comprehensions: '
                                       f'{self.forbidden_list_comprehensions}',
                                       self.forbidden_list_comprehensions)
        if self.forbidden_dict_comprehensions:
            self.report.add_malus_note('Forbidden dict comprehensions: '
                                       f'{self.forbidden_dict_comprehensions}',
                                       self.forbidden_dict_comprehensions)
        if self.forbidden_set_comprehensions:
            self.report.add_malus_note('Forbidden set comprehensions: '
                                       f'{self.forbidden_set_comprehensions}',
                                       self.forbidden_set_comprehensions)
        if self.forbidden_generator_expressions:
            self.report.add_malus_note('Forbidden generator expressions: '
                                       f'{self.forbidden_generator_expressions}',
                                       self.forbidden_generator_expressions)
        if self.forbidden_yield_statements:
            self.report.add_malus_note('Forbidden yield statements: '
                                       f'{self.forbidden_yield_statements}',
                                       self.forbidden_yield_statements)
        if self.forbidden_yield_from_statements:
            self.report.add_malus_note('Forbidden yield from statements: '
                                       f'{self.forbidden_yield_from_statements}',
                                       self.forbidden_yield_from_statements)
        if self.forbidden_raise_statements:
            self.report.add_malus_note('Forbidden raise statements: '
                                       f'{self.forbidden_raise_statements}',
                                       self.forbidden_raise_statements)


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
    print(dump(cleaned_node, indent=4))
    cleaner.fill_report()
    try:
        return unparse(cleaned_node), report
    except Exception as e:
        report.add_malus_note(f'Unparse error: {e}', 1)
        return "", report
