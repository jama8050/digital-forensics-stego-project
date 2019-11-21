#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
from hashlib import md5
from bits import test_bit, set_bit, clear_bit
from png import PNG

ENCODING = 'utf-8'
VERBOSE = False


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
        max_message_size = int.from_bytes(b'\xff\xff\xff\xff', byteorder='big')  # Max size that can fit in IEND size
        if len(message_numbers) > max_message_size:
            raise RuntimeError('Message too big, sorry')

        # two bits of each character go to different color value (CV)
        elif int.from_bytes(carrier_obj.get_chunk_by_type(b'PLTE').size, byteorder='big') < len(message_numbers) * 4:
            # TODO: Going to have to add tRNS chunk if it doesn't exist
            print('bad')
            return carrier_obj
        else:
            # Index of which color value we're looking at
            color_index = 0
            for num in message_numbers:  # for each character in the secret message
                for char_bit_index in range(7, -1, -2):  # starting from most sig bit in num to least
                    # current RGB value of interest
                    plte_index, plte_chunk = carrier_obj.get_chunk_by_type(b'PLTE', bool_return_index=True)
                    current_color_value = plte_chunk.data[color_index]

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
                    carrier_obj.index_data(b'PLTE', color_index, value_to_set)
                    color_index += 1

            # FIXME: Storing message length in size of IEND chunk is stupid easy to detect
            # To keep track of the secret message's length, the message length is stored in the size of the IEND chunk
            message_byte_len = len(message_numbers).to_bytes(4, byteorder='big')
            iend_index, iend_chunk = carrier_obj.get_chunk_by_type(b'IEND', bool_return_index=True)
            carrier_obj.chunks[iend_index].size = message_byte_len
            return carrier_obj


# Extract the secret message
def extract(carrier_obj):
    secret_size = carrier_obj.get_chunk_by_type(b'IEND').int_size()
    plte_index, plte_chunk = carrier_obj.get_chunk_by_type(b'PLTE', bool_return_index=True)
    chars = [0] * secret_size

    color_index = 0

    for char_index in range(0, secret_size):  # for each character in the secret message
        for char_bit_offset in range(7, -1, -2):  # starting from most sig bit in num to least
            # current RGB value of interest
            current_color_value = plte_chunk.data[color_index]

            # first bit setup
            if test_bit(current_color_value, 1) == 0:
                value_to_set = clear_bit(chars[char_index], char_bit_offset)
            else:
                value_to_set = set_bit(chars[char_index], char_bit_offset)

            # second bit setup
            if test_bit(current_color_value, 0) == 0:
                value_to_set = clear_bit(value_to_set, char_bit_offset - 1)
            else:
                value_to_set = set_bit(value_to_set, char_bit_offset - 1)

            # Change palette value, modifying the two least significant bits
            chars[char_index] = value_to_set
            color_index += 1

    str_return = b''.join([str.encode(chr(n), ENCODING) for n in chars])
    return str_return


# Sets up argument parsing with some error checking
def init():
    global VERBOSE

    # Setup argument parsing
    parser = ArgumentParser(description="Steganography embedding/extracting program in Python 3.7",
                            epilog="Credit to Jacob Malcy")

    parser.add_argument('-v', '--verbose',
                        help='Enable verbose information (mainly for debugging).',
                        action='store_true',
                        default=False)

    parser.add_argument("-s", "--secret", help="Specify the hidden message to embed (enables insert mode).")
    parser.add_argument("carrier", help="A PNG image that acts as the carrier file.", type=FileType('rb'))
    parser.add_argument("output_file",
                        help="Specifies the file to export in insert mode or the file to extract to in extraction mode",
                        type=FileType('wb'))
    parsed = parser.parse_args()

    VERBOSE = parsed.verbose

    return parsed


def main():
    parsed = init()

    # In insert mode
    with parsed.carrier as image:
        data = image.read()
    original_image = PNG(data, verbose=VERBOSE)

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
