from importlib.metadata import entry_points
from pkg_resources import parse_requirements
from setuptools import find_packages, setup
import os
lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = './requirements.txt'
install_requires = [] # Here we'll get: ["gunicorn", "docutils>=0.3", "lxml==0.5a7"]
if os.path.isfile(requirement_path):
    with open(requirement_path, "r",encoding="UTF-16") as f:
        install_requires = f.read().splitlines()
setup(
  name="secret-cli",
  version="1.0.0",
  description="This package contains some sample hello world code",
  author="Shivansh",
  author_email="shivanshcoder@outlook.com",
  packages=find_packages(),
  install_requires = install_requires,
  entry_points = {
      'console_scripts': [
          'secret-cli = secret_cli.start:main'
      ]
  }
)