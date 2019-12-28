#!/usr/bin/python
from cindex_wrappers.file_declarations_parser import FileDeclarationsParser
from declaration_parsers.function_declaration_parser import FunctionDeclarationParser
from declaration_parsers.property_declaration_parser import PropertyDeclarationParser


class ClassParser:
    def __init__(self, source_file_path, class_name, clang_args=None):
        self.file_parser = FileDeclarationsParser(source_file_path, clang_args)
        self.class_name = class_name
        self.is_parsed = False

    def parse(self):
        self.parsed_classes = self.file_parser.findall_classes(self.class_name)
        self.is_parsed = True
        return self.parsed_classes

    def parse_with_all_declarations_if_only(self):
        if not self.is_parsed:
            self.parse()

        if not self.parsed_classes or len(self.parsed_classes) > 1:
            return None

        return ClassParser._extend_class_with_declaration_info(self.parsed_classes[0])

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
