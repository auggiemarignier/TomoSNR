from setuptools import setup, find_packages

setup(
    name = 'TomoS2N',
    packages = find_packages(),
    entry_points = {'console_scripts':[
        'tomos2n = src.command:process'
    ]}
)