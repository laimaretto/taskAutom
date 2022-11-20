from importlib.metadata import entry_points
from setuptools import setup

setup(
    name='taskAutom',
    version='7.15.4',    
    description='A simple task automation tool',
    long_description='A simple task automation tool for NOKIA SROS based routers',
    long_description_content_type='text/x-rst',
    url='https://github.com/laimaretto/taskAutom',
    author='Lucas Aimaretto',
    author_email='laimaretto@gmail.com',
    license='BSD 3-clause',
    packages=['src/taskAutom'],
    install_requires=['paramiko==2.11.0',
                      'sshtunnel==0.4.0',
                      'netmiko==4.1.0',
                      'scp==0.13.3',
                      'pandas==1.4.1',
                      'pyyaml==5.3.1',
                      'python-docx==0.8.10',
                      'openpyxl==3.0.6',
                      'xlrd==2.0.1',                     
                      ],
    python_requires='>=3.8',
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['taskAutom=src.taskAutom.taskAutom:main'],
    },
)