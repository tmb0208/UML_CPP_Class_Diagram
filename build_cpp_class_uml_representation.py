#!/usr/bin/python
import json
import sys
import CppHeaderParser
import re
import argparse
import os


def blockPrint():
    sys.stdout = open(os.devnull, 'w')


def enablePrint():
    sys.stdout = sys.__stdout__


def get_uml_class_diagram_relationships():
    return ["association", "dependency", "aggregation", "composition", "inheritance", "realization"]


def parse_args():
    default_relationship_dependee_value = "Node"
    default_relationship_labeldistance_value = 2

    parser = argparse.ArgumentParser(
        description='Extracts class diagram from header file and builds its representation and'
                    'relationship (optionally) in graphviz dot language.')

    parser.add_argument('-f', '--file-path', type=str, required=True,
                        help='Path to file which contains class definition.')
    parser.add_argument('-c', '--class-name', type=str,
                        help='Path to json config file. By default would be extracted from '
                             'FILE_PATH')

    parser.add_argument('-t', '--relationship-type', type=str,
                        choices=get_uml_class_diagram_relationships(),
                        help='Sets type of relationship '
                             '(if not set relationship would not be build)')
    parser.add_argument('-d', '--relationship-dependee', type=str,
                        help='Sets relationship dependee name (by default = "{}")'.format(
                            default_relationship_dependee_value))
    parser.add_argument('-tl', '--relationship-taillabel', type=str,
                        help='Sets relationship tail label')
    parser.add_argument('-l', '--relationship-label', type=str,
                        help='Sets relationship label')
    parser.add_argument('-hl', '--relationship-headlabel', type=str,
                        help='Sets relationship head label')
    parser.add_argument('-ld', '--relationship-labeldistance', type=int,
                        help='Sets relationship label distance (by default = "{}")'.format(
                            default_relationship_labeldistance_value))

    args = parser.parse_args()

    if not args.class_name:
        file = os.path.split(args.file_path)[1]
        args.class_name = os.path.splitext(file)[0]

    if not args.relationship_dependee:
        args.relationship_dependee = default_relationship_dependee_value

    if not args.relationship_labeldistance:
        args.relationship_labeldistance = default_relationship_labeldistance_value

    return args


def parse_cpp_class(cpp_file_path, class_name):
    if not os.path.isfile(cpp_file_path):
        raise ValueError("Error: No such file: '{}'".format(cpp_file_path))

    blockPrint()
    parsed_cpp_file = CppHeaderParser.CppHeader(cpp_file_path)
    enablePrint()

    if not class_name in parsed_cpp_file.classes:
        raise ValueError("Error: No such class: '{}'".format(class_name))

    return parsed_cpp_file.classes[class_name]


def replace_html_specific_characters(string):
    return string.replace("&", "&#38;").replace("<", "&#60;").replace(">", "&#62;")


def replace_multiple(string, old_arr, new):
    for old in old_arr:
        string = string.replace(old, new)

    return string


def replace_dot_id_specific_characters(string):
    return replace_multiple(string, [":", "<", ">", " ", ",", "="], "_")


def build_full_class_name(cpp_class):
    result = "{}::{}".format(cpp_class["namespace"], cpp_class["name"])
    if "template" in cpp_class:
        result += " " + cpp_class["template"]
    return result


# WORKAROUND
def is_property_valid(property):
    return not property["type"] == "using"


# WORKAROUND
def normalize_property_type(type):
    match = re.search(r"^.*?[^:]:[^:]", type)
    if match:
        return type[len(match.group(0))-1:]
    return type


def build_uml_properties_representation(properties, access_modificator_representations):
    results = []

    representation = "{} {} : {}"

    for acc_mod, acc_mod_rep in access_modificator_representations.items():
        for property in properties[acc_mod]:
            if is_property_valid(property):
                results.append(representation.format(acc_mod_rep,
                                                     property["name"],
                                                     normalize_property_type(property["type"])))

    return results


def build_uml_method_parameters_representation(method):
    results = []

    representation = "{} : {}"

    for parameter in method["parameters"]:
        results.append(
            representation.format(parameter["name"], parameter["type"]))

    return ', '.join(results)


def build_uml_method_name_representation(method):
    result = method["name"]

    if method["destructor"]:
        result = "~" + result

    return result


def build_uml_method_return_type_representation(method):
    if method["constructor"] or method["destructor"]:
        return ""

    return method["rtnType"]


def build_uml_method_specificators_representation(method):
    if method["pure_virtual"]:
        return "= 0"
    elif method["virtual"]:
        return "[virtual]"
    elif method["override"]:
        return "[override]"
    else:
        return ""


def build_uml_methods_representation(methods, access_modificator_representations):
    results = []

    representation = "{} {}( {} ) : {} {}"

    for acc_mod, acc_mod_rep in access_modificator_representations.items():
        for method in methods[acc_mod]:
            result = representation.format(acc_mod_rep,
                                           build_uml_method_name_representation(method),
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
    template = """<<table border="0" cellspacing="0" cellborder="1">
        <tr>
            <td>{}</td>
        </tr>
        <tr>
            <td ALIGN="left" BALIGN="left">{}</td>
        </tr>
        <tr>
            <td ALIGN="left" BALIGN="left">{}</td>
        </tr>
    </table>>"""

    full_name = replace_html_specific_characters(full_name)
    properties = format_uml_properties_to_html(uml_properties)
    methods = format_uml_methods_to_html(uml_methods)

    return template.format(full_name, '<br />'.join(properties), '<br />'.join(methods))


def build_dot_node(class_node_id, label):
    node_template = """{} [
    shape=none
    margin=0
    style="filled",
    fillcolor="grey75",
    fontcolor="black",
    label = {}
    ];"""

    return node_template.format(class_node_id, label)


def build_properties_and_methods_uml_representation(properties, methods):
    access_modificator_representations = {"private": "-", "protected": "#", "public": "+"}

    properties_representation = build_uml_properties_representation(
        properties, access_modificator_representations)
    methods_representation = build_uml_methods_representation(
        methods, access_modificator_representations)

    return properties_representation, methods_representation


def build_uml_class_diagram_node(class_node_id, full_class_name, properties, methods):
    uml_properties, uml_methods = build_properties_and_methods_uml_representation(
        properties, methods)
    class_content = format_uml_class_to_html(full_class_name, uml_properties, uml_methods)

    return build_dot_node(class_node_id, class_content)


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

    return "{} -> {} {}".format(depender, dependee, edge_attributes)


def main(argv):
    args = parse_args()

    try:
        cpp_class = parse_cpp_class(args.file_path, args.class_name)
    except ValueError as error:
        print(error)
        return 1

    full_class_name = build_full_class_name(cpp_class)
    class_node_id = replace_dot_id_specific_characters(full_class_name)

    node = build_uml_class_diagram_node(
        class_node_id, full_class_name, cpp_class["properties"], cpp_class["methods"])
    print node

    if args.relationship_type:
        relationship = build_relationship(class_node_id,
                                          args.relationship_dependee,
                                          args.relationship_type,
                                          args.relationship_taillabel,
                                          args.relationship_label,
                                          args.relationship_headlabel,
                                          args.relationship_labeldistance)
        print relationship


if __name__ == "__main__":
    sys.exit(main(sys.argv))
