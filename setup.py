from setuptools import setup

setup(
    name = 'TomoS2N',
    packages = ['src'],
    package_data = {'src':['masks/*']},
    entry_points = {'console_scripts':[
        'tomos2n = src.command:process'
    ]}
)