import clang.cindex
import sys
import json
import re


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


def find_parentheses(string, pos=0, opening="(", closing=")"):
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
        e = find_parentheses(declaration, m.end() - 1, "<", ">") + 1
        if e:
            return declaration[s:e]

    return None


def match_virtual(method_declaration):
    if method_declaration.find("virtual") != -1:
        return "virtual"

    return None


def match_static(method_declaration):
    if method_declaration.find("static") != -1:
        return "static"

    return None


def match_method_parameters(method_declaration, method_name):
    match = re.search(r"{}\s*\(".format(method_name), method_declaration)
    if not match:
        raise ValueError("Could not match method name '{}': {}". format(
            method_name, method_declaration))
        return None

    s = match.start() + len(method_name) + 1
    e = find_parentheses(method_declaration, match.end() - 1, "(", ")")
    if not e:
        raise IndexError("No matching closing parentheses")
        return None

    return method_declaration[s:e]


def match_method_type(method_declaration, method_name):
    template = match_template(method_declaration)
    if template:
        result = method_declaration.replace(template, "")

    virtual = match_virtual(method_declaration)
    if virtual:
        result = method_declaration.replace(virtual, "")

    match = re.search(r"{}\s*\(".format(method_name), result)
    if not match:
        raise ValueError("Could not match method name '{}': {}". format(
            method_name, method_declaration))
        return None

    result = result[:match.start()]
    result.strip()
    return result


def match_method_qualifiers(method_declaration, method_name):
    parameters = match_method_parameters(method_declaration, method_name)
    result = method_declaration.replace(parameters, "")

    match = re.search(r"{}\s*\(\)".format(method_name), result)
    if not match:
        raise ValueError("Could not match method name '{}': {}". format(
            method_name, method_declaration))
        return None

    result = result[match.end():]
    result = result.strip()
    result = result.rstrip(";")
    return result


def parse_nodes(nodes, file_path):
    result = []

    for i in nodes:
        if i.kind.is_declaration:
            name = i.displayname
            nodes = []

            if i.kind is clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
                name = i.access_specifier.name
            elif i.kind is clang.cindex.CursorKind.CXX_METHOD:
                method_declaration = read_extent(sys.argv[1], i.extent)

            else:
                nodes = parse_nodes(i.get_children(), file_path)

            result.append({"kind": "{}".format(i.kind), "name": name, "nodes": nodes})

    return result


def parse_file_nodes(file_path, args):
    index = clang.cindex.Index.create()
    translation_unit = index.parse(file_path, args=args)
    nodes = filter_node_list_by_file(
        translation_unit.cursor.get_children(), translation_unit.spelling)

    return parse_nodes(nodes, file_path)


all_classes = parse_file_nodes(sys.argv[1], ['-std=c++11'])
print json.dumps(all_classes)
