#!/usr/bin/python
from ..utils.extent import Extent
from ..string_with_brackets import StringWithBrackets
import re


class FunctionDeclarationParser:
    def __init__(self, declaration):
        self.declaration = declaration

    def _match_template(self):
        declaration_with_brackets = StringWithBrackets(self.declaration)

        template_start = declaration_with_brackets.find_outside_brackets("template")
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

        return Extent.make_string_extent(self.declaration, template_start, parameters_end + 1)

    def _match_name(self):
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

        return Extent.make_string_extent(self.declaration, name.start(), name.end())

    def _match_type(self):
        template_extent = self._match_template()
        name_extent = self._match_name()
        if not name_extent:
            raise ValueError("Error: Could not match type in method declaration '{}'".format(
                self.declaration))
            return None

        type_start = (template_extent.end_column + 1) if template_extent else 0
        type_end = name_extent.start_column - 1
        return Extent.make_string_extent(self.declaration, type_start, type_end)

    def _match_qualifiers(self):
        declaration_with_brackets = StringWithBrackets(self.declaration)

        parameters_end = declaration_with_brackets.find_any_of_brackets(")")
        if parameters_end == -1:
            raise ValueError(
                "Error: Could not find end of method parameters in method declaration '{}'".format(
                    self.declaration))
            return None

        return Extent.make_string_extent(self.declaration, parameters_end + 1, len(self.declaration))

    def parse(self):
        result = {}

        type_extent = self._match_type()
        type = type_extent.read()
        type = type.strip()
        result["type"] = type

        qualifiers = []

        template_extent = self._match_template()
        if template_extent:
            qualifiers.append("template")
            result["template_declaration"] = template_extent.read()

        if re.search(r"(^|\s+)virtual(\s+|$)", type):
            qualifiers.append("virtual")

        if re.search(r"(^|\s+)static(\s+|$)", type):
            qualifiers.append("static")

        if re.search(r"(^|\s+)explicit(\s+|$)", type):
            qualifiers.append("explicit")

        qualifiers_extent = self._match_qualifiers()
        qualifiers_string = qualifiers_extent.read()
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
