#!/usr/bin/python
import json
import sys
import CppHeaderParser
import re
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description='Builds cpp class uml representation in dot node format')

    parser.add_argument('-f', '--header-file', help='Path to cpp header file.', required=True)
    parser.add_argument('-c', '--class-name', help='Path to json config file.', required=True)

    args = parser.parse_args()

    return args


def build_uml_properties_representation(cpp_class, access_modificator_representations):
    results = []

    uml_property_representation = "{} {} : {}"

    properties = cpp_class["properties"]
    for acc_mod, acc_mod_rep in access_modificator_representations.items():
        for property in properties[acc_mod]:
            results.append(uml_property_representation.format(
                acc_mod_rep, property["name"], property["type"]))

    return results


def build_uml_methods_representation(cpp_class, access_modificator_representations):
    results = []

    uml_method_representation = "{} {}( {} ): {} {}"
    uml_method_parameter_representation = "{} : {}"

    methods = cpp_class["methods"]
    for acc_mod, acc_mod_rep in access_modificator_representations.items():
        for method in methods[acc_mod]:
            parameters_representation = []
            for parameter in method["parameters"]:
                parameters_representation.append(
                    uml_method_parameter_representation.format(parameter["name"],
                                                               parameter["type"]))

            methodName = method["name"]
            returnType = ""
            if not method["constructor"] and not method["destructor"]:
                returnType = method["rtnType"]
            elif method["destructor"]:
                methodName = "~" + methodName

            specificators = ""
            if method["pure_virtual"]:
                specificators = "= 0"
            elif method["virtual"]:
                specificators = "[virtual]"
            elif method["override"]:
                specificators = "[override]"

            result = uml_method_representation.format(acc_mod_rep,
                                                      methodName,
                                                      ', '.join(parameters_representation),
                                                      returnType,
                                                      specificators)
            result = result.rstrip(": ")

            # if method["static"]:
            #     result = "<u>{}</u>".format(result)
            # elif method["pure_virtual"]:
            #     result = "<i>{}</i>".format(result)

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


def build_uml_class_representation(path_to_header, class_name):
    try:
        cppHeader = CppHeaderParser.CppHeader(path_to_header)
    except CppHeaderParser.CppParseError as e:
        print(e)
        sys.exit(1)

    cpp_class = cppHeader.classes[class_name]
    class_caption = "{}::{}".format(cpp_class["namespace"], cpp_class["name"])

    access_modificator_representations = {"private": "-", "protected": "#", "public": "+"}

    uml_properties_representation = build_uml_properties_representation(
        cpp_class, access_modificator_representations)

    uml_methods_representation = build_uml_methods_representation(
        cpp_class, access_modificator_representations)

    html_uml_properties_representation = build_html_uml_properties_representation(
        uml_properties_representation)
    html_uml_methods_representation = build_html_uml_methods_representation(
        uml_methods_representation)

    node_template = """
    [
    shape=none
    margin=0
    style="filled",
    fillcolor="grey75",
    fontcolor="black",
    label = {}
    ];"""

    label_value_template = """
    <<table border="0" cellspacing="0" cellborder="1">
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

    label_value = label_value_template.format(class_caption,
                                              '<br />'.join(html_uml_properties_representation),
                                              '<br />'.join(html_uml_methods_representation))
    node = node_template.format(label_value)

    print node


def main(argv):
    args = parse_args()
    build_uml_class_representation(args.header_file, args.class_name)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
