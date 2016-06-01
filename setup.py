import pathlib
from setuptools import setup, find_packages

name = 'nx_misc'
description = 'Miscellaneous utilities'

here = pathlib.Path(__file__).resolve().parent
with (here / name / 'version.txt').open() as fp:
    version = fp.read().strip()

with (here / 'README.rst').open() as fp:
    long_description = fp.read()

setup(name=name,
      version=version,
      description=description,
      long_description=long_description,
      url='https://github.com/nxdevel/nx_misc',
      author='A Bradford',
      author_email='nxdevel@users.noreply.github.com',
      license='MIT',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Software Development :: Libraries',
          'Topic :: Utilities',          
          'Intended Audience :: Developers'],
      keywords='development utilities',
      packages=find_packages(),
      install_requires=['pytz', 'tzlocal'])
