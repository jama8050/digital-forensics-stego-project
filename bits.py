def num_bits(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


# Get an 8 character long binary representation of an integer n with spaces every 2 characters
def get_bin(n):
    s = format(n, '08b')
    for i in range(len(s) - 2, 0, -2):
        s = s[:i] + ' ' + s[i:]
    return s


# test_bit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
def test_bit(int_type, offset):
    mask = 1 << offset
    return int_type & mask


# set_bit() returns an integer with the bit at 'offset' set to 1.
def set_bit(int_type, offset):
    mask = 1 << offset
    return int_type | mask


# clear_bit() returns an integer with the bit at 'offset' cleared.
def clear_bit(int_type, offset):
    mask = ~(1 << offset)
    return int_type & mask
