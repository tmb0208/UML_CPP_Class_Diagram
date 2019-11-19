#!/usr/bin/python
import re
from method_parser import MethodParser


class ClassBuilder:
    @staticmethod
    def build_property(name, declaration, access_specifier=None):
        result = {}

        result["name"] = name
        result["declaration"] = declaration
        if access_specifier:
            result["access_specifier"] = access_specifier

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

    @staticmethod
    def build_method(name, declaration, parameters, access_specifier, is_constructor,
                     is_destructor):
        result = {}

        result["name"] = name
        result["declaration"] = declaration
        result["parameters"] = parameters
        result["access_specifier"] = access_specifier

        mathod_parser = MethodParser(declaration)

        type_extent = mathod_parser.match_method_type()
        type = type_extent.read_from_string(declaration)
        type = type.strip()
        result["type"] = type

        qualifiers = []

        template_extent = mathod_parser.match_template()
        if template_extent:
            qualifiers.append("template")
            result["template_declaration"] = template_extent.read_from_string(declaration)

        if is_constructor:
            qualifiers.append("constructor")

        elif is_destructor:
            qualifiers.append("destructor")

        if re.search(r"(^|\s+)virtual(\s+|$)", type):
            qualifiers.append("virtual")

        if re.search(r"(^|\s+)static(\s+|$)", type):
            qualifiers.append("static")

        if re.search(r"(^|\s+)explicit(\s+|$)", type):
            qualifiers.append("explicit")

        qualifiers_extent = mathod_parser.match_method_qualifiers()
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
