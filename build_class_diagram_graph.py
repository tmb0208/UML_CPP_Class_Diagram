#!/usr/bin/python
import re
import os
import shlex
from parser.class_parser import ClassParser
from arguments_parser import ArgumentsParser
from dot_utils import build_classes_nodes, build_relationships


def parse_classes(args_list):
    result = []

    for args in args_list:
        if args.file_path:
            c = ClassParser(args.file_path, args.class_pattern, args.clang_arguments).parse()
            if c:
                result.append(c)

    return result


def match_class_full_name(classes, pattern):
    results = []
    full_names = []
    for c in classes:
        full_names.append(c["full_name"])
        if re.search(pattern, c["full_name"]):
            results.append(c["full_name"])

    if not results:
        raise ValueError(
            "Error: No class full name matching pattern '{}': {}".format(pattern, full_names))
        return None
    elif len(results) > 1:
        raise ValueError("Error: Several classes full name are matching pattern '{}': {}".format(
            pattern, results))
        return None

    return results[0]


def parse_arguments_file(file_path):
    if not file_path:
        return None

    result = []
    if not os.path.isfile(file_path):
        raise ValueError("Error: No such file: '{}'".format(file_path))

    with open(file_path) as f:
        lines = f.readlines()

    for n, line in enumerate(lines):
        line_args = shlex.split(line)
        line_args = ArgumentsParser.parse(line_args)
        if not line_args:
            raise ValueError("Error: Could not parse arguments from file '{}' line {}:'{}'".format(
                file_path, n, line))
            return None

        result.append(line_args)

    return result


def build_graph(nodes, relationships):
    template = ('digraph "Class Diagram"\n'
                '{{\n'
                '\tbgcolor = transparent;\n'
                '\trankdir = LR;\n'
                '\tedge [fontname = Helvetica, fontsize = 10, labelfontname = Helvetica, '
                'labelfontsize = 10];\n'
                '\tnode [fontname = Helvetica, fontsize = 10, shape = none, margin = 0, '
                'style = filled, fillcolor = grey75, fontcolor = black ];\n'
                '\n'
                '{}\n'
                '\n'
                '{}\n'
                '}}')

    return template.format("\n".join(nodes), "\n".join(relationships))


def main():
    args = ArgumentsParser.parse()
    if not args:
        print "Error: Argument parser error"
        return 1

    args_list = parse_arguments_file(args.argument_list_file)
    if not args_list:
        args_list = []
        args_list.append(args)

    try:
        classes = parse_classes(args_list)
        nodes = build_classes_nodes(classes)

        relationships = build_relationships(args_list, classes)

        graph = build_graph(nodes, relationships)
        print graph
        return 0
    except ValueError as error:
        print(error)

    return 1


if __name__ == "__main__":
    exit(main())
