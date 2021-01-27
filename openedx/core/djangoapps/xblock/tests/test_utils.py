import pytest
import datetime
from django.test import override_settings
from openedx.core.djangoapps.xblock.utils import (
    get_secure_token_for_xblock_handler,
    validate_secure_token_for_xblock_handler,
)
from freezegun import freeze_time

REFERENCE_PARAMS = {
    "generation_user_id": "12344",
    "validation_user_id": "12344",
    "generation_block_key_str": "some key",
    "validation_block_key_str": "some key",
    "validation_time_delta_s": 0,
    "generation_secret_key": "baseline_key",
    "validation_secret_key": "baseline_key",
}


@pytest.mark.parametrize(
    "param_delta,expected_validation",
    [
        ({}, True),
        # Ensure token still valid in 1 day
        ({"validation_time_delta_s": 86400}, True),
        # Ensure token is invalid after 5 days
        ({"validation_time_delta_s": 86400 * 5}, False),
        # Ensure token is not valid 5 days before generation
        # In the case where the validating server is really skewed
        # from the generating server.
        ({"validation_time_delta_s": 86400 * -5}, False),
        # Different user tries to user your token.
        ({"validation_user_id": 54321}, False),
        # Access a different block.
        ({"validation_block_key_str": "some other block"}, False),
        # If key is changed, token shouldn't be valid.
        ({"validation_secret_key": "new secret key"}, False),
    ],
)
def test_secure_token(param_delta: dict, expected_validation: bool):
    params = {}
    params.update(REFERENCE_PARAMS)
    params.update(param_delta)

    with override_settings(SECRET_KEY=params["generation_secret_key"]):
        reference_time = datetime.datetime.utcnow()
        with freeze_time(reference_time):
            token = get_secure_token_for_xblock_handler(
                params["generation_user_id"], params["generation_block_key_str"]
            )

    with override_settings(SECRET_KEY=params["validation_secret_key"]):
        with freeze_time(reference_time + datetime.timedelta(seconds=params["validation_time_delta_s"])):
            assert (
                validate_secure_token_for_xblock_handler(
                    params["validation_user_id"], params["validation_block_key_str"], token
                )
                == expected_validation
            )
