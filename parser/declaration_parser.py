#!/usr/bin/python
from extent import Extent
from string_with_brackets import StringWithBrackets
import re


def parse_property_declaration(declaration, name):
    result = {}

    if name:
        name_match = re.search(r"\s*{}\s*(=|{{|$)".format(name), declaration)

        if not name_match:
            raise ValueError(
                "Error: Could not match property name '{}' in declaration '{}'". format(
                    name, declaration))

        # TODO: Parse default
        # default = None
        # if name_match:
        #     if len(declaration) != name_match.end():
        #         default = declaration[name_match.end():].strip()
        # result["default"] = default

        type = declaration[:name_match.start()].strip()
    else:
        type = declaration

    result["type"] = type

    qualifiers = []
    if re.search(r"(^|\s+)static(\s+|$)", type):
        qualifiers.append("static")

    if re.search(r"(^|\s+)const(\s+|$)", type):
        qualifiers.append("const")

    if re.search(r"(^|\s+)mutable(\s+|$)", type):
        qualifiers.append("mutable")
    result["qualifiers"] = qualifiers

    return result


def _match_template(declaration):
    template_keyword = "template"
    declaration_with_brackets = StringWithBrackets(declaration)

    template_start = declaration_with_brackets.find_outside_brackets(template_keyword)
    if template_start == -1:
        return None

    parameters_start = declaration_with_brackets.find_any_of_brackets("<", 1, template_start)
    if parameters_start == -1:
        raise ValueError(
            "Error: Could not find template parameters in method declaration '{}'".format(
                declaration))
        return None

    parameters_end = declaration_with_brackets.find_any_of_brackets(">", 1, parameters_start)
    if parameters_end == -1:
        raise ValueError(
            "Error: Could not find template parameters end in method declaration '{}'".format(
                declaration))
        return None

    return Extent.make_string_extent(template_start, parameters_end + 1)


def _match_method_name(declaration):
    declaration_with_brackets = StringWithBrackets(declaration)
    parameters_start = declaration_with_brackets.find_any_of_brackets('(')
    declaration_until_parameters = declaration[:parameters_start]

    identifiers = re.finditer(r"(?<![a-zA-Z_0-9])[a-zA-Z_][a-zA-Z_0-9]*(?![a-zA-Z_0-9])",
                              declaration_until_parameters)

    # get last identifier before parameters
    name = None
    for name in identifiers:
        pass

    if not name:
        raise ValueError(
            "Error: Could not find name in method declaration '{}'".format(
                declaration))
        return None

    return Extent.make_string_extent(name.start(), name.end())


def _match_method_type(declaration):
    template_extent = _match_template(declaration)
    name_extent = _match_method_name(declaration)
    if not name_extent:
        raise ValueError("Error: Could not match type in method declaration '{}'".format(
            declaration))
        return None

    type_start = (template_extent.end_column + 1) if template_extent else 0
    type_end = name_extent.start_column - 1
    return Extent.make_string_extent(type_start, type_end)


def _match_method_qualifiers(declaration):
    declaration_with_brackets = StringWithBrackets(declaration)

    parameters_end = declaration_with_brackets.find_any_of_brackets(")")
    if parameters_end == -1:
        raise ValueError(
            "Error: Could not find end of method parameters in method declaration '{}'".format(
                declaration))
        return None

    return Extent.make_string_extent(parameters_end + 1, len(declaration))


def parse_method_declaration(declaration):
    result = {}

    type_extent = _match_method_type(declaration)
    type = type_extent.read_from_string(declaration)
    type = type.strip()
    result["type"] = type

    qualifiers = []

    template_extent = _match_template(declaration)
    if template_extent:
        qualifiers.append("template")
        result["template_declaration"] = template_extent.read_from_string(declaration)

    if re.search(r"(^|\s+)virtual(\s+|$)", type):
        qualifiers.append("virtual")

    if re.search(r"(^|\s+)static(\s+|$)", type):
        qualifiers.append("static")

    if re.search(r"(^|\s+)explicit(\s+|$)", type):
        qualifiers.append("explicit")

    qualifiers_extent = _match_method_qualifiers(declaration)
    qualifiers_string = qualifiers_extent.read_from_string(declaration)
    qualifiers_string = qualifiers_string.strip()
    if re.search(r"(^|\s+)override(\s+|$)", qualifiers_string):
        qualifiers.append("override")

    if re.search(r"(^|\s+)const(\s+|$)", qualifiers_string):
        qualifiers.append("const")

    if re.search(r"(^|\s+)=\s*0(\s+|$)", qualifiers_string):
        qualifiers.append("pure")

    if re.search(r"(^|\s+)=\s*delete(\s+|$)", qualifiers_string):
        qualifiers.append("deleted")

    if re.search(r"(^|\s+)=\s*default(\s+|$)", qualifiers_string):
        qualifiers.append("default")

    result["qualifiers"] = qualifiers

    return result
