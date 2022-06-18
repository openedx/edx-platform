# Copyright 2010 New Relic, Inc.
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

from newrelic.api.asgi_application import ASGIApplicationWrapper


@property
def loaded_app(self):
    # Always use the original application until the interface is resolved in
    # auto mode
    if getattr(self, "interface", "") == "auto":
        app = self._nr_loaded_app
        while hasattr(app, "__wrapped__"):
            app = app.__wrapped__
        return app
    return self._nr_loaded_app


@loaded_app.setter
def loaded_app(self, value):
    # Wrap only the first loaded app
    if (
        not getattr(self, "_nr_loaded_app", None)
        and value
        and getattr(self, "interface", "") != "wsgi"
    ):
        value = ASGIApplicationWrapper(value)
    self._nr_loaded_app = value


def instrument_uvicorn_config(module):
    module.Config.loaded_app = loaded_app
