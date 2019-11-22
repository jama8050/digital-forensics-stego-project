# Digital Forensics Steganography Project
A basic PNG steganography embedding/extracting program built with Python 3.7.

## Features
* Embedding of a message in a carrier PNG file.
* Extraction of a secret message from the carrier file.
* Printing basic file statistics such as:
    * File MD5 hash
    * File size (currently in bytes)
    * Image dimensions
    * Image bit-depth
* Works with 16-bit or 8-bit images as well as images with either the TrueColor or Indexed color types.

## Usage
To run see usage information, run `python3.7 stego.py --help`

### Example Usage
```
# Embedding the message "my secret message" in carrier.png and exporting it to modified.png
python3.7 stego.py -s "my secret message" carrier.png modified.png

# Extracting the hidden message in modified.png and exporting it to extracted_msg.txt
python3.7 stego.py modified.png extracted_msg.txt
```

## Limitations
* The program is currently restricted to UTF-8 encoded secret messages.
* Only works with PNG files and will raise an exception when provided otherwise.
* Grayscale PNG files do **NOT** work with this program.

## Implementation Methodology
This is a _very_ basic implementation of steganography (if you can even call it that)
where the provided secret message is appended to the carrier file.
The message is given a custom "magic number" to add before the message and a different one for after the message. These "magic numbers" are used to locate the secret message during the extraction phase.

## Future Plans
* Adapt images to export to a similar state to what they started with.
* Encoding independence.
* Implement a better stego algorithm.
* Print file sizes in KB, MB, GB, etc.
* Grayscale images
* Support for channel sizes of 1, 2, and 4 bits for Indexed color types.

## Purpose
This project is an assignment for CYBR-5830-004 Fall 2019 at CU Boulder.

## Credit
This project is developed by Jacob Malcy.

## License
MIT
