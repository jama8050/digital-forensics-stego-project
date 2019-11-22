#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
from hashlib import md5
from bits import test_bit, set_bit, clear_bit, get_bin
from png import PNG

ENCODING = 'utf-8'
VERBOSE = False


# Given 'file.read()' data of a file and the title to start with, print out basic file information
def file_metadata(title, file_name, data):
    print(title)
    print('\tFile Name: "{}"'.format(file_name))
    print('\tFile Size: {}B'.format(len(data)))
    print('\tMD5 Hash: {}'.format(md5(data).hexdigest()))


def determine_chunk_index(chunks, byte_value):
    s = 0

    for i in range(len(chunks)):
        if byte_value < s + chunks[i].int_size():
            return i
        else:
            s += chunks[i].int_size()
    return -1


def determine_byte_index(chunks, byte_value):
    chunk_index = determine_chunk_index(chunks, byte_value)
    bytes_before = sum([chunk.int_size() for chunk in chunks[0:chunk_index]])
    return byte_value - bytes_before


# Insert the secret message to the carrier file
def insert(carrier_obj, message):
    message_numbers = [ord(c) for c in message]  # Get int representation of each char in message

    # Determine where colors are stored and byte_step
    if carrier_obj.color_type == 2:  # TrueColor
        chunk_to_use = b'IDAT'
    elif carrier_obj.color_type == 3:  # Indexed
        chunk_to_use = b'PLTE'
    else:  # TrueColor + Alpha (type 6)
        chunk_to_use = b'IDAT'

    use_chunk_index, use_chunk = carrier_obj.get_chunk_by_type(chunk_to_use, bool_return_index=True)
    if isinstance(use_chunk, list) is False:
        use_chunk_index = [use_chunk_index]
        use_chunk = [use_chunk]

    total_avail_bytes = sum([chunk.int_size() for chunk in use_chunk])

    if len(message_numbers) * 4 > total_avail_bytes:  # one character takes up 4
        raise RuntimeError('Message too big given chunk sizes, sorry')
    else:
        # Determine spread -- assuming 1-Byte per character
        percent_const = int(total_avail_bytes // ((4 * len(message_numbers)) + 1))

    # Given the actual chunk index we start at, determine the index of that chunk in these sublists
    counter = 1
    for num_index, num in enumerate(message_numbers):  # for each character in the secret message
        for char_bit_offset in range(7, -1, -2):  # starting from most sig bit in num to least
            # Index of which color value we're looking at
            chunk_list_index = determine_chunk_index(use_chunk, percent_const * counter)
            byte_index = determine_byte_index(use_chunk, percent_const * counter)
            current_chunk_index = use_chunk_index[chunk_list_index]
            current_chunk = use_chunk[chunk_list_index]

            # current RGB(A) value of interest
            current_color_value = current_chunk.data[byte_index]

            lsb_str = ''
            # first bit setup
            if test_bit(num, char_bit_offset) == 0:
                value_to_set = clear_bit(current_color_value, 1)
                lsb_str += '0'
            else:
                value_to_set = set_bit(current_color_value, 1)
                lsb_str += '1'

            # second bit setup
            if test_bit(num, char_bit_offset - 1) == 0:
                value_to_set = clear_bit(value_to_set, 0)
                lsb_str += '0'
            else:
                value_to_set = set_bit(value_to_set, 0)
                lsb_str += '1'

            if VERBOSE is True:
                print('Current LSB: {}'.format(lsb_str))
                print("Modifying chunk {}, index {} from {} to {}".format(current_chunk_index,
                                                                          byte_index,
                                                                          get_bin(current_color_value),
                                                                          get_bin(value_to_set)))
                print('')

            # Change palette value, modifying the two least significant bits
            carrier_obj.index_data(current_chunk_index, byte_index, value_to_set)

            counter += 1

    # FIXME: Storing message length in size of IEND chunk is stupid easy to detect
    # To keep track of the secret message's length, the message length is stored in the size of the IEND chunk
    message_byte_len = len(message_numbers).to_bytes(4, byteorder='big')
    iend_index, iend_chunk = carrier_obj.get_chunk_by_type(b'IEND', bool_return_index=True)
    carrier_obj.chunks[iend_index].size = message_byte_len
    return carrier_obj


# Extract the secret message
def extract(carrier_obj):
    secret_size = carrier_obj.get_chunk_by_type(b'IEND').int_size()
    chars = [0] * secret_size

    # Determine where colors are stored and byte_step
    if carrier_obj.color_type == 2:  # TrueColor
        chunk_to_use = b'IDAT'
    elif carrier_obj.color_type == 3:  # Indexed
        chunk_to_use = b'PLTE'
    else:  # TrueColor + Alpha (type 6)
        chunk_to_use = b'IDAT'

    use_chunk_index, use_chunk = carrier_obj.get_chunk_by_type(chunk_to_use, bool_return_index=True)
    if isinstance(use_chunk, list) is False:
        use_chunk_index = [use_chunk_index]
        use_chunk = [use_chunk]

    total_avail_bytes = sum([chunk.int_size() for chunk in use_chunk])

    # Determine spread -- assuming 1-Byte per character
    percent_const = int(total_avail_bytes // ((4 * secret_size) + 1))

    counter = 1
    for char_index in range(0, secret_size):  # for each character in the secret message
        for char_bit_offset in range(7, -1, -2):  # starting from most sig bit in num to least
            # Index of which color value we're looking at
            chunk_list_index = determine_chunk_index(use_chunk, percent_const * counter)
            byte_index = determine_byte_index(use_chunk, percent_const * counter)
            current_chunk_index = use_chunk_index[chunk_list_index]
            current_chunk = use_chunk[chunk_list_index]

            if VERBOSE is True:
                print("Checking chunk {}, index {}".format(current_chunk_index, byte_index))

            # current RGB value of interest
            current_color_value = current_chunk.data[byte_index]

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
            counter += 1

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

    if parsed.secret == '-':
        parsed.secret = input('input secret: ')

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
