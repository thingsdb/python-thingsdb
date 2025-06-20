"""
Local testing:
pip install -e .

Upload to PyPI

python setup.py sdist
twine upload --repository pypitest dist/python_thingsdb-X.X.X.tar.gz
twine upload --repository pypi dist/python_thingsdb-X.X.X.tar.gz
"""
from setuptools import setup, find_packages
from thingsdb import __version__

try:
    with open('README.md', 'r') as f:
        long_description = f.read()
except IOError:
    long_description = '''
The ThingsDB connector can be used to communicate with ThingsDB with support
for joining rooms to listens for events.
'''.strip()

setup(
    name='python-thingsdb',
    version=__version__,
    description='ThingsDB Connector',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/thingsdb/python-thingsdb',
    author='Jeroen van der Heijden',
    author_email='jeroen@cesbit.com',
    license='MIT',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    install_requires=[
        'msgpack',
        'deprecation'
    ],
    keywords='database connector',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
)
