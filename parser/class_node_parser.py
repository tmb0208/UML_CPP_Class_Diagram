#!/usr/bin/python
from extent import Extent
from class_parser import ClassParser
import clang.cindex
import re
from enum import Enum


class ClassNodeParser:
    def __init__(self, node, parent_nodes, file_path):
        self.node = node
        self.parent_nodes = parent_nodes
        self.file_path = file_path

    def parse_method_parameter_node(self, parameters_node):
        name = parameters_node.spelling
        declaration = Extent.from_cindex_extent(
            parameters_node.extent).read_from_file(self.file_path)
        return ClassParser.parse_property_node(name, declaration)

    def filter_method_parameters(self, method_nodes):
        results = []
        for node in method_nodes:
            if node.kind is clang.cindex.CursorKind.PARM_DECL:
                results.append(node)

        return results

    def parse_method_parameters_nodes(self, parameters_nodes):
        results = []
        for node in parameters_nodes:
            results.append(self.parse_method_parameter_node(node))

        return results

    # WORKAROUND Template Construct/Destructor
    def __match_method_name(self, spelling):
        match = re.search(r"^~?[a-zA-Z_][a-zA-Z0-9_]*", spelling)
        if not match:
            raise ValueError(
                "Error: Could not match method name in spelling '{}'". format(spelling))

        return match.group(0)

    def parse_method_node(self, node, access_specifier):
        name = node.spelling
        if "<" in name:
            name = self.__match_method_name(name)

        declaration = Extent.from_cindex_extent(node.extent).read_from_file(self.file_path)
        parameters_nodes = self.filter_method_parameters(node.get_children())
        parameters = self.parse_method_parameters_nodes(parameters_nodes)

        is_constructor = node.kind is clang.cindex.CursorKind.CONSTRUCTOR
        is_destructor = node.kind is clang.cindex.CursorKind.DESTRUCTOR

        return ClassParser.parse_method_node(
            name, declaration, parameters, access_specifier, is_constructor, is_destructor)

    def parse_field_node(self, node, access_specifier):
        name = node.spelling
        declaration = Extent.from_cindex_extent(node.extent).read_from_file(self.file_path)
        return ClassParser.parse_property_node(name, declaration, access_specifier)

    def parse_class_methods_and_fields_nodes(self, nodes, is_struct):
        class AccessSpecifier(Enum):
            PRIVATE = 0
            PROTECTED = 1
            PUBLIC = 2

        methods = []
        fields = []
        access_specifier = AccessSpecifier.PUBLIC if is_struct else AccessSpecifier.PRIVATE
        for node in nodes:
            if node.kind is clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
                access_specifier = next(
                    (s for s in AccessSpecifier if s.name == node.access_specifier.name), None)

            elif node.kind in [clang.cindex.CursorKind.CXX_METHOD,
                               clang.cindex.CursorKind.FUNCTION_TEMPLATE,
                               clang.cindex.CursorKind.DESTRUCTOR,
                               clang.cindex.CursorKind.CONSTRUCTOR]:
                methods.append(self.parse_method_node(node, access_specifier))

            elif node.kind is clang.cindex.CursorKind.FIELD_DECL:
                fields.append(self.parse_field_node(node, access_specifier))

        return methods, fields

    @staticmethod
    def match_class_declaration(class_declaration):
        match = re.search(
            r"(class|struct)[^{]*[a-z_][a-z_0-9]*(::[a-z_][a-z_0-9]*)?\s*(<[^{]*>)?\s*{",
            class_declaration)
        if not match:
            return None

        return class_declaration[:match.end() - 1].strip()

    # UNUSED
    @staticmethod
    def add_namespace_before_class_name(full_class_name, class_name, namespace):
        class_name_match = re.search(r"\s*{}\s*".format(class_name), full_class_name)
        if not class_name_match:
            raise ValueError("Could not match class name '{}' in full class name '{}'". format(
                class_name, full_class_name))
            return None

        return "{}{}::{}".format(full_class_name[:class_name_match.start() + 1],
                                 namespace,
                                 full_class_name[class_name_match.start() + 1:])

    def parse_class_declaration(self):
        declaration_or_definition = Extent.from_cindex_extent(
            self.node.extent).read_from_file(self.file_path)

        result = self.match_class_declaration(declaration_or_definition)
        if result is None:
            raise ValueError("Could not match class declaration from '{}'". format(
                declaration_or_definition))

        return result

    def build_class_namespace(self):
        result = str()
        for node in self.parent_nodes:
            name = node.spelling
            result += "::{}".format(name) if result else name

        return result

    def build_class_full_name(self):
        namespace = self.build_class_namespace()
        if namespace:
            return "{}::{}".format(namespace, self.node.spelling)

        return self.node.spelling

    def parse(self):
        is_struct = self.node.kind is clang.cindex.CursorKind.STRUCT_DECL
        methods, fields = self.parse_class_methods_and_fields_nodes(
            self.node.get_children(), is_struct)

        return {"namespace": self.build_class_namespace(),
                "name": self.node.spelling,
                "full_name": self.build_class_full_name(),
                "declaration": self.parse_class_declaration(),
                "methods": methods,
                "fields": fields}
