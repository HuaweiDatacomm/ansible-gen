from setuptools import setup, find_packages

setup(
    name='ansible-gen',
    version='0.6.0',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
          'ansible-gen=ansible_gen.ansible_gen:main',
        ],
    },
    install_requires=[
        "pyang >=2.5.0",
        "jinja2==2.11.0",
        "xmltodict==0.11.0",
    ],
    url='https://github.com/HuaweiDatacomm/ansible-gen',
    license='Apache License, Version 2.0',
    author='frank feng',
    author_email='frank.fengchong@huawei.com',
    description='a tool can generate ansible api according yang modules and some input xml files'
)
