import setuptools

                     

setuptools.setup(
    name="siteparser",
    version="0.0.1",
    author="Alexey Ponimash",
    author_email="alexey.ponimash@gmail.com",
    description="Package for parsing many sistes",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
       'requests>=2.10.0',
       'jinja2>=2.10.0',
       'pysocks',
#       'lxml>=2.0',
#       'cssselect',
       'pyyaml>3.10',
    ],
    entry_points={
       'console_scripts': [
            'siteparser = siteparser.siteparser:main'
       ]
    },
)

