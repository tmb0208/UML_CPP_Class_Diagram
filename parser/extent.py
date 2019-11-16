import os


class Extent:
    def __init__(self, start_line, start_column, end_line, end_column):
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = end_line
        self.end_column = end_column

    def read(self, file_path):
        if not os.path.isfile(file_path):
            raise ValueError("Error: No such file: '{}'".format(file_path))

        with open(file_path) as file:
            result = []
            for i, line in enumerate(file.readlines()):
                if i in range(self.start_line, self.end_line + 1):
                    result.append(line)

            result[-1] = result[-1][:self.end_column]
            result[0] = result[0][self.start_column:]

            result = ''.join(result)
            result = ' '.join(result.split())
            return result

        return None

    @staticmethod
    def from_cindex_extent(extent):
        return Extent(extent.start.line - 1,
                      extent.start.column - 1,
                      extent.end.line - 1,
                      extent.end.column - 1)
