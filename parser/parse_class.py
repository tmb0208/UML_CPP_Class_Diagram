#!/usr/bin/python
from class_node_parser import ClassNodeParser
import clang.cindex
import re
import os


def filter_nodes_by_file_name(nodes, file_name):
    result = []
    for node in nodes:
        if node.location.file.name == file_name:
            result.append(node)

    return result


def is_class(node_kind):
    return node_kind in [clang.cindex.CursorKind.CLASS_TEMPLATE,
                         clang.cindex.CursorKind.CLASS_DECL,
                         clang.cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
                         clang.cindex.CursorKind.STRUCT_DECL]


def findall_class_nodes(nodes, parent_nodes=None):
    results = []

    if parent_nodes is None:
        parent_nodes = []

    for node in nodes:
        if node.kind is clang.cindex.CursorKind.NAMESPACE or is_class(node.kind):
            if is_class(node.kind):
                results.append({"parent_nodes": parent_nodes, "class_node": node})

            class_nodes = findall_class_nodes(node.get_children(), parent_nodes + [node])
            if class_nodes:
                results = results + class_nodes

    return results


def parse_if_match_pattern(class_node, parent_nodes, pattern, file_path):
    # FIXME: Class definition, previosly declared in header in other class is not parsed
    parser = ClassNodeParser(class_node, parent_nodes, file_path)
    full_name = parser.build_class_full_name()
    if full_name is None:
        raise ValueError("Couldn't build full name. Class name: {}".format(class_node.spelling))
        return None

    if re.search(pattern, full_name):
        return parser.parse()

    return None


def parse_matching_class_nodes(file_nodes, pattern, file_path):
    results = []

    class_nodes = findall_class_nodes(file_nodes)
    for node in class_nodes:
        result = parse_if_match_pattern(
            node["class_node"], node["parent_nodes"], pattern, file_path)
        if result:
            results.append(result)

    return results


def search_class_in_file(file_path, class_pattern, args):
    index = clang.cindex.Index.create()

    file_ext = os.path.splitext(file_path)[1]
    if file_ext in [".cpp"]:
        if not args:
            args = []
        args.append("-xc++")

    try:
        translation_unit = index.parse(
            file_path, args=args, options=clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)
        nodes = filter_nodes_by_file_name(
            translation_unit.cursor.get_children(), translation_unit.spelling)

        return parse_matching_class_nodes(nodes, class_pattern, file_path)
    except clang.cindex.TranslationUnitLoadError as error:
        print("Error: {}".format(error))
        print("File path: {}".format(file_path))
        print("Class pattern: {}".format(class_pattern))
        print("Args: {}".format(args))
        return None
