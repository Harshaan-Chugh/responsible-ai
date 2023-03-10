# Copyright 2022 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0


registry = {}


def register_class(class_name, class_object):
    """
    :param class_name: inputs the name for the class and that should be unique
    :param class_object: class object is given as the input

    Return : registered data in the form of dictionary containing class name as the key and class object as the value


    """
    if class_name != "":
        if class_name in registry:
            raise NameError("Class Name: " + class_name + " already exists. Please enter a unique class name.")
        registry[class_name] = class_object

