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

import logging
import threading

try:
    import grpc

    from newrelic.core.infinite_tracing_pb2 import RecordStatus, Span
except ImportError:
    grpc = None

_logger = logging.getLogger(__name__)


class StreamingRpc(object):
    """Streaming Remote Procedure Call

    This class keeps a stream_stream RPC alive, retrying after a timeout when
    errors are encountered. If grpc.StatusCode.UNIMPLEMENTED is encountered, a
    retry will not occur.
    """

    PATH = "/com.newrelic.trace.v1.IngestService/RecordSpan"
    RETRY_POLICY = (
        (15, False),
        (15, False),
        (30, False),
        (60, False),
        (120, False),
        (300, True),
    )
    OPTIONS = [("grpc.enable_retries", 0)]

    def __init__(self, endpoint, stream_buffer, metadata, record_metric, ssl=True):
        self._endpoint = endpoint
        self._ssl = ssl
        self.metadata = metadata
        self.stream_buffer = stream_buffer
        self.request_iterator = iter(stream_buffer)
        self.response_processing_thread = threading.Thread(
            target=self.process_responses, name="NR-StreamingRpc-process-responses"
        )
        self.response_processing_thread.daemon = True
        self.notify = self.condition()
        self.record_metric = record_metric
        self.closed = False

        self.create_channel()

    def create_channel(self):
        if self._ssl:
            credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(self._endpoint, credentials, options=self.OPTIONS)
        else:
            self.channel = grpc.insecure_channel(self._endpoint, options=self.OPTIONS)

        self.rpc = self.channel.stream_stream(self.PATH, Span.SerializeToString, RecordStatus.FromString)

    def create_response_iterator(self):
        with self.stream_buffer._notify:
            self.request_iterator = iter(self.stream_buffer)
            self.request_iterator._stream = reponse_iterator = self.rpc(self.request_iterator, metadata=self.metadata)
            return reponse_iterator

    @staticmethod
    def condition(*args, **kwargs):
        return threading.Condition(*args, **kwargs)

    def close(self):
        channel = None
        with self.notify:
            if self.channel:
                channel = self.channel
                self.channel = None
                self.closed = True
            self.notify.notify_all()

        if channel:
            _logger.debug("Closing streaming rpc.")
            channel.close()
            try:
                self.response_processing_thread.join(timeout=5)
            except Exception:
                pass
            _logger.debug("Streaming rpc close completed.")

    def connect(self):
        self.response_processing_thread.start()

    def process_responses(self):
        response_iterator = None

        retry = 0
        while True:
            with self.notify:
                if self.channel and response_iterator:
                    code = response_iterator.code()
                    details = response_iterator.details()

                    self.record_metric(
                        "Supportability/InfiniteTracing/Span/gRPC/%s" % code.name,
                        {"count": 1},
                    )

                    if code is grpc.StatusCode.OK:
                        _logger.debug(
                            "Streaming RPC received OK "
                            "response code. The agent will attempt "
                            "to reestablish the stream immediately."
                        )

                        # Reconnect channel for load balancing
                        self.request_iterator.shutdown()
                        self.channel.close()
                        self.create_channel()

                    else:
                        self.record_metric(
                            "Supportability/InfiniteTracing/Span/Response/Error",
                            {"count": 1},
                        )

                        if code is grpc.StatusCode.UNIMPLEMENTED:
                            _logger.error(
                                "Streaming RPC received "
                                "UNIMPLEMENTED response code. "
                                "The agent will not attempt to "
                                "reestablish the stream."
                            )
                            break

                        # Unpack retry policy settings
                        if retry >= len(self.RETRY_POLICY):
                            retry_time, error = self.RETRY_POLICY[-1]
                        else:
                            retry_time, error = self.RETRY_POLICY[retry]
                            retry += 1

                        # Emit appropriate retry logs
                        if not error:
                            _logger.warning(
                                "Streaming RPC closed. Will attempt to reconnect in %d seconds. Check the prior log entries and remedy any issue as necessary, or if the problem persists, report this problem to New Relic support for further investigation. Code: %s Details: %s",
                                retry_time,
                                code,
                                details,
                            )
                        else:
                            _logger.error(
                                "Streaming RPC closed after additional attempts. Will attempt to reconnect in %d seconds. Please report this problem to New Relic support for further investigation. Code: %s Details: %s",
                                retry_time,
                                code,
                                details,
                            )

                        # Reconnect channel with backoff
                        self.request_iterator.shutdown()
                        self.channel.close()
                        self.notify.wait(retry_time)
                        if self.closed:
                            break
                        else:
                            _logger.debug("Attempting to reconnect Streaming RPC.")
                            self.create_channel()

                if self.closed:
                    break

                response_iterator = self.create_response_iterator()

                _logger.info("Streaming RPC connect completed.")

            try:
                for response in response_iterator:
                    _logger.debug("Stream response: %s", response)
            except Exception:
                pass

        self.close()
        _logger.info("Process response thread ending.")
