#!/usr/bin/python


class StringWithBrackets:
    def __init__(self, string):
        self.string = string
        self.brackets_dict = {'(': ')', '{': '}', '<': '>', '[': ']'}

    def find_any_of_brackets(self, brackets, bracket_rank=1, start_pos=0):
        if bracket_rank < 1:
            raise ValueError("Bracket rank starts from 1")
            return -1

        if 0 > start_pos or start_pos >= len(self.string):
            return -1

        rank = 0

        open_bracket_stack = []
        for pos, sym in enumerate(self.string[start_pos:], start_pos):
            is_opened_bracket = sym in self.brackets_dict.keys()
            is_closed_bracket = sym in self.brackets_dict.values()

            if is_opened_bracket or is_closed_bracket:
                if is_opened_bracket:
                    rank += 1
                    open_bracket_stack.append(sym)

                if rank == bracket_rank and sym in brackets:
                    return pos

                if is_closed_bracket:
                    rank -= 1
                    if len(open_bracket_stack) == 0:
                        raise IndexError("String '{}' is unbalanced starting from pos {}. "
                                         "Extra back bracket '{}' at {}".format(
                                             self.string, start_pos, sym, pos))
                        return -1

                    last_open_bracket = open_bracket_stack.pop()
                    corresponding_back_bracket = self.brackets_dict[last_open_bracket]
                    if corresponding_back_bracket != sym:
                        raise IndexError(
                            "Closed bracket '{}' at pos {} correspond last open bracket '{}' one in"
                            " string '{}' starting from pos {}".format(
                                sym, pos, last_open_bracket, self.string, start_pos))

                        return -1

        if len(open_bracket_stack) > 0:
            raise IndexError("String '{}' is unbalanced starting from pos {}. There are extra "
                             "opened brackets: {}".format(self.string, start_pos,
                                                          open_bracket_stack))
            return -1

        return -1
