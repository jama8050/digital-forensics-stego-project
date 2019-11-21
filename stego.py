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


# Append the secret message to a file
def append(carrier_obj, message):
    carrier_name = carrier_obj.name
    message_to_write = START_MARKER + str.encode(message, ENCODING) + END_MARKER
    last_dot = carrier_name.rfind('.')
    new_name = carrier_name[:last_dot] + EMBED_STR + carrier_name[last_dot:]

    with carrier_obj as image, open(new_name, 'wb') as new_image:
        data = image.read()
        # Check if provided carrier is a PNG
        if data[:len(PNG_HEADER)] != PNG_HEADER or data[len(data) - len(PNG_FOOTER):] != PNG_FOOTER:
            raise ArgumentTypeError('Provided carrier file could not be validated as a PNG.')

        new_data = data + message_to_write
        new_image.write(new_data)

    carrier_obj.close()

    file_metadata("Original carrier file information:", carrier_name, data)
    file_metadata("Modified carrier file information:", new_name, new_data)


# Extract the secret message
def extract(carrier_obj, output_object):
    carrier_name = carrier_obj.name
    with carrier_obj as image:
        data = image.read()
    carrier_obj.close()

    # Locate message via custom magic numbers
    start_index = data.rfind(START_MARKER)
    end_index = data.rfind(END_MARKER)

    if start_index == -1 or end_index == -1:
        raise RuntimeError('Starting and/or ending magic numbers could not be found in file "{}"'.format(carrier_name))
    else:
        file_metadata("Secret carrier file information:", carrier_name, data)

    # decoded, secret message
    str_return = data[start_index + len(START_MARKER):end_index]

    with output_object:
        output_object.write(str_return)
        file_metadata("Extracted file information:", output_object.name, str_return)
    output_object.close()

    return str_return.decode(ENCODING)


# Sets up argument parsing with some error checking
def init():
    # Setup argument parsing
    parser = ArgumentParser(description="Steganography embedding/extracting program in Python 3.7",
                            epilog="Credit to Jacob Malcy")

    # Setup -s and -e as mutually exclusive, but one of them is required
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-s", "--secret", help="Specify the hidden message to embed (enables embedding).")
    group.add_argument("-e", "--extract-to", help="Enable extraction mode, specify the file to write the message to.",
                       type=FileType('wb'))
    parser.add_argument("carrier", help="A PNG image that acts as the carrier file.", type=FileType('rb'))
    parsed = parser.parse_args()

    return parsed


def main():
    parsed = init()

    if parsed.secret:
        # In insert mode
        append(parsed.carrier, parsed.secret)
    else:
        # in extract mode
        print('Secret message: "{}"'.format(extract(parsed.carrier, parsed.extract_to)))


if __name__ == "__main__":
    main()
