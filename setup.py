from setuptools import setup

with open('readme.md', 'r') as readme:
  long_desc = readme.read()

setup(
  name = 'wiktionaryparser',
  version = '0.0.96',
  description = 'A tool to parse word data from wiktionary.com into a JSON object',
  long_description = long_desc,
  long_description_content_type='text/markdown',
  packages = ['wiktionaryparser', 'tests'],
  data_files=[('testOutput', ['tests/testOutput.json']), ('readme', ['readme.md']), ('requirements', ['requirements.txt'])],
  author = 'Suyash Behera',
  author_email = 'sne9x@outlook.com',
  url = 'https://github.com/Suyash458/WiktionaryParser',
  download_url = 'https://github.com/Suyash458/WiktionaryParser/archive/master.zip',
  keywords = ['Parser', 'Wiktionary'],
  install_requires = ['beautifulsoup4', 'requests'],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: MIT License',
  ],
)
