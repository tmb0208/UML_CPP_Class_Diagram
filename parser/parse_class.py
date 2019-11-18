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


def search_class(nodes, class_pattern, file_path, namespace=""):
    results = []

    for i in nodes:
        if i.kind is clang.cindex.CursorKind.NAMESPACE:
            name = i.spelling
            result = search_class(i.get_children(), class_pattern, file_path,
                                  "{}::{}".format(namespace, name) if namespace else name)
            if result:
                return result

        elif (i.kind is clang.cindex.CursorKind.CLASS_TEMPLATE or
              i.kind is clang.cindex.CursorKind.CLASS_DECL or
              i.kind is clang.cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION or
              i.kind is clang.cindex.CursorKind.STRUCT_DECL):
            # FIXME: Class definition, previosly declared in header in other class is not parsed
            class_parser = ClassNodeParser(i, namespace, file_path)
            class_full_name = class_parser.build_class_full_name()
            if class_full_name and re.search(class_pattern, class_full_name):
                results.append(class_parser.parse())

            else:
                result = search_class(i.get_children(), class_pattern, file_path,
                                      "{}::{}".format(namespace, name) if namespace else name)
                if result:
                    results = results + result

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

        return search_class(nodes, class_pattern, file_path)
    except clang.cindex.TranslationUnitLoadError as error:
        print("Error: {}".format(error))
        print("File path: {}".format(file_path))
        print("Class pattern: {}".format(class_pattern))
        print("Args: {}".format(args))
        return None
