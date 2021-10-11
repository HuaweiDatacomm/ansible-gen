from setuptools import setup

setup(
    name='ansible-gen',
    version='0.2.0',
    packages=['ansible_gen', 'ansible_gen.adapter', 'ansible_gen.adapter.utils', 'ansible_gen.adapter.utils.xml_parse',
              'ansible_gen.adapter.utils.yang_parse', 'ansible_gen.generator'],
    url='https://github.com/HuaweiDatacomm/ansible-gen',
    license='Apache License, Version 2.0',
    author='frank feng',
    author_email='frank.fengchong@huawei.com',
    description='a tool can generate ansible api according yang modules and some input xml files'
)
