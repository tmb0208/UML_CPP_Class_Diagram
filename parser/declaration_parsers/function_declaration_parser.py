#!/usr/bin/python
from string_with_brackets import StringWithBrackets
import re


class StringRange:
    def __init__(self, string, start, end):
        self.string = string
        self.start = start
        self.end = end

    @property
    def value(self):
        return self.string[self.start:self.end]


class FunctionDeclarationParser:

    def __init__(self, declaration):
        self.declaration = declaration

    def _search_template(self):
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

        return StringRange(self.declaration, template_start, parameters_end + 1)

    def _search_name(self):
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

        return StringRange(self.declaration, name.start(), name.end())

    def _search_type(self):
        template_range = self._search_template()
        name_range = self._search_name()
        if not name_range:
            raise ValueError("Error: Could not match type in method declaration '{}'".format(
                self.declaration))
            return None

        type_start = (template_range.end + 1) if template_range else 0
        type_end = name_range.start - 1
        return StringRange(self.declaration, type_start, type_end)

    def _search_qualifiers(self):
        declaration_with_brackets = StringWithBrackets(self.declaration)

        parameters_end = declaration_with_brackets.find_any_of_brackets(")")
        if parameters_end == -1:
            raise ValueError(
                "Error: Could not find end of method parameters in method declaration '{}'".format(
                    self.declaration))
            return None

        return StringRange(self.declaration, parameters_end + 1, len(self.declaration))

    def parse(self):
        result = {}

        type_range = self._search_type()
        type = type_range.value
        type = type.strip()
        result["type"] = type

        qualifiers = []

        template_range = self._search_template()
        if template_range:
            qualifiers.append("template")
            result["template_declaration"] = template_range.value

        if re.search(r"(^|\s+)virtual(\s+|$)", type):
            qualifiers.append("virtual")

        if re.search(r"(^|\s+)static(\s+|$)", type):
            qualifiers.append("static")

        if re.search(r"(^|\s+)explicit(\s+|$)", type):
            qualifiers.append("explicit")

        qualifiers_string = self._search_qualifiers().value
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
