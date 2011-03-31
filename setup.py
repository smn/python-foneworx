from setuptools import setup, find_packages

def listify(filename):
    return filter(None, open(filename, 'r').readlines())

setup(
    name = "python-foneworx",
    version = "0.1",
    url = 'http://github.com/smn/python-foneworx',
    license = 'BSD',
    description = "Foneworx XML API library",
    long_description = open('README.rst', 'r').read(),
    author = 'Simon de Haan',
    author_email='dev@praekeltfoundation.org',
    packages = find_packages(),
    install_requires = ['setuptools'].extend(listify('requirements.pip')),
)

