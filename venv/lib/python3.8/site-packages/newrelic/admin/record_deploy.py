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

from __future__ import print_function

import os
import pwd

from newrelic.admin import command, usage
from newrelic.common import agent_http, certs, encoding_utils
from newrelic.config import initialize
from newrelic.core.config import global_settings


def fetch_app_id(app_name, client, headers):
    status, data = client.send_request(
        "GET",
        "/v2/applications.json",
        params={"filter[name]": app_name},
        headers=headers,
    )

    if not 200 <= status < 300:
        raise RuntimeError("Status not OK", status)

    response_json = encoding_utils.json_decode(encoding_utils.ensure_str(data))
    if "applications" not in response_json:
        return

    for application in response_json["applications"]:
        if application["name"] == app_name:
            return application["id"]


def record_deploy(
    host,
    api_key,
    app_name,
    description,
    revision="Unknown",
    changelog=None,
    user=None,
    port=443,
    proxy_scheme=None,
    proxy_host=None,
    proxy_user=None,
    proxy_pass=None,
    timeout=None,
    ca_bundle_path=None,
    disable_certificate_validation=False,
):
    headers = {"X-Api-Key": api_key or "", "Content-Type": "application/json"}

    client = agent_http.HttpClient(
        host=host,
        port=port,
        proxy_scheme=proxy_scheme,
        proxy_host=proxy_host,
        proxy_user=proxy_user,
        proxy_pass=proxy_pass,
        timeout=timeout,
        ca_bundle_path=ca_bundle_path,
        disable_certificate_validation=disable_certificate_validation,
    )

    with client:
        app_id = fetch_app_id(app_name, client, headers)
        if app_id is None:
            raise RuntimeError(
                "The application named %r was not found in your account. Please "
                "try running the newrelic-admin server-config command to force "
                "the application to register with New Relic." % app_name
            )

        path = "/v2/applications/{}/deployments.json".format(app_id)

        if user is None:
            user = pwd.getpwuid(os.getuid()).pw_gecos

        deployment = {}
        deployment["revision"] = revision

        if description:
            deployment["description"] = description
        if changelog:
            deployment["changelog"] = changelog
        if user:
            deployment["user"] = user

        data = {"deployment": deployment}
        payload = encoding_utils.json_encode(data).encode("utf-8")

        status_code, response = client.send_request(
            "POST", path, headers=headers, payload=payload
        )

        if status_code != 201:
            raise RuntimeError(
                "An unexpected HTTP response of %r was received "
                "for request made to https://%s:%d%s. The payload for the "
                "request was %r. The response payload for the request was %r. "
                "If this issue persists then please report this problem to New "
                "Relic support for further investigation."
                % (status_code, host, port, path, data, response)
            )


@command(
    "record-deploy",
    "config_file description [revision changelog user]",
    "Records a deployment for the monitored application.",
)
def record_deploy_cmd(args):
    import sys

    if len(args) < 2:
        usage("record-deploy")
        sys.exit(1)

    def _args(
        config_file, description, revision="Unknown", changelog=None, user=None, *args
    ):
        return config_file, description, revision, changelog, user

    config_file, description, revision, changelog, user = _args(*args)

    settings = global_settings()

    settings.monitor_mode = False

    initialize(config_file)

    host = settings.host

    if host == "collector.newrelic.com":
        host = "api.newrelic.com"
    elif host.startswith("collector.eu"):
        host = "api.eu.newrelic.com"
    elif host == "staging-collector.newrelic.com":
        host = "staging-api.newrelic.com"

    port = settings.port or 443

    record_deploy(
        host=host,
        api_key=settings.api_key,
        app_name=settings.app_name,
        description=description,
        revision=revision,
        changelog=changelog,
        user=user,
        port=port,
        proxy_scheme=settings.proxy_scheme,
        proxy_host=settings.proxy_host,
        proxy_user=settings.proxy_user,
        proxy_pass=settings.proxy_pass,
        timeout=settings.agent_limits.data_collector_timeout,
        ca_bundle_path=settings.ca_bundle_path,
        disable_certificate_validation=settings.debug.disable_certificate_validation,
    )
