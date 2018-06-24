import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zaggregator",
    version="0.0.4",
    author="Denis Barov",
    author_email="dindin+zaggregator@dindin.ru",
    description="Per-process stat monitoring solution for Zabbix",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fordindin/zaggregator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    keywords="zabbix monitoring",
    python_requires='>=3',
    install_requires=['fuzzywuzzy>=0.16.0', 'psutil>=5.4.5', 'python-Levenshtein>=0.12.0', 'setproctitle>=1.1.10'],
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests*', 'venv', 'misc', 'build', 'dist']),
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'zaggregator = zaggregator.daemon:start',
            'zcheck = zaggregator.client:main',
        ],},
    data_files=[
        ('/var/run/zaggregator', []),
        ('/usr/share/zaggregator', ['misc/zaggregator.service', 'misc/zaggregator.conf', 'README.md', 'LICENSE',]),
        ('/usr/share/zaggregator/init.d', ['misc/init.d/zaggregator'],),
            ],

)
