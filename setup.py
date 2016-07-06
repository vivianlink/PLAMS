
from setuptools import setup

setup(
    name='PLAMS',
    version='1.1',
    author='Michal Handzlik',
    author_email='handzlik@scm.com',
    package_dir={'': 'src/scm'},
    packages=['plams'],
    url='https://www.scm.com/doc/plams/',
    license='',
    description='Python Library for Automating Molecular Simulations',
    long_description='',
    classifiers=[
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Topic :: Computational Chemistry :: Libraries"
    ],
    install_requires=[
        'dill', 'six',
    ],
)
