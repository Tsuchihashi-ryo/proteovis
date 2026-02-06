from setuptools import setup, find_packages

def get_requirements_from_file():
    with open("./requirements.txt") as f_in:
        requirements = f_in.read().splitlines()
    return requirements

setup(
    name="proteovis",
    version='1.0.0',
    description='A Python module for loading and processing chromatography and PAGE data.',
    author='Tsuchihashi Ryo',
    author_email='tsuchihashi-ryo@jbpo.or.jp',
    url='https://github.com/Tsuchihashi-ryo/proteovis',
    packages=find_packages(),
    install_requires=get_requirements_from_file(),
    python_requires='>=3.6',
)
