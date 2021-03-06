"""
Overview and Description
========================
This module determines whether ram is being run in
the console or the command line and verifies the ram
file is in the correct format and exists. It then creates
a nested structure of the code in the file using Block.

Copyright and Usage Information
===============================
All forms of distribution of this code, whether as given or with any changes,
are expressly prohibited.
This file is Copyright (c) 2021 Will Assad, Zain Lakhani,
Ariel Chouminov, Ramya Chawla.
"""
from typing import Union

from syntaxtrees.abs import Module
from parsing.parsing import Block, Line

from exceptions import RamFileNotFoundException, RamGeneralException, RamException


def read_file_as_list(file_path: str) -> list[Union[Line, Block]]:
    """ Read a file containing Ram code and return its contents
        as a list of Blocks and Lines.
    """
    try:
        reader = open(file_path, 'r')
    except FileNotFoundError:
        # Raise exception if file is not found
        raise RamFileNotFoundException(file_path)
    else:
        # create a list of tuples containing each line and its line number.
        lines = reader.readlines()
        tupled_lines = [(lines[index].strip(), index + 1) for index in range(len(lines))]

        return process_ram(tupled_lines)


def process_ram(file_lines: list) -> list[Union[Line, Block]]:
    """ Takes in the lines of a Ram file as a list of tuples
        in the form [(<line>, <line_number>), ...]
        and returns a list that correctly nests blocks.
        For example, with following lines of Ram Code:
        1  loop with j from (15) to (var1) {
        2      loop with k from 1 to 2 {
        3          display j + k
        4      }
        5      display j
        6  }
        7 reset integer var1 to 4
        the call to this function would look like:
        >>> process_ram([('loop with j from (15) to (var1) {', 1),
        >>> ... ('loop with k from 1 to 2 {', 2), ('display j + k', 3), ('}', 4),
        >>> ... ('display j', 5), ('}', 6)])
        [Block([('loop with j from (15) to (var1) {', 1), Block([('loop with k from 1 to 2 {', 2),
        Line('display j + k', 3), ('}', 4)]), Line('display j', 5), ('}', 6)]),
        Line('reset integer var1 to 4', 8)]
        Note the nesting of Blocks and Lines ^ and how empty lines are ignored.
        As another example, take the following lines of Ram code:
        1  if (var1) is (0) {
        2      reset integer x to 4 * 3
        3      display 'The End'
        4  } else if (var1) is (15) {
        5      if (y + 2) is (x) {
        6          reset integer y to 2
        7          display 'Reset'
        8      }
        9      display 'Hello World!'
        10 }
        and this function would be called this way:
        >>> process_ram([('if (var1) is (0) {', 1), ('reset integer x to 4 * 3', 2),
        >>> ... ('display "The End"', 3), ('} else if (var1) is (15) {', 4),
        >>> ... ('if (y + 2) is (x) {', 5), ('reset integer y to 2' , 6),
        >>> ... ('display "Reset"', 7), ('}', 8), ('display "Hello World!"', 9), ('}', 10)])
        [Block([('if (var1) is (0) {', 1), Line('set integer x to 4 * 3', 2),
        Line('display "The End"', 3), ('} else if (var1) is (15) {', 4),
        Block([('if (y + 2) is (x) {', 5), Line('reset integer y to 2', 6),
        Line('display "Reset"', 7), ('}', 8)]), Line('display "Hello World!"', 9),
        ('}', 10) ]]
    """
    # Truncate empty lines and lines with comments
    file_lines_2 = [line for line in file_lines if line[0] != '' and line[0][0] != '%']
    return create_blocks(file_lines_2, 1, [])[0]


def create_blocks(file_lines, line_number, visited: list):
    """ Parses lines into blocks that hold each line's child
    """
    contents = []

    for line_index in range(line_number - 1, len(file_lines)):
        if file_lines[line_index][1] not in visited:
            visited.append(file_lines[line_index][1])

            if '{' in file_lines[line_index][0]:
                if '}' in file_lines[line_index][0]:
                    contents.append((file_lines[line_index][0], file_lines[line_index][1]))
                    continue

                block = Block([(file_lines[line_index][0], file_lines[line_index][1])])
                block.contents, visited = create_blocks(file_lines, line_index + 1, visited)
                block.block += block.contents
                block.evaluate_line()
                contents.append(block)

            elif '}' in file_lines[line_index][0]:
                # end of block
                contents.append(('}', file_lines[line_index][1]))
                break

            else:
                # must create a Line
                line = Line(file_lines[line_index][0], file_lines[line_index][1])
                contents.append(line)

    return (contents, visited)


def main_parser(file_path: str) -> Module:
    """ Take in file_path and process the code.
        Parse each line/block in the file and return a Module.
    """
    # attempt to parse code
    try:
        code = read_file_as_list(file_path)
        statements = []

        # parse each Block and Line in code
        for item in code:
            statements.append(item.parse())

        return Module(statements)
    except Exception as e:
        # raise known RamException
        if isinstance(e, RamException):
            raise e
        raise RamGeneralException(str(e))
