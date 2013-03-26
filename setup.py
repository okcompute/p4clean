# !/usr/bin/env python
# # -*- coding: utf-8 -*-
# """Setup for p4clean."""

import ast
from setuptools import setup



def version():
    """Return version string."""
    with open('p4clean.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s


with open('README.rst') as readme:
    setup(
        name='p4clean',
        version=version(),
        description='A tool to reset perforce local workspace to its initial state. '
        'The operation is similar to "Reconcile Offline Work" operation with more '
        'features.',
        long_description=readme.read(),
        license='Expat License',
        author='Pascal Lalancette',
        author_email='okcompute@gmail.com',
        url='https://github.com/okcompute/p4clean',
        classifiers=[
            'Development Status :: 1 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python'
            ],
        keywords='perforce, clean, initial',
        test_suite='test.test_p4clean',
        py_modules=['p4clean'],
        zip_safe=False,
        entry_points={'console_scripts': ['p4clean = p4clean:main']},
        )
