from setuptools import setup

setup(
    name="TomoSNR",
    version="1.2",
    author="Auggie Marignier",
    author_email="augustin.marignier.14@ucl.ac.uk",
    packages=["src"],
    package_data={"src": ["masks/*"]},
    entry_points={"console_scripts": ["tomosnr = src.main:process"]},
)
