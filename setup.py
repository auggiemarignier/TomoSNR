from setuptools import setup

setup(
    name = 'TomoS2N',
    version = '1.0',
    author = 'Auggie Marignier',
    author_email = 'augustin.marignier.14@ucl.ac.uk',
    packages = ['src'],
    package_data = {'src':['masks/*']},
    entry_points = {'console_scripts':[
        'tomos2n = src.command:process'
    ]}
)
