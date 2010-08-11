"""Sample program using ArithmeticCode class.
************************************************************************

    File    : sample.py
    Purpose : This demonstrates the usage of the ArithmeticCode class.
    Author  : Michael Dipperstein
    Date    : August 3, 2010

************************************************************************

sample: A program demonstrating how to use the ArithmeticCode class.
Copyright (C) 2010
      Michael Dipperstein (mdipper@alumni.engr.ucsb.edu)

This file implements the sample module.

Sample is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

Sample is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import getopt
import os

import arcode


def show_usage():
    # Extract the name of this file from the command line
    this_file = sys.argv[0:][0]                     # full path
    this_file = (os.path.split(this_file))[1]       # name only

    print 'Usage: ',  this_file,  ' <options>\n'
    print 'options:\n'
    print '  -c : Encode input file to output file.'
    print '  -d : Decode input file to output file.'
    print '  -i <filename> : Name of input file.'
    print '  -o <filename> : Name of output file.'
    print '  -a : Use adaptive model instead of static.'
    print '  -h | ?  : Print out command line options.\n'

if __name__ == "__main__":

    encode = None
    use_static_model = True
    input_file = ''
    output_file = ''

    # Parse command line options
    opts, args = getopt.getopt(sys.argv[1:], 'acdh?i:o:',
        ['help', 'encode', 'decode', 'adaptive', 'input=', 'output='])

    for o, a in opts:
        if o in ('-c', '--encode'):
            encode = True
        if o in ('-d', '--decode'):
            encode = False
        if o in ('-a', '--adaptive'):
            use_static_model = False
        if o in ('-i', '--input'):
            input_file = a
        if o in ('-o', '--output'):
            output_file = a
        if o in ('-h', '-?', '--help',):
            show_usage()
            exit()

    # Validate command line options
    if len(input_file) == 0:
        print 'Error: Input file name is required.\n'
        show_usage()
        exit()

    if len(output_file) == 0:
        print 'Error: Output file name is required.\n'
        show_usage()
        exit()

    if encode == None:
        print 'Error: Encoding or Decoding must be specified.\n'
        show_usage()
        exit()

    # Encode/Decode specified file
    ar = arcode.ArithmeticCode(use_static_model)

    if encode:
        ar.encode_file(input_file, output_file)
    else:
        ar.decode_file(input_file, output_file)
