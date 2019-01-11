import setuptools
import siteparser as module
                     

setuptools.setup(
    name=module.name,
    version=module.version,
    author="Alexey Ponimash",
    author_email="alexey.ponimash@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
       'requests',
       'jinja2',
       'lxml',
       'cssselect',
       'pyyaml>3.10',
    ],
    entry_points={
       'console_scripts': [
            'siteparser = siteparser.siteparser:main'
       ]
    },
)
