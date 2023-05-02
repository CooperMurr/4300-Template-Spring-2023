import re

def add_escape_chars(input_string):
    special_chars = ['\\', '\'', '\"', '\a', '\b', '\f', '\n', '\r', '\t', '\v']
    output_string = ''
    for char in input_string:
        if char in special_chars:
            output_string += '\\' + char
        elif re.match(r'[^\x00-\x7F]', char):
            output_string += '\\u{:04x}'.format(ord(char))
        else:
            output_string += char
    return output_string

text = "i ha't this"
print(add_escape_chars(text))