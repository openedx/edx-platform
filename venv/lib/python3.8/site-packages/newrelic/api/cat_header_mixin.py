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

from newrelic.common.encoding_utils import (obfuscate, deobfuscate,
        json_encode, json_decode, base64_encode, base64_decode)


# CatHeaderMixin assumes the mixin class also inherits from TimeTrace
class CatHeaderMixin(object):
    cat_id_key = 'X-NewRelic-ID'
    cat_transaction_key = 'X-NewRelic-Transaction'
    cat_appdata_key = 'X-NewRelic-App-Data'
    cat_synthetics_key = 'X-NewRelic-Synthetics'
    cat_metadata_key = 'x-newrelic-trace'
    cat_distributed_trace_key = 'newrelic'
    settings = None

    def __enter__(self):
        result = super(CatHeaderMixin, self).__enter__()
        if result is self and self.transaction:
            self.settings = self.transaction.settings or None
        return result

    def process_response_headers(self, response_headers):
        """
        Decode the response headers and create appropriate metrics based on the
        header values. The response_headers are passed in as a list of tuples.
        [(HEADER_NAME0, HEADER_VALUE0), (HEADER_NAME1, HEADER_VALUE1)]

        """

        settings = self.settings
        if not settings:
            return

        if not settings.cross_application_tracer.enabled:
            return

        appdata = None
        try:
            for k, v in response_headers:
                if k.upper() == self.cat_appdata_key.upper():
                    appdata = json_decode(deobfuscate(v,
                            settings.encoding_key))
                    break

            if appdata:
                self.params['cross_process_id'] = appdata[0]
                self.params['external_txn_name'] = appdata[1]
                self.params['transaction_guid'] = appdata[5]

        except Exception:
            pass

    def process_response_metadata(self, cat_linking_value):
        payload = base64_decode(cat_linking_value)
        nr_headers = json_decode(payload)
        self.process_response_headers(nr_headers.items())

    @classmethod
    def generate_request_headers(cls, transaction):
        """
        Return a list of NewRelic specific headers as tuples
        [(HEADER_NAME0, HEADER_VALUE0), (HEADER_NAME1, HEADER_VALUE1)]

        """

        if transaction is None or transaction.settings is None:
            return []

        settings = transaction.settings

        nr_headers = []

        if settings.distributed_tracing.enabled:
            transaction.insert_distributed_trace_headers(nr_headers)

        elif settings.cross_application_tracer.enabled:
            transaction.is_part_of_cat = True
            path_hash = transaction.path_hash
            if path_hash is None:
                # Disable cat if path_hash fails to generate.
                transaction.is_part_of_cat = False
            else:
                encoded_cross_process_id = obfuscate(settings.cross_process_id,
                        settings.encoding_key)
                nr_headers.append((cls.cat_id_key, encoded_cross_process_id))

                transaction_data = [transaction.guid, transaction.record_tt,
                        transaction.trip_id, path_hash]
                encoded_transaction = obfuscate(json_encode(transaction_data),
                        settings.encoding_key)
                nr_headers.append(
                        (cls.cat_transaction_key, encoded_transaction))

        if transaction.synthetics_header:
            nr_headers.append(
                    (cls.cat_synthetics_key, transaction.synthetics_header))

        return nr_headers

    @staticmethod
    def _convert_to_cat_metadata_value(nr_headers):
        payload = json_encode(nr_headers)
        cat_linking_value = base64_encode(payload)
        return cat_linking_value

    @classmethod
    def get_request_metadata(cls, transaction):
        nr_headers = dict(cls.generate_request_headers(transaction))

        if not nr_headers:
            return None

        return cls._convert_to_cat_metadata_value(nr_headers)
