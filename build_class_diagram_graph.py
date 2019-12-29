#!/usr/bin/python
import re
import os
import shlex
from parser.class_parser import ClassParser
from arguments_parser import ArgumentsParser
from uml_utils import build_uml_class_content
from dot_utils import build_graph


def parse_classes(args_list):
    result = []

    for args in args_list:
        if args.file_path:
            c = ClassParser(args.file_path, args.class_pattern, args.clang_arguments).parse()
            if c:
                result.append(c)

    return result


def main():
    args = ArgumentsParser.parse()
    if not args:
        print "Error: Argument parser error"
        return 1

    args_list = ArgumentsParser.parse_arguments_file(args.argument_list_file)
    if not args_list:
        args_list = [args]

    try:
        classes = parse_classes(args_list)

        node_dictionaries = []
        for c in classes:
            label = build_uml_class_content(c["full_name"], c["fields"], c["methods"])
            node_dictionaries.append({"name": c["full_name"], "label": label})

        graph = build_graph(args_list, classes, node_dictionaries)
        print graph
        return 0
    except ValueError as error:
        print(error)

    return 1


if __name__ == "__main__":
    exit(main())
