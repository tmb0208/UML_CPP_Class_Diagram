#!/usr/bin/python
import argparse
import os
import shlex


class ArgumentsParser:
    @staticmethod
    def _build_args_parser():
        default_relationship_labeldistance_value = 2
        uml_class_diagram_relationships = ["association", "dependency",
                                           "aggregation", "composition",
                                           "inheritance", "realization"]

        result = argparse.ArgumentParser(
            description='Builds uml class diagram from header file and/or relationship between '
                        'classes which are represented in graphviz dot language. '
                        'Elther FILE_PATH or RELATIONSHIP_TYPE or ARGUMENT_LIST_FILE is required. '
                        'C++ files parsing is based on clang library\n\n'
                        'Note[0]: Classes are matched by fullname, which consist of class '
                        'declaration and namespace before class name')

        result.add_argument('-f', '--file-path', type=str,
                            help='Path to file which contains class definition.')
        result.add_argument('-c', '--class-pattern', type=str,
                            help='Pattern of class to extract. See Note[0]. '
                                 'By default basename of FILE_PATH would be set')
        result.add_argument('-alf', '--argument-list-file', type=str,
                            help='Path to file where every line is argument to this executable.')
        result.add_argument('-a', '--clang-arguments', type=str,
                            help='Arguments passed to clang before parsing')

        result.add_argument('-t', '--relationship-type', type=str,
                            choices=uml_class_diagram_relationships,
                            help='Sets type of relationship. '
                                 'If it does not set relationship representation would not be '
                                 'build. '
                                 'If it is set RELATIONSHIP_DEPENDEE should be set. '
                                 'If FILE_PATH is not set then RELATIONSHIP_DEPENDER should be '
                                 'set.')
        result.add_argument('-dr', '--relationship-depender', type=str,
                            help='Sets relationship depender class pattern. See Note[0]. '
                                 'By default CLASS_NAME would be set')
        result.add_argument('-de', '--relationship-dependee', type=str,
                            help='Sets relationship dependee class pattern. See Note[0]. ')
        result.add_argument('-tl', '--relationship-taillabel', type=str,
                            help='Sets relationship tail label')
        result.add_argument('-l', '--relationship-label', type=str,
                            help='Sets relationship label')
        result.add_argument('-hl', '--relationship-headlabel', type=str,
                            help='Sets relationship head label')
        result.add_argument('-ld', '--relationship-labeldistance', type=int,
                            help='Sets relationship label distance.',
                            default=default_relationship_labeldistance_value)
        return result

    @staticmethod
    def _check_args_logic_error(args):
        if not args.file_path and not args.relationship_type and not args.argument_list_file:
            return "Error: Neither FILE_PATH nor RELATIONSHIP_TYPE nor FILE_LIST is set"
        elif args.relationship_type and not args.relationship_dependee:
            return "Error: RELATIONSHIP_TYPE is set, but RELATIONSHIP_DEPENDEE is not"
        elif args.relationship_type and not args.file_path and not args.relationship_depender:
            return ("Error: RELATIONSHIP_TYPE is set, but Neither FILE_PATH nor "
                    "RELATIONSHIP_DEPENDER is")
        else:
            return None

    @staticmethod
    def _update_args_with_defaults(args):
        if not args.class_pattern and args.file_path:
            file = os.path.split(args.file_path)[1]
            file_name = os.path.splitext(file)[0]
            args.class_pattern = r"(:|\s|^){}(<|\s|$)".format(file_name)

        if not args.clang_arguments:
            args.clang_arguments = []
        else:
            args.clang_arguments = shlex.split(args.clang_arguments)

        clang_arg = "-std=c++11"
        if clang_arg not in args.clang_arguments:
            args.clang_arguments.append("-std=c++11")

        return args

    @staticmethod
    def parse(args=None):
        parser = ArgumentsParser._build_args_parser()
        args = parser.parse_args(args)

        logic_error = ArgumentsParser._check_args_logic_error(args)
        if logic_error:
            print "Logical error when parsing arguments", logic_error
            parser.print_help()
            return None

        args = ArgumentsParser._update_args_with_defaults(args)

        return args

    @staticmethod
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
                raise ValueError(
                    "Error: Could not parse arguments from file '{}' line {}:'{}'".format(
                        file_path, n, line))
                return None

            result.append(line_args)

        return result
