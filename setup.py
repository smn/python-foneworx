from setuptools import setup, find_packages

setup(
    name = "smn-houston",
    version = "0.1",
    url = 'http://github.com/smn/houston',
    license = 'BSD',
    description = "Foneworx XML API library",
    author = 'Simon de Haan',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['twisted',],
)

