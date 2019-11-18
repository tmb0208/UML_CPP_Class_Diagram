#!/usr/bin/python
from extent import Extent
from class_parser import ClassParser
import clang.cindex
import re
import os
import sys
from enum import Enum


def filter_nodes_by_file_name(nodes, file_name):
    result = []
    for node in nodes:
        if node.location.file.name == file_name:
            result.append(node)

    return result


def filter_method_parameters(method_nodes):
    results = []
    for node in method_nodes:
        if node.kind is clang.cindex.CursorKind.PARM_DECL:
            results.append(node)

    return results


# WORKAROUND Template Construct/Destructor
def match_method_name(spelling):
    match = re.search(r"^~?[a-zA-Z_][a-zA-Z0-9_]*", spelling)
    if not match:
        raise ValueError("Error: Could not match method name in spelling '{}'". format(spelling))

    return match.group(0)


def parse_method_parameter_node(parameters_node, file_path):
    name = parameters_node.spelling
    declaration = Extent.from_cindex_extent(parameters_node.extent).read_from_file(file_path)
    return ClassParser.parse_property_node(name, declaration)


def parse_method_parameters_nodes(parameters_nodes, file_path):
    results = []
    for node in parameters_nodes:
        results.append(parse_method_parameter_node(node, file_path))

    return results


def parse_method_node(node, access_specifier, file_path):
    name = node.spelling
    if "<" in name:
        name = match_method_name(name)

    declaration = Extent.from_cindex_extent(node.extent).read_from_file(file_path)
    parameters_nodes = filter_method_parameters(node.get_children())
    parameters = parse_method_parameters_nodes(parameters_nodes, file_path)

    is_constructor = node.kind is clang.cindex.CursorKind.CONSTRUCTOR
    is_destructor = node.kind is clang.cindex.CursorKind.DESTRUCTOR

    return ClassParser.parse_method_node(
        name, declaration, parameters, access_specifier, is_constructor, is_destructor)


def parse_field_node(node, access_specifier, file_path):
    name = node.spelling
    declaration = Extent.from_cindex_extent(node.extent).read_from_file(file_path)
    return ClassParser.parse_property_node(name, declaration, access_specifier)


def parse_class_methods_and_fields_nodes(nodes, file_path, is_struct):
    class AccessSpecifier(Enum):
        PRIVATE = 0
        PROTECTED = 1
        PUBLIC = 2

    methods = []
    fields = []
    access_specifier = AccessSpecifier.PUBLIC if is_struct else AccessSpecifier.PRIVATE
    for node in nodes:
        if node.kind is clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
            access_specifier = next(
                (s for s in AccessSpecifier if s.name == node.access_specifier.name), None)

        elif node.kind in [clang.cindex.CursorKind.CXX_METHOD,
                           clang.cindex.CursorKind.FUNCTION_TEMPLATE,
                           clang.cindex.CursorKind.DESTRUCTOR,
                           clang.cindex.CursorKind.CONSTRUCTOR]:
            methods.append(parse_method_node(node, access_specifier, file_path))

        elif node.kind is clang.cindex.CursorKind.FIELD_DECL:
            fields.append(parse_field_node(node, access_specifier, file_path))

    return methods, fields


def parse_class_node(node, namespace, file_path):
    result = {}

    result["namespace"] = namespace

    name = node.spelling
    result["name"] = name

    declaration = Extent.from_cindex_extent(node.extent).read_from_file(file_path)
    full_name = match_full_class_name(declaration)
    if full_name and namespace:
        full_name = add_namespace_before_class_name(full_name, name, namespace)
    result["full_name"] = full_name

    is_struct = node.kind is clang.cindex.CursorKind.STRUCT_DECL
    methods, fields = parse_class_methods_and_fields_nodes(
        node.get_children(), file_path, is_struct)
    result["methods"] = methods
    result["fields"] = fields

    return result


def match_full_class_name(class_declaration):
    match = re.search(
        r"(class|struct)[^{]*[a-z_][a-z_0-9]*(::[a-z_][a-z_0-9]*)?\s*(<[^{]*>)?\s*{",
        class_declaration)
    if not match:
        return None

    return class_declaration[:match.end() - 1].strip()


def add_namespace_before_class_name(full_class_name, class_name, namespace):
    class_name_match = re.search(r"\s*{}\s*".format(class_name), full_class_name)
    if not class_name_match:
        raise ValueError("Could not match class name '{}' in full class name '{}'". format(
            class_name, full_class_name))
        return None

    return "{}{}::{}".format(full_class_name[:class_name_match.start() + 1],
                             namespace,
                             full_class_name[class_name_match.start() + 1:])


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
            name = i.spelling

            extent = Extent.from_cindex_extent(i.extent)
            declaration = extent.read_from_file(file_path)
            full_name = match_full_class_name(declaration)
            if full_name and namespace:
                full_name = add_namespace_before_class_name(full_name, name, namespace)

            # FIXME: Class definition, previosly declared in header in other class is not parsed

            if full_name and re.search(class_pattern, full_name):
                results.append(parse_class_node(i, namespace, file_path))
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
