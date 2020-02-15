__version__ = '1.0.0'

import os
import sys
from setuptools import setup, find_packages

if sys.version_info[:2] < (3, 4):
    raise RuntimeError('k0emu requires Python 3.4 or later')

DESC = "Renesas (NEC) 78K0 emulator"
here = os.path.abspath(os.path.dirname(__file__))
try:
    LONG_DESC = open(os.path.join(here, 'README.rst')).read()
except:
    LONG_DESC = DESC

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Assembly',
    'Topic :: Software Development :: Debuggers',
    'Topic :: Software Development :: Embedded Systems',
    'Topic :: Software Development :: Interpreters',
    'Topic :: System :: Hardware'
]

setup(
    name='k0emu',
    version=__version__,
    license='License :: OSI Approved :: BSD License',
    url='https://github.com/mnaberez/k0emu',
    description=DESC,
    long_description=LONG_DESC,
    classifiers=CLASSIFIERS,
    author="Mike Naberezny",
    author_email="mike@naberezny.com",
    maintainer="Mike Naberezny",
    maintainer_email="mike@naberezny.com",
    packages=find_packages(),
    install_requires=["k0dasm"],
    extras_require={},
    tests_require=[],
    include_package_data=True,
    zip_safe=False,
    test_suite="k0emu.tests",
    entry_points={
        'console_scripts': [
            'k0emu = k0emu.run:main',
            'k0debug = k0emu.debug:main'
        ],
    },
)
