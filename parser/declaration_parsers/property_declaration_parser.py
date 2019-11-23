#!/usr/bin/python
import re


class PropertyDeclarationParser:
    def __init__(self, declaration, name):
        self.declaration = declaration
        self.name = name

    def parse(self):
        result = {}

        if self.name:
            name_match = re.search(r"\s*{}\s*(=|{{|$)".format(self.name), self.declaration)

            if not name_match:
                raise ValueError(
                    "Error: Could not match property name '{}' in declaration '{}'". format(
                        self.name, self.declaration))

            # TODO: Parse default
            # default = None
            # if name_match:
            #     if len(declaration) != name_match.end():
            #         default = declaration[name_match.end():].strip()
            # result["default"] = default

            type = self.declaration[:name_match.start()].strip()
        else:
            type = self.declaration

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
