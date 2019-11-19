#!/usr/bin/python
import re
from declaration_parser import parse_field_declaration, parse_method_declaration


class ClassBuilder:
    @staticmethod
    def build_property(name, declaration, access_specifier=None):
        result = {}

        result["name"] = name
        result["declaration"] = declaration
        if access_specifier:
            result["access_specifier"] = access_specifier

        result.update(parse_field_declaration(declaration, name))

        return result

    @staticmethod
    def build_method(name, declaration, parameters, access_specifier, is_constructor,
                     is_destructor):
        result = {}

        result["name"] = name
        result["declaration"] = declaration
        result["parameters"] = parameters
        result["access_specifier"] = access_specifier

        qualifiers = []
        if is_constructor:
            qualifiers.append("constructor")

        elif is_destructor:
            qualifiers.append("destructor")
        result["qualifiers"] = qualifiers

        result.update(parse_method_declaration(declaration))
        result["qualifiers"] = result["qualifiers"] + qualifiers

        return result
