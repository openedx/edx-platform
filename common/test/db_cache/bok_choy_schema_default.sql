import boto3
import sys
import logging
import json
import click

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@click.command()
@click.option(
    '--spigot_state',
    help="Set the state of the spigot. "
         "ON: The spigot will send both queued and "
         "incoming webhooks to the target url(s). "
         "OFF: The spigot will store incoming webhooks "
         "in an SQS queue for future processing.",
    required=True,
    type=click.Choice(['ON', 'OFF']),
)
def main(spigot_state):
    # Connect to AWS API and Cloudwatch Events
    try:
        api_client = boto3.client('apigateway')
        cloudwatch_client = boto3.client('events')
    except:
        logger.error(
            "Boto was unable to connect to apigateway "
            "and/or cloudwatch events"
        )
        sys.exit(1)

    # Get the api id and update the state of the spigot
    api_id = _get_api_id(api_client)
    _update_state(
        api_client,
        cloudwatch_client,
        spigot_state,
        api_id
    )

    logger.info(
        "The spigot is now: {}".format(spigot_state)
    )


def _get_api_id(api_client):
    """
    Find the restApiId of the API gateway.
    """
    # Rather than hardcode the API's id, find the
    # API by its name
    api_list = api_client.get_rest_apis()
    for api in api_list.get("items"):
        if api.get("name") == "edx-tools-webhooks-processing":
            api_id = api.get("id")
            break

    if api_id:
        return api_id
    else:
        logger.error(
            "Could not find an api id for the "
            "edx-tools-webhooks-processing API"
        )
        sys.exit(1)


def _update_state(api_client, cloudwatch_client, spigot_state, api_id):
    """
    Update the API stage variable to represent the new state,
    and update the send_to_queue lambda trigger accordingly.
    """
    # Update the API stage variable
    update_variable_op = {
        'op': 'replace',
        'path': '/variables/spigot_state',
        'value': spigot_state
    }

    api_client.update_stage(
        restApiId=api_id,
        stageName="prod",
        patchOperations=[update_variable_op]
    )

    # Update the cloudwatch event state
    if spigot_state == "ON":
        # Enable the cloudwatch event trigger
        try:
            cloudwatch_client.enable_rule(
                Name="edx-spigot-send-from-queue"
            )
        except:
            logger.error(
                "Could not enable the "
                "edx-spigot-send-from-queue event trigger"
            )
            sys.exit(1)
    elif spigot_state == "OFF":
        # Disable the cloudwatch event trigger
        try:
            cloudwatch_client.disable_rule(
                Name="edx-spigot-send-from-queue"
            )
        except:
            logger.error(
                "Could not disable the "
                "edx-tools-webhooks-processing event trigger"
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
