from distutils.core import setup

with open('README') as file:
    __desc__ = file.read()

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

module_description = \
    'A module providing arithmetic coding to compress/decompress files.',

setup(
    name='arcode',
    version='0.3',
    description=module_description,
    author='Michael Dipperstein',
    author_email='mdipper@alumni.engr.ucsb.edu',
    license='GPL',
    url='https://michaeldipperstein.github.io/arithmetic.html',
    packages=['arcode', ],
    package_data={'arcode': ['COPYING', 'README']},
    platforms='All platforms',
    long_description=__desc__,
    classifiers=__classifiers__,
)
