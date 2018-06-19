from setuptools import setup

with open("readme.md", "r") as fh:
    long_description = fh.read()

setup(name='wiktionaryparser',
      version='0.1.0',
      description='A python library to interface with wiktionary via json',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/Suyash458/WiktionaryParser',
      packages=['wiktionaryparser'])
