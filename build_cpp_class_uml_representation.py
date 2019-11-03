#!/usr/bin/python
import json
import sys
import CppHeaderParser
import re
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser(
        description='Builds graphviz dot node containing cpp class uml representation')

    parser.add_argument('-f', '--file-path', help='Path to cpp source file.', required=True)
    parser.add_argument('-c', '--class-name',
                        help='Path to json config file. By default would be extracted from file '
                             'name')

    args = parser.parse_args()

    if not args.class_name:
        file = os.path.split(args.file_path)[1]
        args.class_name = os.path.splitext(file)[0]

    return args


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
            representation.format(parameter["name"],
                                  parameter["type"]))

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
            result = representation.format(
                acc_mod_rep,
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


def replace_html_specific_characters(string):
    return string.replace("&", "&#38;").replace("<", "&#60;").replace(">", "&#62;")


def build_html_uml_properties_representation(uml_properties_representation):
    results = []

    for r in uml_properties_representation:
        r = replace_html_specific_characters(r)
        r = underline_if_static(r)
        results.append(r)

    return results


def build_html_uml_methods_representation(uml_methods_representation):
    results = []

    for r in uml_methods_representation:
        r = replace_html_specific_characters(r)
        r = underline_if_static(r)
        r = italic_if_pure_virtual(r)
        r = format_if_too_long(r, 100)
        results.append(r)

    return results


def build_html_uml_class_representation(class_caption,
                                        html_uml_properties_representation,
                                        html_uml_methods_representation):
    label_value_template = """<<table border="0" cellspacing="0" cellborder="1">
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

    return label_value_template.format(class_caption,
                                       '<br />'.join(html_uml_properties_representation),
                                       '<br />'.join(html_uml_methods_representation))


def build_dot_node(label_value):
    node_template = """[
    shape=none
    margin=0
    style="filled",
    fillcolor="grey75",
    fontcolor="black",
    label = {}
    ];"""

    return node_template.format(label_value)


def build_dot_node_class_uml_representation(path_to_header, class_name):
    try:
        cppHeader = CppHeaderParser.CppHeader(path_to_header)
    except CppHeaderParser.CppParseError as e:
        print(e)
        sys.exit(1)

    if not class_name in cppHeader.classes:
        return "Error: No such class"

    cpp_class = cppHeader.classes[class_name]
    class_caption = "{}::{}".format(cpp_class["namespace"], cpp_class["name"])
    if "template" in cpp_class:
        class_caption += " " + cpp_class["template"]
    class_caption = replace_html_specific_characters(class_caption)

    access_modificator_representations = {"private": "-", "protected": "#", "public": "+"}
    uml_properties_representation = build_uml_properties_representation(
        cpp_class["properties"], access_modificator_representations)
    uml_methods_representation = build_uml_methods_representation(
        cpp_class["methods"], access_modificator_representations)

    html_uml_properties_representation = build_html_uml_properties_representation(
        uml_properties_representation)
    html_uml_methods_representation = build_html_uml_methods_representation(
        uml_methods_representation)

    html_uml_class_representation = build_html_uml_class_representation(
        class_caption,
        html_uml_properties_representation,
        html_uml_methods_representation)

    return build_dot_node(html_uml_class_representation)


def main(argv):
    args = parse_args()
    node = build_dot_node_class_uml_representation(args.file_path, args.class_name)
    print node


if __name__ == "__main__":
    sys.exit(main(sys.argv))
