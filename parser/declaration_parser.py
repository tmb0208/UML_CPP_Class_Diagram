#!/usr/bin/python
from extent import Extent
from string_with_brackets import StringWithBrackets
import re


class DeclarationParser:
    def __init__(self, declaration):
        self.declaration = declaration

    def match_template(self):
        template_keyword = "template"
        declaration_with_brackets = StringWithBrackets(self.declaration)

        template_start = declaration_with_brackets.find_outside_brackets(template_keyword)
        if template_start == -1:
            return None

        parameters_start = declaration_with_brackets.find_any_of_brackets("<", 1, template_start)
        if parameters_start == -1:
            raise ValueError(
                "Error: Could not find template parameters in method declaration '{}'".format(
                    self.declaration))
            return None

        parameters_end = declaration_with_brackets.find_any_of_brackets(">", 1, parameters_start)
        if parameters_end == -1:
            raise ValueError(
                "Error: Could not find template parameters end in method declaration '{}'".format(
                    self.declaration))
            return None

        return Extent.make_string_extent(template_start, parameters_end + 1)

    def match_method_name(self):
        declaration_with_brackets = StringWithBrackets(self.declaration)
        parameters_start = declaration_with_brackets.find_any_of_brackets('(')
        declaration_until_parameters = self.declaration[:parameters_start]

        identifiers = re.finditer(r"(?<![a-zA-Z_0-9])[a-zA-Z_][a-zA-Z_0-9]*(?![a-zA-Z_0-9])",
                                  declaration_until_parameters)

        # get last identifier before parameters
        name = None
        for name in identifiers:
            pass

        if not name:
            raise ValueError(
                "Error: Could not find name in method declaration '{}'".format(
                    self.declaration))
            return None

        return Extent.make_string_extent(name.start(), name.end())

    def match_method_type(self):
        template_extent = self.match_template()
        name_extent = self.match_method_name()
        if not name_extent:
            raise ValueError("Error: Could not match type in method declaration '{}'".format(
                self.declaration))
            return None

        type_start = (template_extent.end_column + 1) if template_extent else 0
        type_end = name_extent.start_column - 1
        return Extent.make_string_extent(type_start, type_end)

    def match_method_qualifiers(self):
        declaration_with_brackets = StringWithBrackets(self.declaration)

        parameters_end = declaration_with_brackets.find_any_of_brackets(")")
        if parameters_end == -1:
            raise ValueError(
                "Error: Could not find end of method parameters in method declaration '{}'".format(
                    self.declaration))
            return None

        return Extent.make_string_extent(parameters_end + 1, len(self.declaration))
