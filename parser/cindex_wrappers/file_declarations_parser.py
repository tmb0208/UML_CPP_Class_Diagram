#!/usr/bin/python
from class_node_parser import ClassNodeParser
import clang.cindex
import re
import os


class FileDeclarationsParser:
    def __init__(self, file_path, clang_args=None):
        self.file_path = file_path
        self.clang_args = clang_args
        self.options = clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES

        self.file_nodes = None

    def _is_class(self, node_kind):
        return node_kind in [clang.cindex.CursorKind.CLASS_TEMPLATE,
                             clang.cindex.CursorKind.CLASS_DECL,
                             clang.cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
                             clang.cindex.CursorKind.STRUCT_DECL]

    def _filter_class_nodes(self, nodes, parent_nodes=None):
        results = []

        if parent_nodes is None:
            parent_nodes = []

        for node in nodes:
            if node.kind is clang.cindex.CursorKind.NAMESPACE or self._is_class(node.kind):
                if self._is_class(node.kind):
                    results.append({"parent_nodes": parent_nodes, "class_node": node})

                class_nodes = self._filter_class_nodes(node.get_children(), parent_nodes + [node])
                if class_nodes:
                    results = results + class_nodes

        return results

    def _parse_matching_class_node(self, class_node, parent_nodes, class_name):
        # FIXME: Class definition, previosly declared in header in other class is not parsed
        parser = ClassNodeParser(class_node, parent_nodes)
        full_name = parser.build_class_full_name()
        if full_name is None:
            raise ValueError("Couldn't build full name. Class name: {}".format(class_node.spelling))
            return None

        if re.search(r"(.*::)?{}$".format(class_name), full_name):
            return parser.parse()

        return None

    def _parse_matching_class_nodes(self, pattern):
        results = []

        class_nodes = self._filter_class_nodes(self.file_nodes)
        for node in class_nodes:
            result = self._parse_matching_class_node(
                node["class_node"], node["parent_nodes"], pattern)
            if result:
                results.append(result)

        return results

    def _append_clang_source_args(self):
        file_ext = os.path.splitext(self.file_path)[1]
        if file_ext in [".cpp"]:
            if self.clang_args is None:
                self.clang_args = []

            arg = "-xc++"
            if arg not in self.clang_args:
                self.clang_args.append(arg)

    def _filter_nodes_by_file_name(self, nodes, file_name):
        result = []
        for node in nodes:
            if node.location.file.name == file_name:
                result.append(node)

        return result

    def _parse_file(self):
        if self.file_nodes is not None:
            return True

        self._append_clang_source_args()

        try:
            index = clang.cindex.Index.create()
            parsed_file = index.parse(self.file_path, args=self.clang_args, options=self.options)

            self.file_nodes = self._filter_nodes_by_file_name(parsed_file.cursor.get_children(),
                                                              parsed_file.spelling)
            return True
        except clang.cindex.TranslationUnitLoadError as error:
            print("Failed to parse file '{}' with clang args '{}': {}".format(
                self.file_path, self.clang_args, error))
            return False

    def findall_classes(self, class_name):
        if not self._parse_file():
            return None

        return self._parse_matching_class_nodes(class_name)
