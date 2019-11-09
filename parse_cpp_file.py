import clang.cindex
import sys
import json
import re
from enum import Enum


def filter_node_list_by_file(nodes, file_name):
    result = []

    for i in nodes:
        if i.location.file.name == file_name:
            result.append(i)

    return result


def read_extent(file_path, extent):
    with open(file_path) as f:
        content = f.readlines()

    # adjust
    sl = extent.start.line - 1
    sc = extent.start.column - 1
    el = extent.end.line - 1
    ec = extent.end.column - 1

    result = ""
    for i in range(sl, el + 1):
        result += content[i]

    end_line = content[el]
    strip_right = len(end_line) - ec
    strip_left = sc

    result = result[strip_left:-strip_right]
    result = result.replace("\n", " ").replace("\r", " ")
    result = ' '.join(result.split())
    return result


def find_corresponding_closing_parenthese(string, pos=0, opening="(", closing=")"):
    stack = 0

    for i, c in enumerate(string[pos:]):
        if c == opening:
            stack += 1
        elif c == closing:
            stack -= 1
            if stack < 0:
                raise IndexError("No matching opening parentheses")
                return None

            if stack == 0:
                return pos + i

    raise IndexError("No matching closing parentheses")
    return None


def match_template(declaration):
    m = re.search(r"template\s*<", declaration)
    if m:
        s = m.start()
        e = find_corresponding_closing_parenthese(declaration, m.end() - 1, "<", ">") + 1
        if e:
            return declaration[s:e]

    return None


def match_method_parameters(method_declaration, method_name):
    match = re.search(r"{}\s*\(".format(method_name), method_declaration)
    if not match:
        raise ValueError("Could not match method name '{}': {}". format(
            method_name, method_declaration))
        return None

    s = match.start() + len(method_name) + 1
    e = find_corresponding_closing_parenthese(method_declaration, match.end() - 1, "(", ")")
    if not e:
        raise IndexError("No matching closing parentheses")
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
        raise ValueError("Could not match method name '{}': {}". format(
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
        raise ValueError("Could not match method name '{}': {}". format(
            method_name, method_declaration))
        return None

    result = result[match.end():]
    result = result.strip()
    result = result.rstrip(";")
    return result


def split_method_parameters(parameters):
    results = []

    mask = parameters
    brackets = {"(": ")", "<": ">", "[": "]"}
    for b in brackets:
        while True:
            s = mask.find(b)
            if s == -1:
                break

            e = find_corresponding_closing_parenthese(mask, s, b, brackets[b])
            mask = mask[:s] + ("#" * (e + 1 - s)) + mask[e + 1:]

    start_pos = 0
    while True:
        comma_pos = mask.find(",", start_pos)
        if comma_pos == -1:
            break

        result = parameters[start_pos:comma_pos]
        result = result.strip()
        results.append(result)

        start_pos = comma_pos + 1

    results.append(parameters[start_pos:])

    return results


def build_propery_node(declaration, name=None):
    name_match = re.search(
        r"\s*{}\s*(=|$)".format(name if name else r"[a-zA-Z_][a-zA-Z0-9_]*"), declaration)
    if not name_match:
        raise ValueError("Could not match declaration name: {}". format(declaration))

    if not name:
        name = declaration[name_match.start():name_match.end() - 1].strip()

    default = ""
    if len(declaration) != name_match.end():
        default = declaration[name_match.end():].strip()

    type = declaration[:name_match.start()].strip()

    qualifiers = []
    if re.search(r"(^|\s+)static(\s+|$)", type):
        qualifiers.append("static")

    if re.search(r"(^|\s+)mutable(\s+|$)", type):
        qualifiers.append("mutable")

    return {"declaration": declaration,
            "name": name,
            "default": default,
            "type": type,
            "qualifiers": qualifiers}


def build_method_parameters_node(parameters):
    results = []
    if not parameters:
        return results

    parameters = split_method_parameters(parameters)
    for parameter in parameters:
        results.append(build_propery_node(parameter))

    return results


def build_method_node(method_declaration, method_name):
    results = {}
    results["name"] = method_name
    results["declaration"] = method_declaration

    template = match_template(method_declaration)

    type = match_method_type(method_declaration, method_name)
    results["type"] = type

    parameters = match_method_parameters(method_declaration, method_name)
    results["parameters"] = build_method_parameters_node(parameters)

    qualifiers = []

    if template:
        qualifiers.append("template")

    if re.search(r"(^|\s+)virtual(\s+|$)", type):
        qualifiers.append("virtual")

    if re.search(r"(^|\s+)static(\s+|$)", type):
        qualifiers.append("static")

    if re.search(r"(^|\s+)explicit(\s+|$)", type):
        qualifiers.append("explicit")

    qualifiers_string = match_method_qualifiers(method_declaration, method_name)
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

    results["qualifiers"] = qualifiers

    return results


def parse_class_methods_and_fields(class_nodes, file_path):
    class AccessSpecifier(Enum):
        PRIVATE = 0
        PROTECTED = 1
        PUBLIC = 2

    methods = []
    fields = []
    access_specifier = AccessSpecifier.PRIVATE
    for i in class_nodes:
        if i.kind is clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
            name = i.access_specifier.name
            access_specifier = next((s for s in AccessSpecifier if s.name == name), None)

        elif (i.kind is clang.cindex.CursorKind.CXX_METHOD or
              i.kind is clang.cindex.CursorKind.FUNCTION_TEMPLATE or
              i.kind is clang.cindex.CursorKind.DESTRUCTOR or
              i.kind is clang.cindex.CursorKind.CONSTRUCTOR):
            name = i.spelling
            declaration = read_extent(file_path, i.extent)
            method = build_method_node(declaration, name)

            method["access_specifier"] = access_specifier.name
            if i.kind is clang.cindex.CursorKind.CONSTRUCTOR:
                method["qualifiers"].append("constructor")
            elif i.kind is clang.cindex.CursorKind.DESTRUCTOR:
                method["qualifiers"].append("destructor")

            methods.append(method)

        elif i.kind is clang.cindex.CursorKind.FIELD_DECL:
            name = i.spelling
            declaration = read_extent(file_path, i.extent)
            field = build_propery_node(declaration, name)
            field["access_specifier"] = access_specifier.name
            fields.append(field)

    return methods, fields


def match_full_class_name(class_declaration):
    match = re.search(r"class[^{]*[a-z_][a-z_0-9]*\s*(<[^{]*>)?\s*{", class_declaration)
    if not match:
        return None

    return class_declaration[:match.end() - 1].strip()


def add_namespace_before_class_name(full_class_name, class_name, namespace):
    class_name_match = re.search(r"\s*{}\s*".format(class_name), full_class_name)
    if not class_name_match:
        raise ValueError("Could not match class name '{}' in full class name '{}'". format(
            class_name, full_class_name))

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
              i.kind is clang.cindex.CursorKind.CLASS_DECL):
            name = i.spelling

            declaration = read_extent(file_path, i.extent)
            full_name = match_full_class_name(declaration)
            if full_name and namespace:
                full_name = add_namespace_before_class_name(full_name, name, namespace)

            if full_name and re.search(class_pattern, full_name):
                methods, fields = parse_class_methods_and_fields(i.get_children(), file_path)
                results.append({"name": name,
                                "full_name": full_name,
                                "namespace": namespace,
                                "methods": methods,
                                "fields": fields})

    return results


def search_class_in_file(file_path, class_pattern, args):
    index = clang.cindex.Index.create()
    translation_unit = index.parse(file_path, args=args)
    nodes = filter_node_list_by_file(
        translation_unit.cursor.get_children(), translation_unit.spelling)

    return search_class(nodes, class_pattern, file_path)
