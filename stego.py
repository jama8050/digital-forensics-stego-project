#!/usr/bin/env python3

from argparse import ArgumentParser
from hashlib import md5
from _md5 import md5
from os import path


def init():
    # Setup argument parsing
    parser = ArgumentParser(description="Steganography embedding/extracting program in Python 3.7",
                            epilog="Credit to Jacob Malcy")

    parser.add_argument("-i", "--insert", help="Embed the specified file.", default=False)
    parser.add_argument("carrier", help="A JPEG image that acts as the carrier file.")
    parsed = parser.parse_args()

    # Check carrier existence
    if path.isfile(parsed.carrier) is False:
        raise FileNotFoundError('File "{}" could not be found!'.format(parsed.carrier))

    # Check file to embed existence
    if parsed.insert is not False and path.isfile(parsed.insert) is False:
        raise FileNotFoundError('File "{}" could not be found!'.format(parsed.insert))

    return parsed


def main():
    parsed = init()

    if parsed.insert is not False:
        # In insert mode
        pass


if __name__ == "__main__":
    main()
