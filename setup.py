from setuptools import setup, find_packages
from os import path
here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='timbermafia',
    version='0.1.1',

    description="Package that makes implementing good-looking "
                "and flexible logging easy.",

    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/hypernormalisation/timbermafia',

    author='Stephen Ogilvy',
    author_email='sogilvy@tutanota.io',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    keywords='logging',
    packages=find_packages(exclude=['bin', 'notebooks']),
    scripts=['bin/demo_timbermafia', 'bin/display_ansi_colours'],
    python_requires='>=3.6',

    project_urls={
        'Source': 'https://github.com/hypernormalisation/timbermafia',
        'Bug Reports': 'https://github.com/hypernormalisation/timbermafia/issues',
    },
)
