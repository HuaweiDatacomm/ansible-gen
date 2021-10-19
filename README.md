# **ansible-gen**

## **Overview**
ansible-gen is a tool which can generated ansible modules according to yang modules and some user-specified files automatically.

## **Documentation**
see Documentation

## **Installation**
### **Prerequisites**
- OS: Windows,Red Hat,Ubuntu,CentOS,OS X,BSD,Suse

- Python: Python2/Python3(greater than python2.7 is preferred)

- Ansible(optional): ansible 2.6 or later and lower than 2.10

- Ne-ansible-plugin: see [https://github.com/HuaweiDatacomm/ne-ansible-plugin](https://github.com/HuaweiDatacomm/ne-ansible-plugin)

- Pyinstaller: 3.6

- pycodestyle: 2.5.0

- Autopep8: 1.4.3

- pyang: 2.5.0


### **From Source**
`git clone https://github.com/HuaweiDatacomm/ansible-gen.git`

`cd ./ansible-gen/ansible-gen` 

`chmod +x ./ansible-gen.sh` 

`./ansible-gen.sh`

### **From Pypi**

`pip3 install ansible-gen`

## **How to use**
input commandline: **ansilbe-gen -h** after installation.
ansible-gen -h
`Usage: ansible-gen.py [options]`

`Dynamically generate Ansible modules from yang and xml files, then deploy`
`Ansible module`

`Options:`
  `-h, --help            show this help message and exit`
  `-v, --version         version number info for program`
  `-y YANG_DIR, --yang_dir=YANG_DIR`
                        `the directory of yang_files.`
  `-r XML_DIR, --resource=XML_DIR`
                        `the directory of xml files which contains netconf rpc`
                        `message.`
  `-p SCRIPT_DIR, --script=SCRIPT_DIR`
                        `the directory of previous generated ansible module`
                        `which may has user define check implementation.`
  `-l LOG_DIR, --log=LOG_DIR`
                        `the log directory, name of log is ansible_gen.log`
  `-o OUTPUT_DIR, --output=OUTPUT_DIR`
                        `the output dir for generated scripts`
  `--default get parameters from default config file /etc/ansible-`
                        `gen/default.cfg`

`Ansible-gen 0.2.0`

