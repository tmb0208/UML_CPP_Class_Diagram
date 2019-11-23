#!/usr/bin/python
import os


class Extent:
    def __init__(self, source, start_line, start_column, end_line, end_column):
        self.source = source
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = end_line
        self.end_column = end_column

    def read(self):
        if not self.source:
            return None

        result = []
        for i, line in enumerate(self.source):
            if i in range(self.start_line, self.end_line + 1):
                result.append(line)

        result[-1] = result[-1][:self.end_column]
        result[0] = result[0][self.start_column:]

        result = ''.join(result)
        result = ' '.join(result.split())
        return result

    @staticmethod
    def read_all_file_lines(file_path):
        if not os.path.isfile(file_path):
            raise ValueError("Error: No such file: '{}'".format(file_path))

        with open(file_path) as file:
            return file.readlines()

        return None

    @staticmethod
    def from_cindex_extent(extent):
        start = extent.start
        end = extent.end

        if start.file.name != end.file.name:
            raise ValueError("Start and end locations file path aren't equal: '{}', '{}'".format(
                start.file.name, end.file.name))

        source = Extent.read_all_file_lines(start.file.name)

        return Extent(source,
                      extent.start.line - 1,
                      extent.start.column - 1,
                      extent.end.line - 1,
                      extent.end.column - 1)

    @staticmethod
    def make_string_extent(string, start_column, end_column):
        source = string.split("\n")
        return Extent(source, 0, start_column, 0, end_column)
