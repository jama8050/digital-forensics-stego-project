#!/usr/bin/env python3

from argparse import ArgumentParser
from hashlib import md5
from _md5 import md5
from os import path

ENCODING = 'utf-8'
EMBED_STR = "_embedded"  # Add onto the end of a file name that we modify

# The following numbers were randomly generated
START_MARKER = b'\x4f\x85\x61\x3a\x57\x41\x1d\xea\xc8\xa8'  # Custom start marker
END_MARKER = b'\x4f\x85\x61\x3a\x57\x41\x1d\xa8\xc8\xea'  # Custom end marker (start_marker with last 3 bytes reversed)
# TODO: Add file statistics function (prints size, name, md5, etc.)

def init():
    # Setup argument parsing
    parser = ArgumentParser(description="Steganography embedding/extracting program in Python 3.7",
                            epilog="Credit to Jacob Malcy")

    parser.add_argument("-s", "--secret", help="Specify the hidden message to embed (enables embedding).")
    parser.add_argument("carrier", help="A JPEG image that acts as the carrier file.")
    parsed = parser.parse_args()

    # Check carrier existence
    if path.isfile(parsed.carrier) is False:
        raise FileNotFoundError('File "{}" could not be found!'.format(parsed.carrier))

    return parsed


def main():
    parsed = init()

    if parsed.secret:
        # In insert mode
        pass


if __name__ == "__main__":
    main()
