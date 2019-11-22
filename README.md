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
While the idea behind the implementation for this project is Least Significant Bit modification of RGB values,
the implementation is rather complicated. So, let's start with a brief overview of how PNG files work.

### PNG Chunks

##### Chunk Structure
Every PNG is split up into chunks, and each chunk is split into four parts which appear in the following order:
1. `Length` (size 4 bytes): defines how large the `Chunk Data` is
1. `Type` (size 4 bytes): four capital letters that tell the rendering software how to interpret this chunk
(will be discussed more later)
1. `Chunk Data` (size `Length` bytes): the content that the chunk actually holds
1. `CRC` (size 4 bytes): a CRC-32 checksum computed over the `Type` and `Chunk Data`

Each part of a PNG chunk its vital to the functionality of the image as a whole, but what really distinguishes one type
from the next is the `Type`.

##### Chunk Type
Chunk types tell the image rendering software what a chunk does and how to handle it.
Critical chunk types include:
* IHDR: The image header chunk. It contains information such as the color type, image dimensions, and filter type
* PLTE: The image palette chunk. This exists in a specific type of image and contains RGB values for each pixel.
This chunk does not need to exist unless the color type of an image is three.
* IDAT: The image data chunk. This contains information regarding different pixels, but what exactly it contains
differs depending on the image's color type. There can also be multiple IDAT chunks.
* IEND: The image end chunk. This exists in every PNG and it's `Length` is always zero bytes.

There are also chunks known as Ancillary chunks, but none are currently interacted with in this program at this time.

##### Chunk Interpretation
In order to help me process chunks, I created a class named `Chunk` which is located in `png.py`.
The purpose of the `Chunk` class is to streamline the process of storing and modifying chunks that are parsed from
a PNG. Its most important method is `Chunk.export_chunk()`, which combines the stored `size`, `type`, `data`,
and `crc32` attributes into a singular byte-string. Not only that, but the `export_chunk()` method recalculates the
`crc32` value before returning, ensuring that the hash is up to date.

But how is the class used? It is primarily used in another class called `PNG`.

### PNG Class
The goal of this class (just like the `Chunk` class) is to streamline the process of parsing, storing, and modifying
a PNG. Upon being give the binary data of a PNG, the data is parsed and stores the detected chunks in `PNG.chunks`,
which is a list of `Chunk` objects. As the chunks are being parsed, validation is performed to ensure the file being
provided is _actually_ a PNG and that all requisite chunks are present. The `PNG` class offers a few advantages over 
regular functions:
* It is a centralized place to find all information regarding the target PNG
* It offers functions like `get_chunk_by_type` and `set_value_at_index`, which help to simplify the modification and
retrieval of chunk information
* The `export_image` function is provided to make saving the image easy

Now that we have an understanding of the classes in the code, let's move onto the main parts located in `stego.py`

### stego.py
This file contains the core steganography of the project. A basic Least Significant Bit (LSB) algorithm is applied to
specific RGB/RGBA values in either the PLTE or IDAT chunk(s) so that the two least significant bits are modified to
encode the provided message.

##### RGB/RGBA Value Selection
In an attempt to the stealth of hidden messages, the bits modified by the LSB algorithm are spread evenly across the
color-containing chunks (or at least, they're supposed to be). The steps for determining where the values should be
located are as follows:
1. Determine which chunks contain color information based color_type and store the determination in `chunk_to_use`.
    * If the color type is 2 or 6, then RGB(A) values are stored in the IDAT chunk(s)
    * Else, the color_type must be 3 which means the PLTE chunk holds RGB values
    * Other types are restricted in the initialization of the `PNG` object
1. Return the indexes and objects of all chunks with type `chunk_to_use` in the form of a list
    * If the type of the value returned from `get_chunk_by_type` is not a list, make it into one
1. Determine how many bytes in total are spread betweeen the chunks which contain RGB(A) values (`total_avail_bytes`)
1. Create the `percent_const` value which is used to compute the index of where the next LSB modification should go
1. Create the `counter` variable which moves the `percent_const` across the list
1. Since `percent_const` gives us an index in the _total_ bytes, we need to transform it to work with the chunks that
have been split up
    1. Use `determine_chunk_index` to figure out which chunk `percent_const * counter` is in.
    1. Use `determine_byte_index` to figure out which byte `percent_const * counter` is pointing to in the chunk
    determined by `determine_chunk_index`
    1. Retrieve the color value to pass to the LSB algorithm via `current_color_value = current_chunk.data[byte_index]`
1. Pass the determined `current_color_value` into the LSB algorithm

##### LSB Algorithm
The LSB algorithm is pretty much the same for both insertion and extraction, but has some differences in the variables
used:
* Insertion:
    1. For each character in `message`, convert it to an integer and add it to `message_numbers`.
    1. For each number `num` in `message_numbers`, get the first and second least significant bits from it
    (indexed at 0) and do the following:
        1. Use the RGB(A) value selection algorithm to get the values for `current_chunk`, `current_chunk_index`,
        and `current_color_value`
        1. Set the value of the bit located at `char_bit_offset` in `current_color_value` to match the bit located at
        `char_bit_offset` in `num`. Store this as `value_to_set`.
        1. Set the value of the bit located at `char_bit_offset - 1` in `current_color_value` to match the bit located at
        `char_bit_offset - 1` in `num`. Store this as `value_to_set`.
        1. Set byte `byte_index` located in chunk `current_chunk_index` to `value_to_set`
        1. Increment `counter` by one so that the value selection algorithm doesn't stay on the current value.
    1. Store the length of the message as the size of the IEND chunk (since this is ignored upon rendering).
* Extraction:
    1. Retrieve the length of the message from the size of the IEND chunk, store  in `secret_size`.
    1. Create a list `chars` of size `secret_size` which is initialized to all zeros. Each value will represent a
    different character from the message.
    1. Loop through the indexes of the `chars` list as `char_index` and do the following:
        1. Use the RGB(A) value selection algorithm to get the values for `current_chunk`, `current_chunk_index`,
        and `current_color_value`.
        1. Set the value of the bit located at `char_bit_offset` in `chars[char_index]` to match the bit located at
        `char_bit_offset` in `current_color_value`. Store this as `value_to_set`.
        1. Set the value of the bit located at `char_bit_offset - 1` in `chars[char_index]` to match the bit located at
        `char_bit_offset - 1` in `current_color_value`. Store this as `value_to_set`.
        1. Set character `char_index` located in chunk `current_chunk_index` to `value_to_set`.
        1. Increment `counter` by one so that the value selection algorithm doesn't stay on the current value.
    

## Future Plans
* **_UNIT TESTING_**
* Adapt images to export to a similar state to what they originally were.
* Encoding independence.
* Print file sizes in KB, MB, GB, etc.
* Grayscale images
* Support for channel sizes of 1, 2, and 4 bits for Indexed color types.
* Use the Python Image Library (was restricted upon submission).
* Scale the LSB algorithm to modify more than two bits if necessary.

## Purpose
This project is an assignment for CYBR-5830-004 Fall 2019 at CU Boulder.

## Credit
This project is developed by Jacob Malcy.

## License
MIT
