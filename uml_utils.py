#!/usr/bin/python
from html_utils import format_uml_class_features_to_html

_uml_specifier_representations = {"PRIVATE": "-", "PROTECTED": "#", "PUBLIC": "+"}


def _build_uml_properties_representation(properties):
    results = []
    for property in properties:
        specifier = property["access_specifier"]
        specifier_representation = _uml_specifier_representations[specifier]
        result = "{} {} : {}".format(specifier_representation, property["name"], property["type"])
        results.append(result)

    return results


def _build_uml_method_parameters_representation(method):
    results = []

    representation = "{} : {}"

    for parameter in method["parameters"]:
        results.append(
            representation.format(parameter["name"], parameter["type"]))

    return ', '.join(results)


def _build_uml_method_return_type_representation(method):
    if "constructor" in method["qualifiers"] or "destructor" in method["qualifiers"]:
        return ""

    return method["type"]


def _build_uml_method_specificators_representation(method):
    if "pure" in method["qualifiers"] or "virtual" in method["qualifiers"]:
        return "= 0"
    elif "virtual" in method["qualifiers"]:
        return "[virtual]"
    elif "override" in method["qualifiers"]:
        return "[override]"
    else:
        return ""


def _build_uml_methods_representation(methods):
    results = []

    representation = "{} {}( {} ) : {} {}"

    for method in methods:
        specifier = method["access_specifier"]
        specifier_representation = _uml_specifier_representations[specifier]
        result = representation.format(specifier_representation,
                                       method["name"],
                                       _build_uml_method_parameters_representation(method),
                                       _build_uml_method_return_type_representation(method),
                                       _build_uml_method_specificators_representation(method))

        result = result.rstrip(": ")
        results.append(result)

    return results


def build_uml_class_content(full_class_name, properties, methods):
    properties_uml = _build_uml_properties_representation(properties)
    methods_uml = _build_uml_methods_representation(methods)
    return format_uml_class_features_to_html(full_class_name, properties_uml, methods_uml)
