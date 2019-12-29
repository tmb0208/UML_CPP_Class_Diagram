#!/usr/bin/python
from html_utils import format_uml_class_features_to_html


def _build_uml_properties_representation(properties, access_modificator_representations):
    results = []

    for property in properties:
        specifier = property["access_specifier"]
        specifier_representation = access_modificator_representations[specifier]

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


def _build_uml_methods_representation(methods, access_modificator_representations):
    results = []

    representation = "{} {}( {} ) : {} {}"

    for method in methods:
        specifier = method["access_specifier"]
        specifier_representation = access_modificator_representations[specifier]
        result = representation.format(specifier_representation,
                                       method["name"],
                                       _build_uml_method_parameters_representation(method),
                                       _build_uml_method_return_type_representation(method),
                                       _build_uml_method_specificators_representation(method))

        result = result.rstrip(": ")
        results.append(result)

    return results


def _build_properties_and_methods_uml_representation(properties, methods):
    access_modificator_representations = {"PRIVATE": "-", "PROTECTED": "#", "PUBLIC": "+"}

    properties_representation = _build_uml_properties_representation(
        properties, access_modificator_representations)
    methods_representation = _build_uml_methods_representation(
        methods, access_modificator_representations)

    return properties_representation, methods_representation


def build_uml_class_content(full_class_name, properties, methods):
    uml_properties, uml_methods = _build_properties_and_methods_uml_representation(
        properties, methods)
    return format_uml_class_features_to_html(full_class_name, uml_properties, uml_methods)
