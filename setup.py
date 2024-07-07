from setuptools import setup, find_packages

# with open('readme.md', 'r') as f:
#     long_description = f.read()

setup(
    name='cetus',
    version='0.1.0',
    description='Cetus',
    long_description='long_description',
    long_description_content_type='text/markdown',
    author='Vitaliy Boyarsky',
    author_email='boyarsky.vitaliy@live.com',
    url='https://github.com/vitalibo/cetus',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.9',
)
