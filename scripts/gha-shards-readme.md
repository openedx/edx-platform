# Unit tests sharding strategy

#### background
Unit tests are run in parallel (in GitHub Actions matrices) using the sharding strategy specified in unit-test-shards.json
We've divided the top level modules into multiple shards to achieve better parallelism.
The configuration in unit-test-shards.json specifies the shard name as key for each shard and the value contains an object
with django settings for each module and paths for submodules to test for example:
```json
{
    "lms-1": {
        "paths": ["lms/djangoapps/course_api", ...],
        "settings": "lms.envs.test",
    }
    .
    .
    .
}
```
The `common` and `openedx` modules are tested with both `lms` and `cms` settings; that's why there are shards with the same `openedx`
submodules but with different Django settings.
For more details on sharding strategy please refer to this section on [sharding](https://openedx.atlassian.net/wiki/spaces/AT/pages/3235971586/edx-platfrom+unit+tests+migration+from+Jenkins+to+Github+Actions#Motivation-for-sharding-manually)

#### Unit tests count check is failing
There's a check in place that makes sure that all the unit tests under edx-platform modules are specified in `unit-test-shards.json`
If there's a mismatch between the number of unit tests collected from `unit-test-shards.json` and the number of unit tests collected
against the entire codebase the check will fail.
You'd have to update the `unit-test-shards.json` file manually to fix this.

##### How to fix
- If you've added a new django app to the codebase, and you want to add it to the unit tests you need to add it to the `unit-test-shards.json`, details on where (in which shard) to place your Django app please refer to the [sharding](https://openedx.atlassian.net/wiki/spaces/AT/pages/3235971586/edx-platfrom+unit+tests+migration+from+Jenkins+to+Github+Actions#Where-should-I-place-my-new-Django-app) section in this document.
- If you haven't added any new django app to the codebase, you can debug / verify this by collecting unit tests against a submodule by running `pytest` for example:
```
pytest --collect-only --ds=cms.envs.test cms/
```
For more details on how this check collects and compares the unit tests count please take a look at [verify unit tests count](../.github/workflows/verify-gha-unit-tests-count.yml)
