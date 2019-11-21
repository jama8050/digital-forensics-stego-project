from binascii import crc32
_PNG_HEADER = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
_PNG_FOOTER = b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'
CRITICAL_CHUNKS = (b'IHDR', b'PLTE', b'IDAT', b'IEND')
ANCILLARY_CHUNKS = (b'bKGD', b'cHRM', b'dSIG', b'eXIF', b'gAMA', b'hIST', b'iCCP', b'iTXt',
                    b'pHYs', b'sBIT', b'sPLT', b'sRGB', b'sTER', b'tEXt', b'tIME', b'tRNS', b'zTXt')


class Pixel:
    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b

    def __getitem__(self, item):
        if item == 0 or item == 'r':
            return self.r
        elif item == 1 or item == 'g':
            return self.g
        elif item == 2 or item == 'b':
            return self.b
        else:
            raise KeyError()

    def __setitem__(self, key, value):
        if isinstance(value, int) is False:
            raise ValueError('Value of the wrong type')
        elif value < 0 or value > 255:
            raise ValueError('Value out of range [0, 255]')
        if key not in ('r', 'g', 'b', 0, 1, 2):
            raise KeyError()

        if key == 0 or key == 'r':
            self.r = value
        elif key == 1 or key == 'g':
            self.g = value
        else:
            self.b = value


class Chunk:
    def __init__(self, init_type=b'', init_data=b''):
        self.size = len(init_data).to_bytes(4, byteorder='big')
        self.type = init_type
        self.data = init_data
        self.crc32 = b''
        self.calculate_crc32()

    def calculate_crc32(self):
        self.crc32 = crc32(self.type + self.data).to_bytes(4, byteorder='big')

    def int_size(self):
        return int.from_bytes(self.size, byteorder='big')

    # Return the chunk as you would see it in a hex editor
    def output_chunk(self):
        self.calculate_crc32()
        return self.size + self.type + self.data + self.crc32

    def __len__(self):
        return len(self.data)


class PNG:
    def __init__(self, data, verbose=False):
        self.verbose = verbose
        self.encoding = 'utf-8'
        if data[:len(_PNG_HEADER)] != _PNG_HEADER or data[len(data) - len(_PNG_FOOTER):] != _PNG_FOOTER:
            raise Exception('Valid PNG header and/or footer not found')

        self.chunks, self.chunk_indexes = self.split_chunks(data)
        meta_info = self.chunks[self.chunk_indexes[b'IHDR'][0]].data

        # Process metadata, converting bytes to ints
        self.width = int.from_bytes(meta_info[0:4], byteorder='big')
        self.height = int.from_bytes(meta_info[4:8], byteorder='big')
        self.bit_depth = int.from_bytes(meta_info[8:9], byteorder='big')
        self.color_type = int.from_bytes(meta_info[9:10], byteorder='big')
        self.compression_method = int.from_bytes(meta_info[10:11], byteorder='big')
        self.filter_method = int.from_bytes(meta_info[11:12], byteorder='big')
        self.interlace_method = int.from_bytes(meta_info[12:13], byteorder='big')

        # Parse PLTE and IDAT chunks
        self.palette = self.parse_palette()
        self.channels = self.parse_idat()

        # Metadata verbose printing
        if self.verbose is True:
            print("PNG header and footer found, splitting chunks...")
            print("Chunk indexes:", self.chunk_indexes)

            print("PLTE chunk size: {}B".format(len(self.chunks[self.chunk_indexes[b'PLTE'][0]].data)))
            print("Number of palette entries:", len(self.palette))

            print("IDAT Size: {}B".format(len(self.channels)))

            print("Image width: {}px".format(self.width))
            print("Image height: {}px".format(self.height))
            print("Image bit depth: {}-bit".format(self.bit_depth))
            print("Image color type: {}".format(self.color_type))
            print("Image compression method: {}".format(self.compression_method))
            print("Image filter method: {}".format(self.filter_method))
            print("Image interlace method: {}".format(self.interlace_method))

    def get_chunk_by_type(self, chunk_type):
        chunk_indexes = self.chunk_indexes[chunk_type]
        return_chunks = [self.chunks[chunk_index] for chunk_index in chunk_indexes]
        return return_chunks

    # Split PNG data up into chunks, categorize them by critical, ancillary, or unknown,
    # and return a list of all chunks + the indexes where each chunk was found
    # Format for returned chunks is [chunk size, chunk type, chunk data, CRC-32]
    def split_chunks(self, data):
        chunks = []
        chunk_indexes = {}
        i = 0
        i += len(_PNG_HEADER)

        # While there are still chunks to parse...
        while i < len(data):
            new_chunk = Chunk()
            size = data[i:i + 4]
            new_chunk.size = size
            chunk_size = new_chunk.int_size()  # Gets current chunk size (in number of bytes)
            i += 4

            chunk_type = data[i:i + 4]
            new_chunk.type = chunk_type
            if self.verbose is True:
                if chunk_type in CRITICAL_CHUNKS:
                    print('Critical chunk "{}" found at byte-index {}!'.format(chunk_type.decode(self.encoding), i))
                elif chunk_type in ANCILLARY_CHUNKS:
                    print('Ancillary chunk "{}" found at byte-index {}!'.format(chunk_type.decode(self.encoding), i))

            if chunk_type not in CRITICAL_CHUNKS and chunk_type not in ANCILLARY_CHUNKS:
                raise RuntimeWarning(
                    'Unknown chunk type "{}" found at byte-index {}'.format(chunk_type.decode(self.encoding), i))

            if chunk_type not in chunk_indexes:
                chunk_indexes[chunk_type] = [len(chunks)]
            else:
                chunk_indexes[chunk_type].append(len(chunks))
            i += 4

            chunk_data = data[i:i + chunk_size]
            new_chunk.data = chunk_data
            i += chunk_size

            original_crc32 = data[i:i + 4]
            new_chunk.crc32 = original_crc32
            i += 4
            chunks.append(new_chunk)

        if self.verbose is True:
            print("PNG split into {} chunks (counting header and footer)".format(len(chunks)))
        return chunks, chunk_indexes

    # ASSUMES COLOR TYPE = INDEXED, BIT-DEPTH = 8
    # Palette not used for color type != (indexed = 3)
    # Returns list of RGB values in the Palette ('PLTE') chunk
    def parse_palette(self):
        plte_chunks = self.get_chunk_by_type(b'PLTE')
        if len(plte_chunks) > 1:
            raise Exception('Multiple PLTE chunks detected')
        elif len(plte_chunks) == 0:
            raise Exception('No PLTE chunks detected')
        plte = plte_chunks[0].data
        palette = []
        for i in range(0, len(plte), 3):  # 3 bytes per color
            r = plte[i]
            g = plte[i + 1]
            b = plte[i + 2]
            entry = [r, g, b]
            palette.append(entry)
        return palette

    # ASSUMES COLOR TYPE = INDEXED, BIT-DEPTH = 8
    # Palette not used for color type != (indexed = 3)
    def parse_idat(self):
        idat_chunks = self.get_chunk_by_type(b'IDAT')
        if len(idat_chunks) > 1:
            raise RuntimeError('Currently unable to parse multiple IDAT chunks.')
        elif len(idat_chunks) == 0:
            raise Exception('No IDAT chunk detected, invalid file')
        elif self.color_type != 3:
            raise RuntimeError('Currently restricted to color_type = 3 (set to {})'.format(self.color_type))

        idat = idat_chunks[0].data

        # 1 byte per channel
        channels = list(idat)
        # Verify indexes parsed correctly
        for v in channels:
            assert(0 <= v < len(self.palette)), "channels contains invalid index " + str(v)
        return channels

    # Used to easily modify palette values
    def set_palette(self, palette_index, color, new_value):
        plte_chunks = self.get_chunk_by_type(b'PLTE')
        color_codes = ('r', 'g', 'b')

        # Error checking block
        if color not in color_codes:
            raise ValueError('Selected color to change must be in {}, given {}'.format(color_codes, color))
        elif not (0 <= new_value <= 255):
            raise ValueError('Color values must be in range [0, 255], given {}'.format(new_value))
        elif len(plte_chunks) == 0:
            raise Exception('No PLTE chunk detected')
        elif len(plte_chunks) > 1:
            raise Exception('More than 1 PLTE chunk detected')

        # Change value stored in palette array
        self.palette[palette_index][color_codes.index(color)] = new_value

        actual_index = (3 * palette_index) + color_codes.index(color)  # Byte offset in chunk

        current_text = plte_chunks[0].data
        # Change chunk value
        self.chunks[self.chunk_indexes[b'PLTE'][0]].data = current_text[:actual_index] + new_value.to_bytes(1, byteorder='big') + current_text[actual_index + 1:]

    # export current data to new file
    def export_image(self):
        return _PNG_HEADER + b''.join([chunk.output_chunk() for chunk in self.chunks])


# A test of the PNG & Chunk classes by incrementing all green values in every pixel in a test image by 18 (max 255)
def test_main():
    with open('test_png.png', 'rb') as image:
        data = image.read()
    newPNG = PNG(data, verbose=True)
    color_to_change = 'g'
    color_index = 1
    for palette_index in range(len(newPNG.palette)):
        current_value = newPNG.palette[palette_index][color_index]
        if current_value == 255:
            continue
        print("Original {} value = {}".format(color_to_change, current_value))

        increment = 18
        if increment + current_value < 255:
            new_value = increment + current_value
        else:
            new_value = 255

        newPNG.set_palette(palette_index, color_to_change, new_value)
        new_value = newPNG.palette[palette_index][color_index]
        print("New {} value = {}".format(color_to_change, new_value))
        assert(current_value < new_value), 'Decrement failed'

    with open('new_png.png', 'wb') as new_image:
        new_image.write(newPNG.export_image())


if __name__ == '__main__':
    test_main()
