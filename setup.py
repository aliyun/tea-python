"""
 Licensed to the Apache Software Foundation (ASF) under one
 or more contributor license agreements.  See the NOTICE file
 distributed with this work for additional information
 regarding copyright ownership.  The ASF licenses this file
 to you under the Apache License, Version 2.0 (the
 "License"); you may not use this file except in compliance
 with the License.  You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing,
 software distributed under the License is distributed on an
 "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 KIND, either express or implied.  See the License for the
 specific language governing permissions and limitations
 under the License.
"""

import sys
import ssl
from setuptools import setup, find_packages

"""
Setup module for tea.
Created on 3/24/2020
@author: Alibaba Cloud
"""

install_requires = [
    'requests>=2.21.0, <3.0.0',
]

if sys.version_info.minor <= 7:
    install_requires.append('aiohttp>=3.7.0, <3.9.0')
else:
    install_requires.append('aiohttp>=3.7.0, <4.0.0')

if ssl.OPENSSL_VERSION_INFO is not None and len(ssl.OPENSSL_VERSION_INFO) >= 3 and ssl.OPENSSL_VERSION_INFO[:3] >= (
        1, 1, 1):
    pass
else:
    install_requires.append('urllib3<2.0.0')

PACKAGE = "Tea"
DESCRIPTION = "The tea module of alibabaCloud Python SDK."
AUTHOR = "Alibaba Cloud"
AUTHOR_EMAIL = "alibaba-cloud-sdk-dev-team@list.alibaba-inc.com"
URL = "https://github.com/aliyun/tea-python"
VERSION = __import__(PACKAGE).__version__

with open("README.md", encoding="utf-8") as fp:
    LONG_DESCRIPTION = fp.read()

setup_args = {
    'version': VERSION,
    'description': DESCRIPTION,
    'long_description': LONG_DESCRIPTION,
    'author': AUTHOR,
    'author_email': AUTHOR_EMAIL,
    'license': "Apache License 2.0",
    'url': URL,
    'keywords': ["alibabacloud", "sdk", "tea"],
    'packages': find_packages(exclude=["tests*"]),
    'platforms': 'any',
    'install_requires': install_requires,
    'classifiers': (
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development',
    ),
    'python_requires': '>=3.6'
}

setup(name='alibabacloud-tea', **setup_args)
