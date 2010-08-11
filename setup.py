from distutils.core import setup

__desc__  = """
====================
ArithmeticCode Class
====================
Description
-----------
This archive contains a python package that includes a class implementing
arithmetic coding and decoding.  This implementation is not intended to be
the best, fastest, smallest, or any other performance related adjective.

More information on Arithmetic encoding may be found at:
http://michael.dipperstein.com/arithmetic
http://www.datacompression.info/ArithmeticCoding.shtml

License
-------
ArithmeticCode is licensed under the GNU General Public License v3.  See COPYING
for full license text.

Files
-----
::

    __init__.py     - Python package initializtion code for bitfile.
    arcode.py       - File containing a Class implementing the arithmetic encoding and decoding algorithms.
    COPYING         - GNU General Public License v3
    README          - Package documentation
    sample.py       - Sample usage.
    setup.py        - distutils setup file.

Installing
----------
This package is dependent on the BitFile package.  A current version may be
obtained from the Python Package Index (http://pypi.python.org/) or
http://michael.dipperstein.com/bitlibs/

Install the BitFile package prior to installing this package.

This package uses distutils.  The package may be installed with the following
command::

    python setup.py install

Usage
-----
arcode.py is fully documented with docstrings.  Use your favorite tool for
generating documentation from docstrings.

arcode.py also contains a simple unit test, which may be performed when the
package is executed with the following command:
python arcode.py

sample.py demonstrates usage of the ArithmaticCode methods for encoding and
decoding files.

The following commands will encode a file:
import arcode::

    ar = arcode.ArithmeticCode(use_static_model)
    ar.encode_file(input_file, output_file)

Where *input_file* and *output_file* are the names of the file to be encoded and
file that will contain the results of the encoding.

The following commands will decode a file:
import arcode::

    ar = arcode.ArithmeticCode(use_static_model)
    ar.decode_file(input_file, output_file)

Where *input_file* and *output_file* are the names of the file to be decoded and
file that will contain the results of the decoding.

History
-------
| 08/06/10 - Initial release

ToDo
----
* Add/Verify support for Python 3.x.
* Add/Verify support for file-like objects.
"""

__classifiers__ = [
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Archiving :: Compression',
    'Topic :: Utilities',
]

setup(name='arcode',
      version='0.1',
      description=\
        'A module providing arithmetic coding to compress/decompress files.',
      author='Michael Dipperstein',
      author_email='mdipper@alumni.engr.ucsb.edu',
      license='GPL',
      url='http://michael.dipperstein.com/arithmetic/',
      packages=['arcode',],
      package_data={'arcode': ['COPYING', 'README']},
      platforms='All platforms',
      long_description=__desc__,
      classifiers=__classifiers__,
     )
