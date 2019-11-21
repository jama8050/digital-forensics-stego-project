#!/usr/bin/env python3

from argparse import ArgumentParser, FileType, ArgumentTypeError
from hashlib import md5
from _md5 import md5
from png import PNG
from bits import test_bit, set_bit, clear_bit, get_bin

PNG_HEADER = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
PNG_FOOTER = b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'
ENCODING = 'utf-8'
CRITICAL_CHUNKS = (b'IHDR', b'PLTE', b'IDAT', b'IEND')
ANCILLARY_CHUNKS = (b'bKGD', b'cHRM', b'dSIG', b'eXIF', b'gAMA', b'hIST', b'iCCP', b'iTXt',
                    b'pHYs', b'sBIT', b'sPLT', b'sRGB', b'sTER', b'tEXt', b'tIME', b'tRNS', b'zTXt')
EMBED_STR = "_embedded"  # Add onto the end of a file name that we modify

# The following numbers were randomly generated
START_MARKER = b'\x4f\x85\x61\x3a\x57\x41\x1d\xea\xc8\xa8'  # Custom start marker
END_MARKER = b'\x4f\x85\x61\x3a\x57\x41\x1d\xa8\xc8\xea'  # Custom end marker (start_marker with last 3 bytes reversed)


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
            for num in message_numbers:
                for char_bit_index in range(7, -1, -2):
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

                    carrier_obj.set_palette(palette_index, color_index, value_to_set)

                    if color_index == 2:
                        palette_index += 1
                        color_index = 0
                    else:
                        color_index += 1

            message_byte_len = len(message_numbers).to_bytes(4, byteorder='big')
            carrier_obj.chunks[carrier_obj.chunk_indexes[b'IEND'][0]].size = message_byte_len
            return carrier_obj
    # TODO: Implement file metadata calls
    # file_metadata("Original carrier file information:", carrier_name, data)
    # file_metadata("Modified carrier file information:", new_name, new_data)


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

    str_return = ''.join([chr(n) for n in chars])
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
        original_image = insert(original_image, parsed.secret)

        # After finished parsing, output file
        with parsed.output_file as output_file:
            output_file.write(original_image.export_image())
    else:
        # in extract mode
        message = extract(original_image)
        print('Secret message: "{}"'.format(message))


if __name__ == "__main__":
    main()
