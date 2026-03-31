# -*- coding: utf-8 -*-

"""
Copyright 2026 The Dapr Authors
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import configparser
import os

from setuptools import setup

version_info = {}
with open("dapr/ext/drasi/version.py") as fp:
    exec(fp.read(), version_info)
__version__ = version_info["__version__"]


def is_release():
    return ".dev" not in __version__


name = "dapr-ext-drasi"
version = __version__
description = "The official release of Dapr Python SDK Drasi Extension."
long_description = "This is the Drasi trigger extension for Dapr Workflows."

build_number = os.environ.get("GITHUB_RUN_NUMBER", "0")

cfg = configparser.ConfigParser()
cfg.read("setup.cfg")
install_requires = [
    r.strip()
    for r in cfg.get("options", "install_requires", fallback="").strip().splitlines()
    if r.strip()
]

if not is_release():
    name += "-dev"
    version = f"{__version__}{build_number}"
    description = "The developmental release for Dapr Python SDK Drasi Extension."
    long_description = (
        "This is the developmental release for the Drasi trigger extension."
    )
    install_requires = [
        "dapr-dev" + r[4:] if r.startswith("dapr ") else r for r in install_requires
    ]

print(f"package name: {name}, version: {version}", flush=True)

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    install_requires=install_requires,
)
