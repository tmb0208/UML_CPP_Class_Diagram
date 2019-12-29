#!/usr/bin/python
import re


def _replace_html_specific_characters(string):
    return string.replace("&", "&#38;").replace("<", "&#60;").replace(">", "&#62;")


def _underline_if_static(declaration):
    if re.search(r":.* static .*", declaration):
        return "<u>{}</u>".format(declaration)

    return declaration


def _italic_if_pure_virtual(declaration):
    if re.search(r":.*= 0.*", declaration):
        return "<i>{}</i>".format(declaration)

    return declaration


def _format_if_too_long(declaration, max_chars, spacing=8):
    if len(declaration) > max_chars:
        html_sep = "<br />" + (" " * spacing)
        return declaration.replace("( ", "(" + html_sep).replace(", ", "," + html_sep)

    return declaration


def _format_uml_properties_to_html(properties):
    results = []
    for p in properties:
        result = _replace_html_specific_characters(p)
        result = _underline_if_static(result)
        results.append(result)

    return results


def _format_uml_methods_to_html(methods):
    results = []
    for m in methods:
        result = _replace_html_specific_characters(m)
        result = _underline_if_static(result)
        result = _italic_if_pure_virtual(result)
        result = _format_if_too_long(result, 100)
        results.append(result)

    return results


def format_uml_class_features_to_html(full_name, properties, methods):
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

    full_name = _replace_html_specific_characters(full_name)
    properties = _format_uml_properties_to_html(properties)
    methods = _format_uml_methods_to_html(methods)

    return template.format(full_name, '<br />'.join(properties), '<br />'.join(methods))
