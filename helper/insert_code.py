from _ast import AST, List, Call, Name, Load
from ast import NodeTransformer, unparse, parse, dump
from pathlib import Path

from helper import report


class ASTInserter(NodeTransformer):
    """
    AST inserter that insert nodes
    """

    def visit_List(self, node: List) -> Call:
        """Rewrites all occurrences of a list with a call to the custom subclass _list."""
        self.generic_visit(node)
        return Call(
            func=Name(id='list_', ctx=Load()),
            args=[node],
            keywords=[])

    def visit_Name(self, node: Name) -> Name:
        """Rewrites all occurrences of specifics name with a custom subclass _name."""
        if node.id == 'list':
            node.id = 'list_'
        return node


def insert_features(cleaned_node):
    features_nodes = parse(Path('helper/inserts.py').read_text())
    # print(dump(features_nodes, indent=4))
    cleaned_node.body.insert(0, features_nodes.body)
    return cleaned_node


def ast_insert(cleaned_node: AST) -> str:
    """
    Function that return the code with inserted nodes
    """
    # print(dump(cleaned_node, indent=4))
    inserter = ASTInserter()
    augmented_node = inserter.visit(cleaned_node)
    final_node = insert_features(augmented_node)
    # print('=' * 80)
    # print(dump(final_node, indent=4))
    try:
        # print(unparse(final_node))
        return unparse(final_node)
    except Exception as e:
        print(e)
        return ""
