from setuptools import setup, find_packages
from os import path

def local_file(filename):
	with open(path.join(path.dirname(__file__), filename)) as f:
		return f.read()

setup(
	name='flexasm',
	version=local_file('VERSION').strip(),
	description='Flexible assembler',
	long_description=local_file('README.md'),
	long_description_content_type='text/markdown',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
	],
	keywords='flexible assembler',
	url='https://github.com/camerondm9/flexasm',
	author='Cameron Martens',
	author_email='camerondm9@yahoo.ca',
	license='MIT',
	packages=find_packages(),
	install_requires=[],
	include_package_data=True,
	zip_safe=True,
	test_suite='tests',
	tests_require=['pytest'],
	python_requires='>=3'
)
