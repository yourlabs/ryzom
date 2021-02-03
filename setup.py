from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import sys


setup(
    name='ryzom',
    setup_requires='setupmeta',
    versioning='dev',
    description='Meteorish Python responsive frontend',
    author='Thomas Mignot',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/ryzom',
    # packages=find_packages(),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    keywords='django frontend',
    install_requires=[
        'cli2'
    ],
    tests_require=[
        'tox',
    ],
    extras_require=dict(
        django=[
            'django',
            'crudlfap @ git+https://yourlabs.io/oss/crudlfap.git@newryz#egg=crudlfap',
            # 'crudlfap',
        ],
        dev=[
            'channels',
            'channels-redis',
        ],
        test=[
            'lxml',
        ],
        psql=[
            'psycopg2-binary',
            'lxml',
            #'psycopg2-binary',
        ],
    ),
    entry_points={
        'console_scripts': [
            'ryzom = ryzom_example.manage:main',
        ],
    },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3',
)
