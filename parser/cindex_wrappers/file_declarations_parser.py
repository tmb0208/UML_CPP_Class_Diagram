#!/usr/bin/python
from class_node_parser import ClassNodeParser
import clang.cindex
import os


class FileDeclarationsParser:
    def __init__(self, file_path, clang_args=None):
        self.file_path = file_path
        self.clang_args = clang_args
        self.options = clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES

        self.cached_file_nodes = None

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

    def _append_clang_source_args(self):
        file_ext = os.path.splitext(self.file_path)[1]
        if file_ext in [".cpp"]:
            if self.clang_args is None:
                self.clang_args = []

            arg = "-xc++"
            if arg not in self.clang_args:
                self.clang_args.append(arg)

    def _parse_file_nodes(self):
        if self.cached_file_nodes is not None:
            return self.cached_file_nodes

        self._append_clang_source_args()

        try:
            index = clang.cindex.Index.create()
            parsed_file = index.parse(self.file_path, args=self.clang_args, options=self.options)

            file_nodes = parsed_file.cursor.get_children()
            self.cached_file_nodes = filter(
                lambda node: node.location.file.name == parsed_file.spelling, file_nodes)

        except clang.cindex.TranslationUnitLoadError as error:
            print("Failed to parse file '{}' with clang args '{}': {}".format(
                self.file_path, self.clang_args, error))

        return self.cached_file_nodes

    def for_each_class_node_parser(self, func):
        file_nodes = self._parse_file_nodes()
        if not file_nodes:
            return

        class_nodes = self._filter_class_nodes(self.cached_file_nodes)
        for node in class_nodes:
            # FIXME: Class definition, previosly declared in header in other class is not parsed
            parser = ClassNodeParser(node["class_node"], node["parent_nodes"])
            func(parser)

    def parse_classes(self, full_name):
        results = []

        def func(parser):
            actual_full_name = parser.build_class_full_name()
            if actual_full_name is None:
                spelling = parser.node.spelling
                raise ValueError("Couldn't build full name. Class name: {}".format(spelling))
            elif actual_full_name == full_name:
                result = parser.parse()
                results.append(result)

            return None

        self.for_each_class_node_parser(func)
        return results

    def parse_classes_full_names(self):
        results = []

        def func(parser):
            result = parser.build_class_full_name()
            if result is None:
                spelling = parser.node.spelling
                raise ValueError("Couldn't build full name. Class name: {}".format(spelling))
                return

            results.append(result)

        self.for_each_class_node_parser(func)
        return results
