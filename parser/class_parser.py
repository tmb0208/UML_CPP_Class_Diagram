#!/usr/bin/python
import os
import re
from cindex_wrappers.file_declarations_parser import FileDeclarationsParser
from declaration_parsers.function_declaration_parser import FunctionDeclarationParser
from declaration_parsers.property_declaration_parser import PropertyDeclarationParser


class ClassParser:
    def __init__(self, file_path, class_name, clang_args=None):
        self.file_parser = FileDeclarationsParser(file_path, clang_args)
        self.class_name = class_name

    def _search_class_full_name(self):
        classes_full_names = self.file_parser.parse_classes_full_names()
        if not classes_full_names:
            raise ValueError(
                "Error: No classes in file '{}', clang args: {}".format(file_path, clang_args))
            return None

        class_pattern = r"(.*::)?{}$".format(self.class_name)
        matched_classes_full_names = filter(lambda full_name: re.search(class_pattern, full_name),
                                            classes_full_names)
        if not matched_classes_full_names:
            raise ValueError(
                "Error: No class matching pattern '{}' in file '{}', clang args '{}', "
                "suggested classes: {}".format(class_pattern, file_path, clang_args,
                                               classes_full_names))
            return None

        elif len(matched_classes_full_names) > 1:
            raise ValueError(
                "Error: In file '{}' several classes are matching pattern '{}': {}".format(
                    file_path, class_pattern, matched_classes_full_names))
            return None

        return matched_classes_full_names[0]

    def parse(self):
        matched_full_name = self._search_class_full_name()
        if matched_full_name:
            results = self.file_parser.parse_classes(matched_full_name)

            if len(results) == 1:
                result = results[0]
                result = ClassParser._extend_class_with_declaration_info(result)
                return result

        return None

    @staticmethod
    def _extend_properties_with_declaration_info(properties):
        for property in properties:
            parsed_declaration = PropertyDeclarationParser(
                property["declaration"], property["name"]).parse()
            property.update(parsed_declaration)

        return properties

    @staticmethod
    def _extend_method_with_declaration_info(method):
        qualifiers = method["qualifiers"]
        parsed_declaration = FunctionDeclarationParser(method["declaration"]).parse()
        method.update(parsed_declaration)
        method["qualifiers"] = method["qualifiers"] + qualifiers
        method["parameters"] = ClassParser._extend_properties_with_declaration_info(
            method["parameters"])

        return method

    @staticmethod
    def _extend_methods_with_declaration_info(methods):
        for method in methods:
            method = ClassParser._extend_method_with_declaration_info(method)

        return methods

    @staticmethod
    def _extend_class_with_declaration_info(_class):
        _class["methods"] = ClassParser._extend_methods_with_declaration_info(_class["methods"])
        _class["fields"] = ClassParser._extend_properties_with_declaration_info(_class["fields"])

        return _class
