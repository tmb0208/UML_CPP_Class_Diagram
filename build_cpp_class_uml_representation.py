#!/usr/bin/python
import json
import re
import argparse
import os
from parse_cpp_file import search_class_in_file


def get_uml_class_diagram_relationships():
    return ["association", "dependency", "aggregation", "composition", "inheritance", "realization"]


def parse_args(args=None):
    default_relationship_labeldistance_value = 2

    parser = argparse.ArgumentParser(
        description='Builds uml class diagram from header file and/or relationship between '
                    'classes which are represented in graphviz dot language. '
                    'Elther FILE_PATH or RELATIONSHIP_TYPE or ARGUMENT_LIST_FILE is required. '
                    'C++ files parsing is based on clang library')

    parser.add_argument('-f', '--file-path', type=str,
                        help='Path to file which contains class definition.')
    parser.add_argument('-c', '--class-name', type=str,
                        help='Name of class to extract (Use "::" for nested classes). '
                             'By default basename of FILE_PATH would be set')
    parser.add_argument('-alf', '--argument-list-file', type=str,
                        help='Path to file where every line is argument to this executable.')
    parser.add_argument('-a', '--clang-arguments', type=str,
                        help='Arguments passed to clang before parsing')

    parser.add_argument('-t', '--relationship-type', type=str,
                        choices=get_uml_class_diagram_relationships(),
                        help='Sets type of relationship. '
                             'If it does not set relationship representation would not be build. '
                             'If it is set RELATIONSHIP_DEPENDEE should be set. '
                             'If FILE_PATH is not set then RELATIONSHIP_DEPENDER should be set.')
    parser.add_argument('-dr', '--relationship-depender', type=str,
                        help='Sets relationship depender name. '
                             'By default CLASS_NAME would be set')
    parser.add_argument('-de', '--relationship-dependee', type=str,
                        help='Sets relationship dependee name')
    parser.add_argument('-tl', '--relationship-taillabel', type=str,
                        help='Sets relationship tail label')
    parser.add_argument('-l', '--relationship-label', type=str,
                        help='Sets relationship label')
    parser.add_argument('-hl', '--relationship-headlabel', type=str,
                        help='Sets relationship head label')
    parser.add_argument('-ld', '--relationship-labeldistance', type=int,
                        help='Sets relationship label distance .'
                             'By default = "{}")'.format(
                                 default_relationship_labeldistance_value))

    args = parser.parse_args(args)

    # Check error
    err = None
    if not args.file_path and not args.relationship_type and not args.argument_list_file:
        err = "Error: Neither FILE_PATH nor RELATIONSHIP_TYPE nor FILE_LIST is set"
    elif args.relationship_type and not args.relationship_dependee:
        err = "Error: RELATIONSHIP_TYPE is set, but RELATIONSHIP_DEPENDEE is not"
    elif args.relationship_type and not args.file_path and not args.relationship_depender:
        err = "Error: RELATIONSHIP_TYPE is set, but Neither FILE_PATH nor RELATIONSHIP_DEPENDER is"

    if err:
        parser.print_help()
        print err
        return None

    # Set defaults
    if not args.class_name and args.file_path:
        file = os.path.split(args.file_path)[1]
        args.class_name = os.path.splitext(file)[0]

    if not args.relationship_labeldistance:
        args.relationship_labeldistance = default_relationship_labeldistance_value

    return args


def parse_cpp_classes(cpp_file_path, class_pattern, args):
    if not os.path.isfile(cpp_file_path):
        raise ValueError("Error: No such file: '{}'".format(cpp_file_path))

    if args:
        args = args.split(" ")
    classes = search_class_in_file(cpp_file_path, class_pattern, args)
    if not classes:
        raise ValueError("Error: No class matching pattern '{}' in file '{}'".format(
            class_pattern, cpp_file_path))
        return None
    elif len(classes) > 1:
        classes_names = []
        for c in classes:
            classes_names.append(c["name"])
        raise ValueError("Error: Several classes are matching pattern '{}': {}".format(
            class_pattern, classes_names))
        return None

    return classes[0]


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


def build_uml_class_diagram_node_and_relationship(args):
    result = []

    cpp_class = None
    if args.file_path:
        try:
            cpp_class = parse_cpp_classes(args.file_path, args.class_name, args.clang_arguments)
            if cpp_class:
                node = build_uml_class_diagram_node(
                    cpp_class["full_name"], cpp_class["fields"], cpp_class["methods"])
                result.append(node)
        except ValueError as error:
            print(error)
            return None

    if args.relationship_type:
        if not args.relationship_depender:
            if not cpp_class:
                raise ValueError(
                    "Error: Neither RELATIONSHIP_DEPENDER is set nor cpp class is parsed")
                return None

            args.relationship_depender = cpp_class["full_name"]

        relationship = build_relationship(args.relationship_depender,
                                          args.relationship_dependee,
                                          args.relationship_type,
                                          args.relationship_taillabel,
                                          args.relationship_label,
                                          args.relationship_headlabel,
                                          args.relationship_labeldistance)
        result.append(relationship)

    return result


def main():
    args = parse_args()

    if not args:
        print "Error: Argument parser error"
        return 1

    argument_list_file = args.argument_list_file
    if argument_list_file:
        if not os.path.isfile(argument_list_file):
            raise ValueError("Error: No such file: '{}'".format(argument_list_file))

        with open(argument_list_file) as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            line_args = line.split(" -")
            line_args = [arg if arg[0] is "-" else ("-" + arg) for arg in line_args]
            line_args.append("--clang-arguments=\"{}\"".format(args.clang_arguments))

            line_args = parse_args(line_args)
            graph = build_uml_class_diagram_node_and_relationship(line_args)
            print graph
            return
    else:
        graph = build_uml_class_diagram_node_and_relationship(args)
        print "\n".join(graph)


if __name__ == "__main__":
    exit(main())
