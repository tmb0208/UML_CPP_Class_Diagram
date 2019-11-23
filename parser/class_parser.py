#!/usr/bin/python
from cindex_wrappers.file_node_parser import FileNodeParser
from declaration_parsers.function_declaration_parser import FunctionDeclarationParser
from declaration_parsers.property_declaration_parser import PropertyDeclarationParser


class ClassParser:
    def __init__(self, source_file_path, class_pattern, clang_args=None):
        self.file_parser = FileNodeParser(source_file_path, clang_args)
        self.class_pattern = class_pattern

    def parse(self):
        classes = self.file_parser.parse_class(self.class_pattern)
        if classes is None:
            return None

        if len(classes) > 1:
            classes_full_names = []
            for c in classes:
                classes_full_names.append(c["full_name"])
            raise ValueError(
                "Error: In file '{}' several classes are matching pattern '{}': {}".format(
                    self.file_parser.file_path, self.class_pattern, classes_full_names))
            return None

        result = ClassParser._extend_class_with_declaration_info(classes[0])
        return result

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
