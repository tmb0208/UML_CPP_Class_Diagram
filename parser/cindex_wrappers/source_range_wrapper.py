#!/usr/bin/python
import os


class SourceRangeWrapper:
    def __init__(self, extent):
        start = extent.start
        end = extent.end

        if not start.file or not end.file:
            self.source = None
            return

        if start.file.name != end.file.name:
            raise ValueError("Start and end locations file path aren't equal: '{}', '{}'".format(
                start.file.name, end.file.name))
            return

        self.source = SourceRangeWrapper._read_extent(start.file.name)
        self.start_line = extent.start.line - 1
        self.start_column = extent.start.column - 1
        self.end_line = extent.end.line - 1
        self.end_column = extent.end.column - 1

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
    def _read_extent(file_path):
        if not os.path.isfile(file_path):
            raise ValueError("Error: No such file: '{}'".format(file_path))

        with open(file_path) as file:
            return file.readlines()

        return None
