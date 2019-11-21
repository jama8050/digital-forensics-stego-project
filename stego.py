#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
from hashlib import md5
from _md5 import md5
from png import PNG
from bits import test_bit, set_bit, clear_bit

ENCODING = 'utf-8'


# Given 'file.read()' data of a file and the title to start with, print out basic file information
def file_metadata(title, file_name, data):
    print(title)
    print('\tFile Name: "{}"'.format(file_name))
    print('\tFile Size: {}B'.format(len(data)))
    print('\tMD5 Hash: {}'.format(md5(data).hexdigest()))


# Insert the secret message to the carrier file
def insert(carrier_obj, message):
    message_numbers = [ord(c) for c in message]  # Get int representation of each char in message

    if carrier_obj.color_type == 3:  # Indexed
        # two bits of each character go to different color value (CV)
        if len(carrier_obj.get_chunk_by_type(b'PLTE')[0].data) < len(message_numbers) * 3:
            # TODO: Going to have to add tRNS chunk if it doesn't exist
            print('bad')
            return carrier_obj
        else:
            # Do LSB on the palette values
            if carrier_obj.verbose is True:
                print('We\'ll be able to fit the message in the PLTE!')

            # Where we are in the palette
            palette_index = 0

            # which color value we're looking at
            color_index = 0
            for num in message_numbers:  # for each character in the secret message
                for char_bit_index in range(7, -1, -2):  # starting from most sig bit in num to least
                    # current RGB value of interest
                    current_color_value = carrier_obj.palette[palette_index][color_index]

                    # first bit setup
                    if test_bit(num, char_bit_index) == 0:
                        value_to_set = clear_bit(current_color_value, 1)
                    else:
                        value_to_set = set_bit(current_color_value, 1)

                    # second bit setup
                    if test_bit(num, char_bit_index - 1) == 0:
                        value_to_set = clear_bit(value_to_set, 0)
                    else:
                        value_to_set = set_bit(value_to_set, 0)

                    # Change palette value, modifying the two least significant bits
                    carrier_obj.set_palette(palette_index, color_index, value_to_set)

                    # If we just changed a green value, move to red value of next pixel. Else, move to next color
                    if color_index == 2:
                        palette_index += 1
                        color_index = 0
                    else:
                        color_index += 1

            # To keep track of the secret message's length, the message length is stored in the size of the IEND chunk
            # FIXME: Storing message length in size of IEND chunk is stupid easy to detect
            message_byte_len = len(message_numbers).to_bytes(4, byteorder='big')
            carrier_obj.chunks[carrier_obj.chunk_indexes[b'IEND'][0]].size = message_byte_len
            return carrier_obj


# Extract the secret message
def extract(carrier_png):
    secret_size = carrier_png.get_chunk_by_type(b'IEND')[0].int_size()
    plte = carrier_png.palette
    chars = [0] * secret_size

    pixel_index = 0
    rgb_index = 0
    chars_index = 0
    char_sub_index = 7

    while chars_index < secret_size:
        n = plte[pixel_index][rgb_index]
        first_bit = test_bit(n, 1)
        second_bit = test_bit(n, 0)

        if first_bit == 0:
            chars[chars_index] = clear_bit(chars[chars_index], char_sub_index)
        else:
            chars[chars_index] = set_bit(chars[chars_index], char_sub_index)

        if char_sub_index == 0:
            chars_index += 1
            char_sub_index = 7
        else:
            char_sub_index -= 1

        if second_bit == 0:
            chars[chars_index] = clear_bit(chars[chars_index], char_sub_index)
        else:
            chars[chars_index] = set_bit(chars[chars_index], char_sub_index)

        if rgb_index == 2:
            rgb_index = 0
            pixel_index += 1
        else:
            rgb_index += 1

        if char_sub_index == 0:
            chars_index += 1
            char_sub_index = 7
        else:
            char_sub_index -= 1

    str_return = b''.join([str.encode(chr(n), ENCODING) for n in chars])
    return str_return


# Sets up argument parsing with some error checking
def init():
    # Setup argument parsing
    parser = ArgumentParser(description="Steganography embedding/extracting program in Python 3.7",
                            epilog="Credit to Jacob Malcy")

    parser.add_argument("-s", "--secret", help="Specify the hidden message to embed (enables insert mode).")
    parser.add_argument("carrier", help="A PNG image that acts as the carrier file.", type=FileType('rb'))
    parser.add_argument("output_file",
                        help="Specifies the file to export in insert mode or the file to extract to in extraction mode",
                        type=FileType('wb'))
    parsed = parser.parse_args()

    return parsed


def main():
    parsed = init()

    # In insert mode
    with parsed.carrier as image:
        data = image.read()
    original_image = PNG(data, verbose=True)

    if parsed.secret:
        modified_image = insert(original_image, parsed.secret)
        output_data = modified_image.export_image()
    else:
        # in extract mode
        output_data = extract(original_image)

        print('Secret message: "{}"'.format(output_data.decode(ENCODING)))

    # After finished parsing, output file
    with parsed.output_file as output_file:
        output_file.write(output_data)

    # Print file statistics
    file_metadata("Original file information:", parsed.carrier.name, data)
    file_metadata("Exported file information:", parsed.output_file.name, output_data)


if __name__ == "__main__":
    main()
