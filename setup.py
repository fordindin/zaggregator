import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zaggregator",
    version="0.0.1",
    author="Denis Barov",
    author_email="dindin+zaggregator@dindin.ru",
    description="Per-process stat monitoring solution for Zabbix",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fordindin/zaggregator",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ),
)
