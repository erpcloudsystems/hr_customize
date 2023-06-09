from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in hr_customize/__init__.py
from hr_customize import __version__ as version

setup(
	name="hr_customize",
	version=version,
	description="HR Customize",
	author="Albashq Alshwmy",
	author_email="al.alshwmy@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
