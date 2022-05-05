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

        if node.func.id == 'type' and len(node.args) == 3:
            self.forbidden_func_calls.append(node.func.id)
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

    def visit_Try(self, node: Try) -> None:
        """AST visitor that deletes forbidden try clauses"""
        self.forbidden_try_clauses += 1
        return None

    def visit_Break(self, node: Break) -> None:
        """AST visitor that deletes forbidden break statements"""
        self.forbidden_break_statements += 1
        return None

    def visit_Continue(self, node: Continue) -> None:
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

    def visit_For(self, node: For) -> None:
        """AST visitor that deletes forbidden for loops"""
        self.forbidden_for_loops += 1
        return None

    def visit_ListComp(self, node: ListComp) -> None:
        """AST visitor that deletes forbidden list comprehensions"""
        self.forbidden_list_comprehensions += 1
        return None

    def visit_DictComp(self, node: DictComp) -> None:
        """AST visitor that deletes forbidden dict comprehensions"""
        self.forbidden_dict_comprehensions += 1
        return None

    def visit_SetComp(self, node: SetComp) -> None:
        """AST visitor that deletes forbidden set comprehensions"""
        self.forbidden_set_comprehensions += 1
        return None

    def visit_GeneratorExp(self, node: GeneratorExp) -> None:
        """AST visitor that deletes forbidden generator expressions"""
        self.forbidden_generator_expressions += 1
        return None

    def visit_Yield(self, node: Yield) ->None:
        """AST visitor that deletes forbidden yield statements"""
        self.forbidden_yield_statements += 1
        return None

    def visit_YieldFrom(self, node: YieldFrom) -> None:
        """AST visitor that deletes forbidden yield from statements"""
        self.forbidden_yield_from_statements += 1
        return None

    def visit_Raise(self, node: Raise) -> None:
        """AST visitor that deletes forbidden raise statements"""
        self.forbidden_raise_statements += 1
        return None

    @staticmethod
    def _fill_report(report: Report, buffer: list, msg: str) -> None:
        report.add_malus_note(f'{msg} {", ".join(set(buffer))}', len(buffer))

    def fill_report(self) -> None:
        """Fills the report with the results of the analysis"""
        buffer_analysis = [
            (self.forbidden_imports, 'Forbidden imports:'),
            (self.forbidden_from_imports, 'Forbidden imports from:'),
            (self.forbidden_func_calls, 'Forbidden function calls:'),
            (self.forbidden_method_calls, 'Forbidden method calls:'),
            (self.forbidden_func_definitions, 'Forbidden function definitions:'),
            (self.forbidden_names, 'Forbidden names:'),
            (self.forbidden_assignments, 'Forbidden assignments:'),
        ]

        for buffer, msg in buffer_analysis:
            if buffer:
                self._fill_report(self.report, buffer, msg)

        counter_analysis = [
            (self.forbidden_try_clauses,
             f'Forbidden try clauses: {self.forbidden_try_clauses}'),
            (self.forbidden_break_statements,
             f'Forbidden break statements: {self.forbidden_break_statements}'),
            (self.forbidden_continue_statements,
             f'Forbidden continue statements: {self.forbidden_continue_statements}'),
            (self.forbidden_for_loops,
             f'Forbidden for loops: {self.forbidden_for_loops}'),
            (self.forbidden_list_comprehensions,
             f'Forbidden list comprehensions: {self.forbidden_list_comprehensions}'),
            (self.forbidden_dict_comprehensions,
             f'Forbidden dict comprehensions: {self.forbidden_dict_comprehensions}'),
            (self.forbidden_set_comprehensions,
             f'Forbidden set comprehensions: {self.forbidden_set_comprehensions}'),
            (self.forbidden_generator_expressions,
             f'Forbidden generator expressions: {self.forbidden_generator_expressions}'),
            (self.forbidden_yield_statements,
             f'Forbidden yield statements: {self.forbidden_yield_statements}'),
            (self.forbidden_yield_from_statements,
             f'Forbiddenf yield from statements: {self.forbidden_yield_from_statements}'),
            (self.forbidden_raise_statements,
             f'Forbidden raise statements: {self.forbidden_raise_statements}'),
            (self.forbidden_assert_statements,
             f'Forbidden assert statements: {self.forbidden_assert_statements}'),
            (self.forbidden_while_else_clauses,
             f'Forbiddenf while else clauses: {self.forbidden_while_else_clauses}'),
            (self.forbidden_global_statements,
             f'Forbidden global statements: {self.forbidden_global_statements}'),
            (self.forbidden_nonlocal_statements,
             f'Forbidden nonlocal statements: {self.forbidden_nonlocal_statements}'),
            (self.forbidden_in_statements,
             f'Forbidden in statements: {self.forbidden_in_statements}'),
        ]
        for counter, msg in counter_analysis:
            if counter:
                self.report.add_malus_note(msg, counter)


def ast_clean(code: str, report: Report) -> tuple[AST | None, Report]:
    """
    Function that return the cleaned code and the report.
    """
    try:
        original_node = parse(code)
    except Exception as e:
        report.add_malus_note(f'Parse error: {e}', 1)
        return None, report
    print(dump(original_node, indent=4))
    cleaner = ASTCleaner(report)
    cleaned_node = cleaner.visit(original_node)
    print(dump(cleaned_node, indent=4))
    cleaner.fill_report()
    try:
        return cleaned_node, report
    except Exception as e:
        report.add_malus_note(f'Unparse error: {e}', 1)
        return None, report
