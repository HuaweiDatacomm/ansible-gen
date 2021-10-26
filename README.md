# **ansible-gen**

## **Overview**
ansible-gen is an automatic code generation tool for ansible modules according to YANG modules and some user-specified files which is designed to managemant the devices through NETCONF.


## **Installation**
### **Prerequisites**
- OS: Windows,Red Hat,Ubuntu,CentOS,OS X,BSD,Suse

- Python: Python2/Python3(greater than python2.7 is preferred)

- Ansible(optional): ansible 2.6 or later and lower than 2.10, greater than 2.10 is under development.

- Ne-ansible-plugin: see [https://github.com/HuaweiDatacomm/ne-ansible-plugin](https://github.com/HuaweiDatacomm/ne-ansible-plugin)



### **From Source**
```
$git clone https://github.com/HuaweiDatacomm/ansible-gen.git
```
```
$python setup.py install
```
### **From Pypi**

```
$pip3 install ansible-gen
```


## **How to use it**
input commandline: **ansilbe-gen -h** after installation.

```
$ansible-gen -h
```

Usage: ansible-gen.py [options]

Dynamically generate Ansible modules from yang and xml files, then deploy
Ansible module

Options:

  -h, --help  &#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;show this help message and exit

  -v, --version&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;version number info for program

  -y YANG_DIR, --yang_dir=YANG_DIR&#x2003;&#x2003;&#x2002;      the directory of yang_files.

  -r XML_DIR, --resource=XML_DIR&#x2003;&#x2003;&#x2003;&#x2003;        the directory of ansible api description xml files.

  -p SCRIPT_DIR, --script=SCRIPT_DIR&#x2003;&#x2003;    the directory of previous generated ansible module which may has user define check implementation.

  -l LOG_DIR, --log=LOG_DIR&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2002;&#x2003; the log directory, name of log is ansible_gen.log

  -o OUTPUT_DIR, --output=OUTPUT_DIR&#x2003;    the output dir for generated ansible modules

  --default&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;&#x2003;get parameters from default config file /etc/ansible-gen/default.cfg


## Contributing

There are many ways to contribute:
- Fix and report bugs
- Improve documentation
- Review code and feature proposals
- Answer questions and discuss here on github and on our [Community Site](https://intl.devzone.huawei.com/en/datacom/network-element/index.html)


## **Additional Resources**
TBD
