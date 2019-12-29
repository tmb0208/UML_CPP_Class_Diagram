#!/usr/bin/python
import re
import os
import shlex
from parser.class_parser import ClassParser
from arguments_parser import ArgumentsParser


def replace_html_specific_characters(string):
    return string.replace("&", "&#38;").replace("<", "&#60;").replace(">", "&#62;")


def replace_multiple(string, old_arr, new):
    for old in old_arr:
        string = string.replace(old, new)

    return string


def build_uml_properties_representation(properties, access_modificator_representations):
    results = []

    for property in properties:
        specifier = property["access_specifier"]
        specifier_representation = access_modificator_representations[specifier]

        result = "{} {} : {}".format(specifier_representation, property["name"], property["type"])
        results.append(result)

    return results


def build_uml_method_parameters_representation(method):
    results = []

    representation = "{} : {}"

    for parameter in method["parameters"]:
        results.append(
            representation.format(parameter["name"], parameter["type"]))

    return ', '.join(results)


def build_uml_method_return_type_representation(method):
    if "constructor" in method["qualifiers"] or "destructor" in method["qualifiers"]:
        return ""

    return method["type"]


def build_uml_method_specificators_representation(method):
    if "pure" in method["qualifiers"] or "virtual" in method["qualifiers"]:
        return "= 0"
    elif "virtual" in method["qualifiers"]:
        return "[virtual]"
    elif "override" in method["qualifiers"]:
        return "[override]"
    else:
        return ""


def build_uml_methods_representation(methods, access_modificator_representations):
    results = []

    representation = "{} {}( {} ) : {} {}"

    for method in methods:
        specifier = method["access_specifier"]
        specifier_representation = access_modificator_representations[specifier]
        result = representation.format(specifier_representation,
                                       method["name"],
                                       build_uml_method_parameters_representation(method),
                                       build_uml_method_return_type_representation(method),
                                       build_uml_method_specificators_representation(method))

        result = result.rstrip(": ")
        results.append(result)

    return results


def underline_if_static(uml_representation):
    if re.search(r":.* static .*", uml_representation):
        return "<u>{}</u>".format(uml_representation)

    return uml_representation


def italic_if_pure_virtual(uml_representation):
    if re.search(r":.*= 0.*", uml_representation):
        return "<i>{}</i>".format(uml_representation)

    return uml_representation


def format_if_too_long(uml_method_representation, max_chars, spacing=8):
    sep = "<br />" + (" " * spacing)

    if len(uml_method_representation) > max_chars:
        return uml_method_representation.replace("( ", "(" + sep).replace(", ", "," + sep)

    return uml_method_representation


def format_uml_properties_to_html(properties):
    results = []

    for p in properties:
        result = replace_html_specific_characters(p)
        result = underline_if_static(result)
        results.append(result)

    return results


def format_uml_methods_to_html(methods):
    results = []

    for m in methods:
        result = replace_html_specific_characters(m)
        result = underline_if_static(result)
        result = italic_if_pure_virtual(result)
        result = format_if_too_long(result, 100)
        results.append(result)

    return results


def format_uml_class_to_html(full_name, uml_properties, uml_methods):
    template = ('<<table border="0" cellspacing="0" cellborder="1">\n'
                '\t<tr>\n'
                '\t\t<td>{}</td>\n'
                '\t</tr>\n'
                '\t<tr>\n'
                '\t\t<td ALIGN="left" BALIGN="left">{}</td>\n'
                '\t</tr>\n'
                '\t<tr>\n'
                '\t\t<td ALIGN="left" BALIGN="left">{}</td>\n'
                '\t</tr>\n'
                '</table>>\n')

    full_name = replace_html_specific_characters(full_name)
    properties = format_uml_properties_to_html(uml_properties)
    methods = format_uml_methods_to_html(uml_methods)

    return template.format(full_name, '<br />'.join(properties), '<br />'.join(methods))


def build_dot_node(full_class_name, label):
    template = "\"{}\" [\n\tlabel = \n{}];"

    return template.format(full_class_name, label)


def build_properties_and_methods_uml_representation(properties, methods):
    access_modificator_representations = {"PRIVATE": "-", "PROTECTED": "#", "PUBLIC": "+"}

    properties_representation = build_uml_properties_representation(
        properties, access_modificator_representations)
    methods_representation = build_uml_methods_representation(
        methods, access_modificator_representations)

    return properties_representation, methods_representation


def build_uml_class_diagram_node(full_class_name, properties, methods):
    uml_properties, uml_methods = build_properties_and_methods_uml_representation(
        properties, methods)
    class_content = format_uml_class_to_html(full_class_name, uml_properties, uml_methods)

    return build_dot_node(full_class_name, class_content)


def build_edge_attributes(rtype, taillabel=None, label=None, headlabel=None, labeldistance=None):
    relationships = {
        "association":
            '[style="solid", taillabel="{}", label="{}", headlabel="{}", '
            'arrowhead="vee", labeldistance="{}"]; // association',
        "dependency":
            '[style="dashed", taillabel="{}", label="{}", headlabel="{}", '
        'arrowhead="vee", labeldistance="{}"]; // dependency',
        "aggregation":
            '[style="solid", dir="both", taillabel="{}", arrowtail="odiamond", '
            'label="{}", headlabel="{}", arrowhead="vee", labeldistance="{}"]; // aggregation',
        "composition":
            '[style="solid", dir="both", taillabel="{}", arrowtail="diamond", '
            'label="{}", headlabel="{}", arrowhead="vee", labeldistance="{}"]; // composition',
        "inheritance":
            '[style="solid", arrowhead="onormal"]; // inheritance',
        "realization":
            '[style="dashed", arrowhead="onormal"]; // realization'
    }

    if not rtype in relationships:
        return None

    taillabel = taillabel if taillabel else ""
    label = label if label else ""
    headlabel = headlabel if headlabel else ""
    labeldistance = labeldistance if labeldistance else ""

    return relationships[rtype].format(taillabel, label, headlabel, labeldistance)


def build_relationship(depender, dependee, rtype,
                       taillabel=None, label=None, headlabel=None, labeldistance=None):
    edge_attributes = build_edge_attributes(rtype, taillabel, label, headlabel, labeldistance)

    return "\"{}\" -> \"{}\" {}".format(depender, dependee, edge_attributes)


def parse_classes(args_list):
    result = []

    for args in args_list:
        if args.file_path:
            c = ClassParser(args.file_path, args.class_pattern, args.clang_arguments).parse()
            if c:
                result.append(c)

    return result


def build_classes_nodes(classes):
    result = []

    for c in classes:
        node = build_uml_class_diagram_node(c["full_name"], c["fields"], c["methods"])
        result.append(node)

    return result


def match_class_full_name(classes, pattern):
    results = []
    full_names = []
    for c in classes:
        full_names.append(c["full_name"])
        if re.search(pattern, c["full_name"]):
            results.append(c["full_name"])

    if not results:
        raise ValueError(
            "Error: No class full name matching pattern '{}': {}".format(pattern, full_names))
        return None
    elif len(results) > 1:
        raise ValueError("Error: Several classes full name are matching pattern '{}': {}".format(
            pattern, results))
        return None

    return results[0]


def build_relationships(args_list, classes):
    results = []

    for args in args_list:
        if args.relationship_type:
            if not args.relationship_depender:
                args.relationship_depender = args.class_pattern

            try:
                depender_full_name = match_class_full_name(classes, args.relationship_depender)
                dependee_full_name = match_class_full_name(classes, args.relationship_dependee)
            except ValueError as error:
                print(error)
                raise ValueError("Could not build relationships with args '{}'.".format(args))
                return None

            relationship = build_relationship(depender_full_name,
                                              dependee_full_name,
                                              args.relationship_type,
                                              args.relationship_taillabel,
                                              args.relationship_label,
                                              args.relationship_headlabel,
                                              args.relationship_labeldistance)
            results.append(relationship)

    return results


def parse_arguments_file(file_path):
    if not file_path:
        return None

    result = []
    if not os.path.isfile(file_path):
        raise ValueError("Error: No such file: '{}'".format(file_path))

    with open(file_path) as f:
        lines = f.readlines()

    for n, line in enumerate(lines):
        line_args = shlex.split(line)
        line_args = ArgumentsParser.parse(line_args)
        if not line_args:
            raise ValueError("Error: Could not parse arguments from file '{}' line {}:'{}'".format(
                file_path, n, line))
            return None

        result.append(line_args)

    return result


def build_graph(nodes, relationships):
    template = ('digraph "Class Diagram"\n'
                '{{\n'
                '\tbgcolor = transparent;\n'
                '\trankdir = LR;\n'
                '\tedge [fontname = Helvetica, fontsize = 10, labelfontname = Helvetica, '
                'labelfontsize = 10];\n'
                '\tnode [fontname = Helvetica, fontsize = 10, shape = none, margin = 0, '
                'style = filled, fillcolor = grey75, fontcolor = black ];\n'
                '\n'
                '{}\n'
                '\n'
                '{}\n'
                '}}')

    return template.format("\n".join(nodes), "\n".join(relationships))


def main():
    args = ArgumentsParser.parse()
    if not args:
        print "Error: Argument parser error"
        return 1

    args_list = parse_arguments_file(args.argument_list_file)
    if not args_list:
        args_list = []
        args_list.append(args)

    try:
        classes = parse_classes(args_list)
        nodes = build_classes_nodes(classes)

        relationships = build_relationships(args_list, classes)

        graph = build_graph(nodes, relationships)
        print graph
        return 0
    except ValueError as error:
        print(error)

    return 1


if __name__ == "__main__":
    exit(main())
