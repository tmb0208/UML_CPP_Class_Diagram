#!/usr/bin/python
from string_with_brackets import StringWithBrackets
from extent import Extent
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


def match_template(declaration):
    m = re.search(r"template\s*<", declaration)
    if m:
        s = m.start()
        e = StringWithBrackets(declaration).find_any_of_brackets([">"], 1, m.end() - 1) + 1
        if e != -1:
            return declaration[s:e]

    return None


# TODO should be removed
def match_method_parameters(method_declaration, method_name):
    match = re.search(r"{}\s*\(".format(method_name), method_declaration)
    if not match:
        raise ValueError("Error: Could not match method name '{}' in method declaration '{}'".format(
            method_name, method_declaration))
        return None

    s = match.start() + len(method_name) + 1
    e = StringWithBrackets(method_declaration).find_any_of_brackets([")"], 1, match.end() - 1)
    if e == -1:
        raise IndexError("Error: No matching closing parentheses")
        return None

    if s == e:
        return None

    result = method_declaration[s:e]
    result = result.strip()
    return result


def match_method_type(method_declaration, method_name):
    result = method_declaration
    template = match_template(method_declaration)
    if template:
        result = method_declaration.replace(template, "")

    match = re.search(r"{}\s*\(".format(method_name), result)
    if not match:
        raise ValueError("Error: Could not match method name '{}' in method declaration '{}'". format(
            method_name, method_declaration))
        return None

    result = result[:match.start()]
    result = result.strip()
    return result


def match_method_qualifiers(method_declaration, method_name):
    result = method_declaration

    parameters = match_method_parameters(method_declaration, method_name)
    if parameters:
        result = result.replace(parameters, "")

    match = re.search(r"{}\s*\(\s*\)".format(method_name), result)
    if not match:
        raise ValueError("Error: Could not match method name '{}' in method declaration '{}'". format(
            method_name, method_declaration))
        return None

    result = result[match.end():]
    result = result.strip()
    result = result.rstrip(";")
    return result


def build_property_node(name, declaration):
    result = {}

    result["name"] = name
    result["declaration"] = declaration
    if name:
        name_match = re.search(r"\s*{}\s*(=|{}|$)".format(name, "{"), declaration)

        if not name_match:
            raise ValueError(
                "Error: Could not match property name '{}' in declaration '{}'". format(
                    name, declaration))

        # TODO: Parse default
        # default = None
        # if name_match:
        #     if len(declaration) != name_match.end():
        #         default = declaration[name_match.end():].strip()
        # result["default"] = default

        type = declaration[:name_match.start()].strip()
    else:
        type = declaration
    result["type"] = type

    qualifiers = []
    if re.search(r"(^|\s+)static(\s+|$)", type):
        qualifiers.append("static")

    if re.search(r"(^|\s+)const(\s+|$)", type):
        qualifiers.append("const")

    if re.search(r"(^|\s+)mutable(\s+|$)", type):
        qualifiers.append("mutable")
    result["qualifiers"] = qualifiers

    return result


def parse_method_parameters(name, method_nodes, file_path):
    results = []

    for i in method_nodes:
        if i.kind is clang.cindex.CursorKind.PARM_DECL:
            name = i.spelling
            extent = Extent.from_cindex_extent(i.extent)
            declaration = extent.read(file_path)

            result = build_property_node(name, declaration)
            results.append(result)

    return results


# WORKAROUND Template Construct/Destructor
def remove_template(spelling):
    match = re.search(r"^~?[a-zA-Z_][a-zA-Z0-9_]*", spelling)
    if not match:
        raise ValueError("Error: Could not match method name in spelling '{}'". format(spelling))

    return match.group(0)


# WORKAROUND operator method
def extract_operator_name(spelling, declaration):
    match_operator = re.search(r"operator\s*(?!\.|::|\?:|sizeof)", spelling)
    if match_operator:
        return spelling

    return None


def parse_method(method_node, file_path):
    result = {}

    name = method_node.spelling
    if "<" in name:
        name = remove_template(name)

    result["name"] = name

    extent = Extent.from_cindex_extent(method_node.extent)
    declaration = extent.read(file_path)
    result["declaration"] = declaration

    type = match_method_type(declaration, name)
    result["type"] = type

    result["parameters"] = parse_method_parameters(name, method_node.get_children(), file_path)

    qualifiers = []

    template = match_template(declaration)
    if template:
        qualifiers.append("template")

    if method_node.kind is clang.cindex.CursorKind.CONSTRUCTOR:
        qualifiers.append("constructor")

    elif method_node.kind is clang.cindex.CursorKind.DESTRUCTOR:
        qualifiers.append("destructor")

    if re.search(r"(^|\s+)virtual(\s+|$)", type):
        qualifiers.append("virtual")

    if re.search(r"(^|\s+)static(\s+|$)", type):
        qualifiers.append("static")

    if re.search(r"(^|\s+)explicit(\s+|$)", type):
        qualifiers.append("explicit")

    qualifiers_string = match_method_qualifiers(declaration, name)
    if re.search(r"(^|\s+)override(\s+|$)", qualifiers_string):
        qualifiers.append("override")

    if re.search(r"(^|\s+)const(\s+|$)", qualifiers_string):
        qualifiers.append("const")

    if re.search(r"(^|\s+)=\s*0(\s+|$)", qualifiers_string):
        qualifiers.append("pure")

    if re.search(r"(^|\s+)=\s*delete(\s+|$)", qualifiers_string):
        qualifiers.append("deleted")

    if re.search(r"(^|\s+)=\s*default(\s+|$)", qualifiers_string):
        qualifiers.append("default")

    result["qualifiers"] = qualifiers

    return result


def parse_class_methods_and_fields(class_nodes, file_path, is_struct):
    class AccessSpecifier(Enum):
        PRIVATE = 0
        PROTECTED = 1
        PUBLIC = 2

    methods = []
    fields = []
    access_specifier = AccessSpecifier.PUBLIC if is_struct else AccessSpecifier.PRIVATE
    for i in class_nodes:
        if i.kind is clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
            name = i.access_specifier.name
            access_specifier = next((s for s in AccessSpecifier if s.name == name), None)

        elif (i.kind is clang.cindex.CursorKind.CXX_METHOD or
              i.kind is clang.cindex.CursorKind.FUNCTION_TEMPLATE or
              i.kind is clang.cindex.CursorKind.DESTRUCTOR or
              i.kind is clang.cindex.CursorKind.CONSTRUCTOR):
            method = parse_method(i, file_path)
            method["access_specifier"] = access_specifier.name

            methods.append(method)

        elif i.kind is clang.cindex.CursorKind.FIELD_DECL:
            name = i.spelling
            extent = Extent.from_cindex_extent(i.extent)
            declaration = extent.read(file_path)
            field = build_property_node(name, declaration)
            field["access_specifier"] = access_specifier.name
            fields.append(field)

    return methods, fields


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
            declaration = extent.read(file_path)
            full_name = match_full_class_name(declaration)
            if full_name and namespace:
                full_name = add_namespace_before_class_name(full_name, name, namespace)

            # FIXME: Class definition, previosly declared in header in other class is not parsed

            if full_name and re.search(class_pattern, full_name):
                is_struct = i.kind is clang.cindex.CursorKind.STRUCT_DECL
                methods, fields = parse_class_methods_and_fields(
                    i.get_children(), file_path, is_struct)
                results.append({"name": name,
                                "full_name": full_name,
                                "namespace": namespace,
                                "methods": methods,
                                "fields": fields})
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
