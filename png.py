from binascii import crc32

_PNG_HEADER = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
_PNG_FOOTER = b'IEND\xae\x42\x60\x82'
CRITICAL_CHUNKS = (b'IHDR', b'PLTE', b'IDAT', b'IEND')
ANCILLARY_CHUNKS = (b'bKGD', b'cHRM', b'dSIG', b'eXIF', b'gAMA', b'hIST', b'iCCP', b'iTXt',
                    b'pHYs', b'sBIT', b'sPLT', b'sRGB', b'sTER', b'tEXt', b'tIME', b'tRNS', b'zTXt')


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
        self.__encoding__ = 'utf-8'
        if data[:len(_PNG_HEADER)] != _PNG_HEADER or data[len(data) - len(_PNG_FOOTER):] != _PNG_FOOTER:
            raise Exception('Valid PNG header and/or footer not found')

        self.__split_chunks__(data)
        header_chunk = self.get_chunk_by_type(b'IHDR')
        meta_info = header_chunk.data

        # Process metadata, converting bytes to ints
        self.width = int.from_bytes(meta_info[0:4], byteorder='big')
        self.height = int.from_bytes(meta_info[4:8], byteorder='big')
        self.bit_depth = int.from_bytes(meta_info[8:9], byteorder='big')
        self.color_type = int.from_bytes(meta_info[9:10], byteorder='big')
        self.compression_method = int.from_bytes(meta_info[10:11], byteorder='big')
        self.filter_method = int.from_bytes(meta_info[11:12], byteorder='big')
        self.interlace_method = int.from_bytes(meta_info[12:13], byteorder='big')

        self.__validate_chunks__()

        if self.color_type == 0 or self.color_type == 4:
            raise Exception('Grayscale images currently unsupported')

        # Metadata verbose printing
        if self.verbose is True:
            print("Image width: {}px".format(self.width))
            print("Image height: {}px".format(self.height))
            print("Image bit depth: {}-bit".format(self.bit_depth))
            print("Image color type: {}".format(self.color_type))
            print("Image compression method: {}".format(self.compression_method))
            print("Image filter method: {}".format(self.filter_method))
            print("Image interlace method: {}".format(self.interlace_method))

    def get_chunk_by_type(self, chunk_type, bool_return_index=False):
        return_index = -1
        return_chunk = None

        for index, chunk in enumerate(self.chunks):
            if chunk.type == chunk_type:
                return_index = index
                return_chunk = chunk
                break

        # If we complete the for loop, we never found the chunk we were looking for
        if bool_return_index is True:
            return return_index, return_chunk
        else:
            return return_chunk

    def index_data(self, select_chunk_type, index, new_value, num_bytes=1):
        chunk_index, chunk_data = self.get_chunk_by_type(select_chunk_type, bool_return_index=True)
        before_current = self.chunks[chunk_index].data[:index]
        after_current = self.chunks[chunk_index].data[index + num_bytes:]
        self.chunks[chunk_index].data = before_current + new_value.to_bytes(num_bytes, byteorder='big') + after_current

    # Split PNG data up into chunks, categorize them by critical, ancillary, or unknown,
    # and return a list of all chunks + the indexes where each chunk was found
    # Format for returned chunks is [chunk size, chunk type, chunk data, CRC-32]
    def __split_chunks__(self, data):
        self.chunks = []

        # skip PNG starting magic number
        i = len(_PNG_HEADER)

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
                    print('Critical chunk "{}" found at byte-index {}!'.format(chunk_type.decode(self.__encoding__), i))
                elif chunk_type in ANCILLARY_CHUNKS:
                    print(
                        'Ancillary chunk "{}" found at byte-index {}!'.format(chunk_type.decode(self.__encoding__), i))

            if chunk_type not in CRITICAL_CHUNKS and chunk_type not in ANCILLARY_CHUNKS:
                raise RuntimeWarning(
                    'Unknown chunk type "{}" found at byte-index {}'.format(chunk_type.decode(self.__encoding__), i))

            # Build chunk_indexes list
            if self.get_chunk_by_type(chunk_type) is not None:
                raise RuntimeError('Chunk of type {} already exists'.format(chunk_type))

            i += 4

            chunk_data = data[i:i + chunk_size]
            new_chunk.data = chunk_data
            i += chunk_size

            original_crc32 = data[i:i + 4]
            new_chunk.crc32 = original_crc32
            i += 4
            self.chunks.append(new_chunk)

        if self.verbose is True:
            print("PNG split into {} chunks (counting header and footer)".format(len(self.chunks)))

    # Called when reading and exporting to validate chunk counts
    def __validate_chunks__(self):
        for chunk_type in (b'IHDR', b'IDAT', b'IEND'):
            num_chunk = self.get_chunk_by_type(chunk_type)

            if num_chunk is None:
                str_version = chunk_type.decode(self.__encoding__)
                raise RuntimeError('No {} chunk detected in PNG'.format(str_version))

        # Special case
        if self.color_type == 3:
            num_chunk = self.get_chunk_by_type(b'PLTE')
            if num_chunk == -1:
                raise RuntimeError('No {} chunk detected in PNG'.format(num_chunk.type.decode(self.__encoding__)))

    # export current data to new file
    def export_image(self):
        self.__validate_chunks__()
        return _PNG_HEADER + b''.join([chunk.output_chunk() for chunk in self.chunks])


# A test of the PNG & Chunk classes by incrementing all green values in every pixel in a test image by 18 (max 255)
def test_main():
    with open('test.png', 'rb') as image:
        data = image.read()
    newPNG = PNG(data, verbose=True)

    color_name = 'g'
    color_to_change = 1

    palette_index, palette_chunk = newPNG.get_chunk_by_type(b'PLTE', bool_return_index=True)

    for color_index in range(1, int.from_bytes(palette_chunk.size, byteorder='big'), 3):
        current_value = newPNG.chunks[palette_index].data[color_index]

        if current_value == 255:
            continue
        print("Original {} value = {}".format(color_name, current_value))

        increment = 18
        if increment + current_value < 255:
            new_value = increment + current_value
        else:
            new_value = 255

        before_current = newPNG.chunks[palette_index].data[:color_index]
        after_current = newPNG.chunks[palette_index].data[color_index + 1:]
        newPNG.chunks[palette_index].data = before_current + new_value.to_bytes(1, byteorder='big') + after_current

        print("New {} value = {}".format(color_to_change, new_value))

        assert (current_value < new_value), 'Decrement failed'

    with open('new.png', 'wb') as new_image:
        new_image.write(newPNG.export_image())


if __name__ == '__main__':
    test_main()
