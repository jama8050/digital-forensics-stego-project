# Digital Forensics Steganography Project
A basic steganography embedding/extracting program built with Python 3.7.

## Features
* Embedding of a message in a carrier PNG file
* Extraction of a secret message from the carrier file.
* Printing basic file statistics such as:
    * File MD5 hash
    * File size (currently in bytes)

## Usage
To run see usage information, run `python3.7 stego.py --help`

## Limitations
* The program is currently restricted to UTF-8 encoded secret messages.

## Implementation Methodology
This is a _very_ basic implementation of steganography (if you can even call it that)
where the provided secret message is appended to the carrier file.
The message is given a custom "magic number" to add before the message and a different one for after the message. These "magic numbers" are used to locate the secret message during the extraction phase.

## Future Plans
* Encoding independence 
* Implement a better stego algorithm.
* Print file sizes in KB, MB, GB, etc.

## Purpose
This project is an assignment for CYBR-5830-004 Fall 2019 at CU Boulder.

## Credit
This project is developed by Jacob Malcy.

## License
MIT
