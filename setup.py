from setuptools import setup, find_packages


setup(
    name="tomosnr",
    version="1.2.1",
    author="Auggie Marignier",
    author_email="augustin.marignier.14@ucl.ac.uk",
    packages=find_packages(),
    package_data={"tomosnr": ["tiles/*"]},
    entry_points={"console_scripts": ["tomosnr = tomosnr.main:process"]},
)
