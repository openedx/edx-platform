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

from newrelic.agent import wrap_external_trace

def instrument_pywapi(module):

    if hasattr(module, 'get_weather_from_weather_com'):
        wrap_external_trace(module, 'get_weather_from_weather_com', 'pywapi',
               module.WEATHER_COM_URL)

    if hasattr(module, 'get_countries_from_google'):
        wrap_external_trace(module, 'get_countries_from_google', 'pywapi',
               module.GOOGLE_COUNTRIES_URL)

    if hasattr(module, 'get_cities_from_google'):
        wrap_external_trace(module, 'get_cities_from_google', 'pywapi',
               module.GOOGLE_CITIES_URL)

    if hasattr(module, 'get_weather_from_yahoo'):
        wrap_external_trace(module, 'get_weather_from_yahoo', 'pywapi',
               module.YAHOO_WEATHER_URL)

    if hasattr(module, 'get_weather_from_noaa'):
          wrap_external_trace(module, 'get_weather_from_noaa', 'pywapi',
                 module.NOAA_WEATHER_URL)
