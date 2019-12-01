#!/usr/bin/python
from source_range_wrapper import SourceRangeWrapper
import clang.cindex
import re


class ClassNodeParser:
    def __init__(self, node, parent_nodes):
        self.node = node
        self.parent_nodes = parent_nodes

    def _parse_method_parameter_node(self, parameters_node):
        declaration = SourceRangeWrapper(parameters_node.extent).read()
        if declaration is None:
            return None

        return {"name": parameters_node.spelling, "declaration": declaration}

    def _parse_method_parameters_nodes(self, method_nodes):
        results = []
        for node in method_nodes:
            if node.kind is clang.cindex.CursorKind.PARM_DECL:
                result = self._parse_method_parameter_node(node)
                if result is None:
                    return None

                results.append(result)

        return results

    # WORKAROUND Template Construct/Destructor
    def _match_method_name(self, spelling):
        match = re.search(r"^~?[a-zA-Z_][a-zA-Z0-9_]*", spelling)
        if not match:
            raise ValueError(
                "Error: Could not match method name in spelling '{}'". format(spelling))

        return match.group(0)

    def _parse_method_node(self, node):
        result = {}

        result["access_specifier"] = node.access_specifier.name

        name = node.spelling
        if "<" in name:
            name = self._match_method_name(name)
        result["name"] = name

        result["declaration"] = SourceRangeWrapper(node.extent).read()

        parameters = self._parse_method_parameters_nodes(node.get_children())
        if parameters is None:
            return None

        result["parameters"] = parameters

        qualifiers = []
        if node.kind is clang.cindex.CursorKind.CONSTRUCTOR:
            qualifiers = ["constructor"]
        elif node.kind is clang.cindex.CursorKind.DESTRUCTOR:
            qualifiers = ["destructor"]
        result["qualifiers"] = qualifiers

        return result

    def _parse_method_nodes(self, nodes):
        results = []
        for node in nodes:
            if node.kind in [clang.cindex.CursorKind.CXX_METHOD,
                             clang.cindex.CursorKind.FUNCTION_TEMPLATE,
                             clang.cindex.CursorKind.DESTRUCTOR,
                             clang.cindex.CursorKind.CONSTRUCTOR]:
                result = self._parse_method_node(node)
                if result is None:
                    print "WARNING: Failed to parse method:", SourceRangeWrapper(node.extent).read()
                    continue

                results.append(result)

        return results

    def _parse_field_node(self, node):
        return {"name": node.spelling,
                "declaration": SourceRangeWrapper(node.extent).read(),
                "access_specifier": node.access_specifier.name}

    def _parse_field_nodes(self, nodes):
        results = []
        for node in nodes:
            if node.kind in [clang.cindex.CursorKind.FIELD_DECL, clang.cindex.CursorKind.VAR_DECL]:
                results.append(self._parse_field_node(node))

        return results

    @staticmethod
    def _match_class_declaration(class_declaration):
        match = re.search(
            r"(class|struct)[^{]*[a-zA-Z_]\w*(::[a-zA-Z_]\w*)?\s*(<[^{]*>)?\s*{",
            class_declaration)
        if not match:
            return None

        return class_declaration[:match.end() - 1].strip()

    # UNUSED
    @staticmethod
    def _add_namespace_before_class_name(full_class_name, class_name, namespace):
        class_name_match = re.search(r"\s*{}\s*".format(class_name), full_class_name)
        if not class_name_match:
            raise ValueError("Could not match class name '{}' in full class name '{}'". format(
                class_name, full_class_name))
            return None

        return "{}{}::{}".format(full_class_name[:class_name_match.start() + 1],
                                 namespace,
                                 full_class_name[class_name_match.start() + 1:])

    def _parse_class_declaration(self):
        declaration_or_definition = SourceRangeWrapper(self.node.extent).read()

        result = self._match_class_declaration(declaration_or_definition)
        if result is None:
            raise ValueError("Could not match class declaration from '{}'". format(
                declaration_or_definition))

        return result

    def _build_class_namespace(self):
        result = str()
        for node in self.parent_nodes:
            name = node.spelling
            result += "::{}".format(name) if result else name

        return result

    def build_class_full_name(self):
        namespace = self._build_class_namespace()
        if namespace:
            return "{}::{}".format(namespace, self.node.spelling)

        return self.node.spelling

    def parse(self):
        return {"namespace": self._build_class_namespace(),
                "name": self.node.spelling,
                "full_name": self.build_class_full_name(),
                "declaration": self._parse_class_declaration(),
                "methods": self._parse_method_nodes(self.node.get_children()),
                "fields": self._parse_field_nodes(self.node.get_children())}
