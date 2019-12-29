#!/usr/bin/python
from parser.class_parser import ClassParser
from arguments_parser import ArgumentsParser
from html_utils import format_uml_class_features_to_html
from uml_utils import build_uml_properties_representation, build_uml_methods_representation
from dot_utils import build_graph


def parse_classes(args_list):
    result = []

    for args in args_list:
        if args.file_path:
            c = ClassParser(args.file_path, args.class_pattern, args.clang_arguments).parse()
            if c:
                result.append(c)

    return result


def build_node_dictionaries(classes):
    results = []
    for _class in classes:
        full_name = _class["full_name"]
        properties_uml = build_uml_properties_representation(_class["fields"])
        methods_uml = build_uml_methods_representation(_class["methods"])
        label = format_uml_class_features_to_html(full_name, properties_uml, methods_uml)
        results.append({"name": full_name, "label": label})

    return results


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
        node_dictionaries = build_node_dictionaries(classes)
        graph = build_graph(args_list, node_dictionaries)
        print graph
        return 0
    except ValueError as error:
        print(error)

    return 1


if __name__ == "__main__":
    exit(main())
