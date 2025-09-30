from setuptools import setup

setup(
    name='taskAutom',
    version='8.4.3',
    description='A simple task automation tool',
    long_description='A simple task automation tool for NOKIA SROS based routers',
    long_description_content_type='text/x-rst',
    url='https://github.com/laimaretto/taskAutom',
    author='Lucas Aimaretto',
    author_email='laimaretto@gmail.com',
    license='BSD 3-clause',
    packages=['src/taskAutom'],
    install_requires=['sshtunnel==0.4.0',
                      'netmiko==4.6.0',
                      'pandas==2.2.2',
                      'pyyaml==6.0.2',
                      'python-docx==0.8.11',
                      'numpy==1.26.4',
                      'paramiko==3.5.1',
                      ],
    python_requires='>=3.10',
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['taskAutom=src.taskAutom.taskAutom:main'],
    },
)