from setuptools import setup, find_packages

setup(
    name='weather-library',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A library for fetching and formatting weather data.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/weather-library',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pyquery',
        'requests',  # Add any other dependencies your library needs
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Change if using a different license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)