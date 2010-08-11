"""Use arithmetic coding to compress and decompress files.
************************************************************************

    File    : arcode.py
    Purpose : This file implements a simple class for compressing and
              decompressing files using the arithmetic coding algorithm.
              This implementation is not intended to be the best,
              fastest, smallest, or any other performance related
              adjective.  It is intended produced the same results as
              my ANSI C arithmetic coding library.
    Author  : Michael Dipperstein
    Date    : July 21, 2010

************************************************************************

arcode: A python module that uses arithmetic coding to compress and
        decompress files.
Copyright (C) 2010
      Michael Dipperstein (mdipper@alumni.engr.ucsb.edu)

This file implements the arcode module.

Arcode is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

Arcode is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import bitfile

EOF_CHAR = 256

# number of bits used to compute running code values
PRECISION = 16

# mask to clear the msb of probability values
MSB_MASK = ((1 << (PRECISION - 1)) - 1)

# 2 bits less than precision. keeps lower and upper bounds from crossing
MAX_PROBABILITY = (1 << (PRECISION - 2))


class ArithmeticCodeError(Exception):
    """Exception thrown for errors unique to the ArithmeticCode class.

    This class derives off of the base class Exception to provide
    an error indication for exceptions unique to the ArithmeticCode
    class.

    Methods:
        None.

    Instance Variables:
        None.
    """
    pass


class ArithmeticCode:
    """Methods used to compress/decompress files with arithmetic coding.

    Methods:
        apply_symbol_range - Apply range restrictions of a new symbol to
                             range bounds.
        build_probability_range_list - Fill _ranges with the probability
                                       values for the input file.
        decode_file - Use arithmetic coding to decode a file.
        encode_file - Use arithmetic coding to encode a file.
        get_symbol_from_probability - Undo scaling performed by
                                      apply_symbol_range.
        get_unscaled_code - Get the symbol encoded by a probability.
        initialize_adaptive_probability_range_list - Initialize the
            probability range list for adaptive algorithm.
        initialize_decoder - Initialize the code value and range bounds
                             for encoded input.
        lower - Returns the index of a symbol's lower probability range.
        mask_bit - Sets bit x to 1 in PRECISION sized integer.
        read_encoded_bits - Shift out any bits that unaffected by
                            decoding new symbols.
        read_header - Read header containing symbol probabilities.
        symbol_count_to_probability_ranges - Convert _ranges with symbol
            counts to probability values.
        upper - Returns the index of a symbol's upper probability range.
        write_encoded_bits - Write out any bits that will not be
                             affected by new symbol.
        write_header - Write header containing symbol probabilities.
        write_remaining - Write out remaining bits the after last symbol
                          is encoded.

    Instance Variables:
        _lower - The lower bound of the current probability range.
        _upper - The upper bound of the current probability range.
        _code - The current MSBs of encoded input stream.
        _underflow_bits - The underflow bits from current probabilities.
        _ranges - An array of probability ranges for all symbols.
        _cumulative_prob - The cumulative probability of all ranges.
        _infile - The input stream to encode/decode.
        _outfile - The input stream to encode/decode.
        _static_model - True if a static model is being used.

    """

    def __init__(self, static=True):
        """Constructor for ArithmeticCode class.

        This is the constructor function of the ArithmeticCode class. It
        creates a ArithmeticCode object and initializes all of it's data.

        Arguments:
            static - True if a static model is to be used.

        Return Value(s):
            An initialized ArithmeticCode object.

        Side Effects:
            Data elements are initialized as follows:
            _lower = 0
            _upper = 0xFFFF (all ones)
            _code = 0
            _underflow_bits = 0
            _ranges = all zeros
            _cumulative_prob = 0
            _infile = None
            _outfile = None
            _static_model = static


        Exceptions Raised:
            None.

        """

        self._lower = 0             # lower bound of current code range
        self._upper = 0xFFFF        # upper bound of current code range

        self._code = 0              # current MSBs of encode input stream

        self._underflow_bits = 0    # current underflow bit count

        # The probability lower and upper ranges for each symbol
        self._ranges = [0 for i in xrange(self.upper(EOF_CHAR) + 1)]

        self._cumulative_prob = 0   # cumulative probability  of all ranges

        self._infile = None
        self._outfile = None

        self._static_model = static     # True if encoding with a static model

    @staticmethod
    def mask_bit(x):
        """Sets bit x to 1 in PRECISION sized integer.  (Bit 0 is MSB)

        This is a static method that returns an integer with the
        specified bit set to 1 and all other bits set to 0.
        e.g. mask_bit(3) returns 0001 0000 0000 0000.

        Arguments:
            x - Bit position to set to 1.

        Return Value(s):
            An integer with the specified bit set to 1 and all other
            bits set to 0.

        Side Effects:
            None.

        Exceptions Raised:
            None.

        """

        return (1 << (PRECISION - (1 + x)))

    @staticmethod
    def lower(c):
        """Returns the index of a symbol's lower probability range.

        This is a static method that returns an index into the _ranges
        array where the lower probability range for a symbol is stored.

        Arguments:
            c - The symbol to get the _range index for.

        Return Value(s):
            An index into the _ranges where the lower probability range
            for a symbol c is stored.

        Side Effects:
            None.

        Exceptions Raised:
            None.

        """

        if type(c) == str:      # handle strings
            return ord(c)
        return c

    @staticmethod
    def upper(c):
        """Returns the index of a symbol's upper probability range.

        This is a static method that returns an index into the _ranges
        array where the upper probability range for a symbol is stored.

        Arguments:
            c - The symbol to get the _range index for.

        Return Value(s):
            An index into the _ranges where the upper probability range
            for a symbol c is stored.

        Side Effects:
            None.

        Exceptions Raised:
            None.

        """

        if type(c) == str:      # handle strings
            return ord(c) + 1
        return c + 1

    def encode_file(self, input_file_name, output_file_name):
        """Use arithmetic coding to encode a file.

        This method generates a list of arithmetic code ranges for a
        file and then uses them to write out an encoded version of that
        file.

        Arguments:
            input_file_name - The name of the file to be encoded.
            output_file_name - The name of the file to write the encoded
                               output to.

        Return Value(s):
            None.

        Side Effects:
            An arithmetically encoded output file is created.

        Exceptions Raised:
            ValueError - Raised when an object's input or output file
                         streams are alreay open.

        """

        if (self._infile is not None) or (self._outfile is not None):
            raise ValueError('I/O operation on opened file.')

        if self._static_model:
            # read through input file and compute ranges
            self._infile = open(input_file_name, 'rb')
            self.build_probability_range_list()
            self._infile.seek(0)

            # write header with ranges to output file
            self._outfile = bitfile.BitFile()
            self._outfile.open(output_file_name, 'wb')
            self.write_header()
        else:
            # initialize probability ranges assuming uniform distribution
            self.initialize_adaptive_probability_range_list()

            # open input and output files
            self._infile = open(input_file_name, 'rb')
            self._outfile = bitfile.BitFile()
            self._outfile.open(output_file_name, 'wb')

        # encode file 1 byte at at time
        c = self._infile.read(1)
        while (c != ''):
            self.apply_symbol_range(c)
            self.write_encoded_bits()
            c = self._infile.read(1)

        self._infile.close()
        self.apply_symbol_range(EOF_CHAR)   # encode an EOF
        self.write_encoded_bits()

        self.write_remaining()              # write out least significant bits
        self._outfile.close()

    def build_probability_range_list(self):
        """Fill _ranges with the probability values for the input file.

        This method reads the input file and builds the global list of
        upper and lower probability ranges for each symbol.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The _ranges array is made to contain the probability ranges
            for each symbol.

        Exceptions Raised:
            ArithmeticCodeError - Raised when no input file is opened
                                  for encoding.

        """

        if self._infile is None:
            raise ArithmeticCodeError('No input file opened for encoding.')

        # start with no symbols counted
        count_array = [0 for i in xrange(EOF_CHAR)]

        c = self._infile.read(1)
        while (c != ''):
            count_array[ord(c)] += 1
            c = self._infile.read(1)

        total_count = sum(count_array)

        # rescale counts to be < MAX_PROBABILITY
        if total_count >= MAX_PROBABILITY:
            rescale_value = (total_count / MAX_PROBABILITY) + 1

            for index, value in enumerate(count_array):
                if value > rescale_value:
                    count_array[index] = value / rescale_value
                elif value != 0:
                    count_array[index] = 1

        # copy scaled symbol counts to range list upper range (add EOF)
        self._ranges = [0] + count_array + [1]
        self._cumulative_prob = sum(count_array)

        # convert counts to a range of probabilities
        self.symbol_count_to_probability_ranges()

    def symbol_count_to_probability_ranges(self):
        """Convert _ranges with symbol counts to probability values.

        This method converts the _ranges array containing only symbol
        counts to an array containing the upper and lower probability
        ranges for each symbol.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The _ranges array containing symbol counts in the upper
            field for each symbol is converted to a list of upper and
            lower probability bounds for each symbol.

        Exceptions Raised:
            None.

        """

        self._ranges[0] = 0                     # absolute lower bound is 0
        self._ranges[self.upper(EOF_CHAR)] = 1  # add one EOF character
        self._cumulative_prob += 1

        for c in xrange(EOF_CHAR + 1):
            self._ranges[c + 1] += self._ranges[c]

    def write_header(self):
        """Write header containing symbol probabilities.

        This method writes the value of each symbol contained in the
        encoded file as well as its rescaled number of occurrences.  A
        decoding algorithm may use these numbers to reconstruct the
        probability range list used to encode the file.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            Symbol values and symbol counts are written to the encoded
            file.

        Exceptions Raised:
            ArithmeticCodeError - Raised when no output file is opened
                                  for encoding.

        """

        if self._outfile is None:
            raise ArithmeticCodeError('No output file opened for encoding.')

        previous = 0

        for c in xrange(EOF_CHAR):
            if self._ranges[self.upper(c)] > previous:
                # some of these symbols will be encoded
                self._outfile.put_char(c)
                # calculate symbol count
                previous = (self._ranges[self.upper(c)] - previous)

                # write out PRECISION - 2 bit count
                self._outfile.put_bits_ltom(previous, (PRECISION - 2))

                # current upper range is previous for the next character
                previous = self._ranges[self.upper(c)]

        # now write end of table (zero count)
        self._outfile.put_char(0)
        previous = 0
        self._outfile.put_bits_ltom(previous, (PRECISION - 2))

    def initialize_adaptive_probability_range_list(self):
        """Initialize the probability range list for adaptive algorithm.

        This method builds the initial global list of upper and lower
        probability ranges for each symbol.  This routine is used by
        both adaptive encoding and decoding.  Currently it provides a
        uniform symbol distribution.  Other distributions might be
        better suited for known data types (such as English text).

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The _ranges array is made to contain initial probability
            ranges for each symbol.

        Exceptions Raised:
            None.

        """
        self._ranges = [i for i in xrange(self.upper(EOF_CHAR) + 1)]
        self._cumulative_prob = EOF_CHAR + 1

    def apply_symbol_range(self, symbol):
        """Apply range restrictions of a new symbol to range bounds.

        This method is used for both encoding and decoding.  It applies
        the range restrictions of a new symbol to the current upper and
        lower range bounds of an encoded stream.  If an adaptive model
        is being used, the probability range list will be updated after
        the effect of the symbol is applied.

        Arguments:
            symbol - The symbol to be added to the current code range.

        Return Value(s):
            None.

        Side Effects:
            The current upper and lower range bounds are adjusted to
            include the range effects of adding another symbol to the
            encoded stream.  If an adaptive model is being used, the
            probability range list (_ranges) will be updated.

        Exceptions Raised:
            None.

        """

        range = self._upper - self._lower + 1           # current range

        # scale the upper range of the symbol being coded
        rescaled = self._ranges[self.upper(symbol)] * range
        rescaled /= self._cumulative_prob

        # new upper = old lower + rescaled new upper - 1
        self._upper = self._lower + rescaled - 1

        # scale lower range of the symbol being coded
        rescaled = self._ranges[self.lower(symbol)] * range
        rescaled /= self._cumulative_prob

        # new lower = old lower + rescaled new lower
        self._lower = self._lower + rescaled

        if not self._static_model:
            # add new symbol to model
            self._cumulative_prob += 1
            for i in xrange(self.upper(symbol),  len(self._ranges)):
                self._ranges[i] += 1

            # halve current values if _cumulative_prob is too large
            if self._cumulative_prob >= MAX_PROBABILITY:
                original = 0

                for i in xrange(1, len(self._ranges)):
                    delta = self._ranges[i] - original
                    original = self._ranges[i]

                    if delta <= 2:
                        # prevent probability from being
                        self._ranges[i] = self._ranges[i - 1] + 1
                    else:
                        self._ranges[i] = self._ranges[i - 1] + (delta / 2)

                self._cumulative_prob = self._ranges[self.upper(EOF_CHAR)]

    def write_encoded_bits(self):
        """Write out any bits that will not be affected by new symbol.

        This method attempts to shift out as many code bits as possible,
        writing the shifted bits to the encoded output file.  Only bits
        that will be unchanged when additional symbols are encoded may
        be written out.

        If the n most significant bits of the lower and upper range
        bounds match, they will not be changed when additional symbols
        are encoded, so they may be shifted out.

        Adjustments are also made to prevent possible underflows that
        occur when the upper and lower ranges are so close that encoding
        another symbol won't change their values.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The upper and lower code bounds are adjusted so that they
            only contain bits that may be affected by the addition of a
            new symbol to the encoded stream.

        Exceptions Raised:
            ArithmeticCodeError - Raised when no output file is opened
                                  for encoding.

        """

        if self._outfile is None:
            raise ArithmeticCodeError('No output file opened for encoding.')

        mask_bit_zero = self.mask_bit(0)
        mask_bit_one = self.mask_bit(1)

        while True:
            if (self._upper ^ ~self._lower) & mask_bit_zero:
                # MSBs match, write them to output file
                self._outfile.put_bit((self._upper & mask_bit_zero) != 0)

                # we can write out underflow bits too
                while self._underflow_bits > 0:
                    self._outfile.put_bit((self._upper & mask_bit_zero) == 0)
                    self._underflow_bits -= 1

            elif (~self._upper & self._lower) & mask_bit_one:
                #*******************************************************
                # Possible underflow condition: neither MSBs nor second
                # MSBs match.  It must be the case that lower and upper
                # have MSBs of 01 and 10.  Remove 2nd MSB from lower and
                # upper.
                #*******************************************************
                self._underflow_bits += 1
                self._lower &= ~(mask_bit_zero | mask_bit_one)
                self._upper |= mask_bit_one

                #*******************************************************
                # The shifts below make the rest of the bit removal
                # work.  If you don't believe me try it yourself.
                #*******************************************************
            else:
                return              # nothing left to do

            #***********************************************************
            # Mask off old MSB and shift in new LSB.  Remember that
            # lower has all 0s beyond it's end and upper has all 1s
            # beyond it's end.
            #***********************************************************
            self._lower &= MSB_MASK
            self._lower <<= 1
            self._upper &= MSB_MASK
            self._upper <<= 1
            self._upper |= 0x0001

    def write_remaining(self):
        """Write out remaining bits the after last symbol is encoded.

        This method writes out all remaining significant bits in the
        upper and lower ranges and the underflow bits once the last
        symbol has been encoded.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The remaining significant range bits are written to the
            output file.

        Exceptions Raised:
            ArithmeticCodeError - Raised when no output file is opened
                                  for encoding.

        """

        if self._outfile is None:
            raise ArithmeticCodeError('No output file opened for encoding.')

        mask_bit_one = self.mask_bit(1)
        self._outfile.put_bit((self._lower & mask_bit_one) != 0)

        # write out any unwritten underflow bits
        self._underflow_bits += 1
        for i in xrange(self._underflow_bits):
            self._outfile.put_bit((self._lower & mask_bit_one) == 0)

    def decode_file(self, input_file_name, output_file_name):
        """Use arithmetic coding to decode a file.

        This method opens an arithmetically encoded file, reads it's
        header, and builds a list of probability ranges which it then
        uses to decode the rest of the file.

        Arguments:
            input_file_name - The name of the file to be decoded.
            output_file_name - The name of the file to write the decoded
                               output to.

        Return Value(s):
            None.

        Side Effects:
            An arithmetically encoded file is decoded and written to an
            output file.

        Exceptions Raised:
            ValueError - Raised when an object's input or output file
                         streams are alreay open.

        """

        if (self._infile is not None) or (self._outfile is not None):
            raise ValueError('I/O operation on opened file.')

        # open input and build probability ranges from header in file
        self._infile = bitfile.BitFile()
        self._infile.open(input_file_name, 'rb')

        if self._static_model:
            self.read_header()  # build probability ranges from header in file
        else:
            # initialize probability ranges assuming uniform distribution
            self.initialize_adaptive_probability_range_list()

        # read start of code and initialize bounds
        self.initialize_decoder()

        self._outfile = open(output_file_name, 'wb')

        # decode one symbol at a time
        while True:
            # get the unscaled probability of the current symbol
            unscaled = self.get_unscaled_code()

            # figure out which symbol has the above probability
            c = self.get_symbol_from_probability(unscaled)
            if c == EOF_CHAR:
                # no more symbols
                break

            self._outfile.write(chr(c))

            # factor out symbol
            self.apply_symbol_range(c)
            self.read_encoded_bits()

        self._outfile.close()
        self._infile.close()

    def read_header(self):
        """Read header containing symbol probabilities.

        This method reads the header information stored by write_header.
        The header is then used to build a probability range list
        matching the list that was used to encode the file.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The probability range list, _ranges, is built.

        Exceptions Raised:
            ArithmeticCodeError - Raised when no input file is opened
                                  for decoding.

        """

        if self._infile is None:
            raise ArithmeticCodeError('No input file opened for decoding.')

        self._cumulative_prob = 0
        self._ranges = [0 for i in xrange(self.upper(EOF_CHAR) + 1)]
        count = 0

        # read [character, probability] sets
        while True:
            c = self._infile.get_char()

            # read (PRECISION - 2) bit count
            count = self._infile.get_bits_ltom(PRECISION - 2)

            if count == 0:
                # 0 count means end of header
                break
            elif self._ranges[self.upper(c)] != 0:
                raise ArithmeticCodeError('Duplicate entry for ' +
                    hex(ord(c)) + ' in header.')

            self._ranges[self.upper(c)] = count
            self._cumulative_prob += count

        # convert counts to range list
        self.symbol_count_to_probability_ranges()

    def initialize_decoder(self):
        """Initialize the code value and range bounds for encoded input.

        This method initializes the upper and lower ranges at their
        max/min values and reads in the most significant encoded bits.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            _upper, _lower, and _code are initialized from the MSBs of
            the encoded input.

        Exceptions Raised:
            None.

        """

        self._code = 0

        # read PRECISION MSBs of code one bit at a time
        for i in xrange(PRECISION):
            self._code <<= 1

            try:
                next_bit = self._infile.get_bit()
            except EOFError:
                # Encoded file out of data bits, just shift bits.
                pass
            except:
                raise       # other exception.  Let calling code handle it.
            else:
                self._code |= next_bit

        # start with full probability range [0%, 100%)
        self._lower = 0
        self._upper = 0xFFFF        # all ones

    def get_unscaled_code(self):
        """Undo scaling performed by apply_symbol_range.

        This method undoes the scaling that apply_symbol_range performed
        before bits were shifted out.  The value returned is the
        probability of the encoded symbol.

        Arguments:
            None.

        Return Value(s):
            The probability of the current symbol.

        Side Effects:
            The probability range list, _ranges, is built.

        Exceptions Raised:
            None.

        """

        range = self._upper - self._lower + 1

        # reverse the scaling operations from apply_symbol_range
        unscaled = self._code - self._lower + 1
        unscaled = unscaled * self._cumulative_prob - 1
        unscaled /= range
        return unscaled

    def get_symbol_from_probability(self, probability):
        """Get the symbol encoded by a probability.

        Given a probability, this method will return the symbol whose
        range includes that probability.  The symbol is found by a
        binary search on probability ranges, _ranges.

        Arguments:
            probability - The probability of the encoded symbol.

        Return Value(s):
            The decoded value of the encoded symbol.

        Side Effects:
            The probability range list, _ranges, is built.

        Exceptions Raised:
            ValueError - The specified probability doesn't fall within
            any of the ranges.

        """

        # initialize indices for binary search
        first = 0
        last = self.upper(EOF_CHAR)
        middle = last / 2

        # binary search
        while (last >= first):
            if probability < self._ranges[self.lower(middle)]:
                # lower bound is higher than probability
                last = middle - 1
                middle = first + ((last - first) / 2)
            elif probability >= self._ranges[self.upper(middle)]:
                # upper bound is lower than probability
                first = middle + 1
                middle = first + ((last - first) / 2)
            else:
                # we must have found the right value
                return middle

        # error: none of the ranges include the probability
        raise ValueError('Probability not in range.')

    def read_encoded_bits(self):
        """Shift out any bits that unaffected by decoding new symbols.

        This method undoes the scaling that apply_symbol_range performed
        before bits were shifted out.  The value returned is the
        probability of the encoded symbol.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            The upper and lower code bounds are adjusted so that they
            only contain bits that will be affected by the decoding of a
            new symbol.  Replacements are read from the encoded stream.

        Exceptions Raised:
            None.

        """

        mask_bit_zero = self.mask_bit(0)
        mask_bit_one = self.mask_bit(1)

        while True:
            if (self._upper ^ ~self._lower) & mask_bit_zero:
                # MSBs match, allow them to be shifted out
                pass
            elif (~self._upper & self._lower) & mask_bit_one:
                #*******************************************************
                # Possible underflow condition: neither MSBs nor second
                # MSBs match.  It must be the case that lower and upper
                # have MSBs of 01 and 10.  Remove 2nd MSB from lower and
                # upper.
                #*******************************************************
                self._lower &= ~(mask_bit_zero | mask_bit_one)
                self._upper |= mask_bit_one
                self._code ^= mask_bit_one

                # the shifts below make the rest of the bit removal work
            else:
                # nothing to shift out
                return

            #***********************************************************
            # Mask off old MSB and shift in new LSB.  Remember that
            # lower has all 0s beyond it's end and upper has all 1s
            # beyond it's end.
            #***********************************************************
            self._lower &= MSB_MASK
            self._lower <<= 1
            self._upper &= MSB_MASK
            self._upper <<= 1
            self._upper |= 1
            self._code &= MSB_MASK
            self._code <<= 1

            try:
                next_bit = self._infile.get_bit()
            except EOFError:
                pass        # either out of bits or error occurred.
            except:
                raise       # other exception.  Let calling code handle it.
            else:
                self._code |= next_bit

import os
import filecmp
import tempfile
import unittest


class EncodeDirTest(unittest.TestCase):
    """unittest test case that encodes/decodes/verifies files in cwd.

    Methods:
        setUp - Initialize arithmetic coding unit test.
        tearDown - Clean-up arithmetic coding unit test.
        test_static - Verify static arithmetic encoding on all files
                      in cwd.
        test_adaptive - Verify adaptive arithmetic encoding on all files
                        in cwd.

    Instance Variables:
        dir - listing of current directory
        encoded - name to be used for encoded file
        decoded - name to be used for decoded file
        ar - instance of ArithmeticCode class

    """

    def setUp(self):
        """Initialize arithmetic coding unit test.

        This method is called when an EncodeDirTest object is run.  It
        gets the contents of the current directory, creates the names
        used for temporary files containing encoded and decoded data,
        and it creates an instance of an ArithmeticCode object.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            Instance variables are initialized.

        Exceptions Raised:
            None.

        """

        self.dir = os.listdir('.')

        # generate unique tmp file names by cheating
        makesuffix = tempfile._RandomNameSequence()
        self.encoded = tempfile.gettempprefix() + makesuffix.next()
        self.decoded = tempfile.gettempprefix() + makesuffix.next()

        while self.encoded in self.dir:
            self.encoded = tempfile.gettempprefix() + makesuffix.next()

        while self.decoded in self.dir:
            self.decoded = tempfile.gettempprefix() + makesuffix.next()

        self.ar = ArithmeticCode()

    def tearDown(self):
        """Clean-up arithmetic coding unit test.

        This method is called when an EncodeDirTest run completes.  It
        deletes any temporary files left behind due to test failure.  It
        also deletes the instance of the ArithmeticCode object used for
        testing.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            Deletes test object and temporary files.

        Exceptions Raised:
            None.

        """

        del self.ar

        # delete any tmp files that might be opened
        if os.path.isfile(self.encoded):
            os.remove(self.encoded)

        if os.path.isfile(self.decoded):
            os.remove(self.decoded)

    def test_static(self):
        """Verify static arithmetic encoding on all files in cwd.

        This method iterates over every file in the current working
        directory.  Each file is encoded using the static arithmetic
        encoding algorithm, then the encoded file is decoded, and the
        decoded file is compared to the original to verify the process.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            None.

        Exceptions Raised:
            AssertionError - Mismatch between decoded file and original.

        """

        # use the static model to encode/decode every file in directory
        print '\nTests Using Static Model:'
        for src in self.dir:
            if os.path.isfile(src):
                print '\tEncoding', src
                self.ar.__init__(True)
                self.ar.encode_file(src, self.encoded)
                print '\tDecoding', src
                self.ar.__init__(True)
                self.ar.decode_file(self.encoded, self.decoded)

                self.assertTrue(filecmp.cmp(src, self.decoded),
                    'Failed to Verify {0}'.format(src))

                os.remove(self.encoded)
                os.remove(self.decoded)

    def test_adaptive(self):
        """Verify adaptive arithmetic encoding on all files in cwd.

        This method iterates over every file in the current working
        directory.  Each file is encoded using the adaptive arithmetic
        encoding algorithm, then the encoded file is decoded, and the
        decoded file is compared to the original to verify the process.

        Arguments:
            None.

        Return Value(s):
            None.

        Side Effects:
            None.

        Exceptions Raised:
            AssertionError - Mismatch between decoded file and original.

        """

        # use the static model to encode/decode every file in directory
        print '\nTests Using Adaptive Model:'
        for src in self.dir:
            if os.path.isfile(src):
                print '\tEncoding', src
                self.ar.__init__(False)
                self.ar.encode_file(src, self.encoded)
                print '\tDecoding', src
                self.ar.__init__(False)
                self.ar.decode_file(self.encoded, self.decoded)

                self.assertTrue(filecmp.cmp(src, self.decoded),
                    'Failed to Verify {0}'.format(src))

                os.remove(self.encoded)
                os.remove(self.decoded)

if __name__ == "__main__":
    unittest.main()
