#!/usr/bin/python
import re


def replace_html_specific_characters(string):
    return string.replace("&", "&#38;").replace("<", "&#60;").replace(">", "&#62;")


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
