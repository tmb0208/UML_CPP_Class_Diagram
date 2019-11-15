#!/usr/bin/python


def find_closing_bracket(string, bracket, start_pos=0,
                         front_brackets=["(", "{", "<", "["], back_brackets=[")", "}", ">", "]"]):
    balance = 0
    for pos, sym in enumerate(string[start_pos:], start_pos):
        if sym in front_brackets:
            balance += 1
        elif sym in back_brackets:
            balance -= 1
            if balance < 0:
                raise IndexError(
                    "String '{}' is unbalanced starting from {}. Extra back bracket '{}' at {}",
                    start_pos, string, sym, pos)
                return -1

            if balance == 0 and sym == bracket:
                return pos

    if balance > 0:
        raise IndexError(
            "String '{}' is unbalanced starting from {}. There are extra front brackets")

    return -1
