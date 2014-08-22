# Troubleshooting failing jenkins builds

###### Check the logs to find out why your build failed.
  * See [here](results.md#console-output-for-the-shard) for how to find the log.
  * If the log shows the build erroring out before tests begin running, report this to the test 
    engineering team. Be sure to share the link to your build log.

###### Run tests on devstack
  * If a build fails on jenkins, try to reporoduce and debug the failures in devstack.
  * See the [testing guide](../testing.md) for how to run the tests.
    - For lettuce acceptance test debugging, see [this section](../testing.md#debugging-acceptance-tests-on-vagrant).
  * For more debugging tips, see the [testing FAQ](https://github.com/edx/edx-platform/wiki/Test-engineering-FAQ).
    There you'll find tips for:
      - setting breakpoints in tests
      - visually debugging acceptance tests
      - running tests from a single file
      - and more..

  * "What's devstack?" ... See [here](https://github.com/edx/configuration/wiki/edX-Developer-Stack)

###### Check the 'flaky test' list
  * Known flaky tests can be found with filters on the openedx Jira site
    - [Known unresolved flaky tests](https://openedx.atlassian.net/issues/?filter=10600)
    - [Recently resolved flaky tests](https://openedx.atlassian.net/issues/?filter=11001)
  * Remember that a test being listed as flaky doesn't mean that it can't fail for other reasons. Look into
    the logs and confirm that it is failing for the same reason as listed in the issue ticket.
  * If your build has failure that is a recently resolved flaky test, try rebasing from master. (A new auto-pr
    build will start when you do this on an open PR.)

###### Check if the failure is occurring on the master branch
  * Tests run for the master branch are [here](https://jenkins.testeng.edx.org/job/edx-all-tests-auto-master/).
    You can inspect them the same way you would a PR build. 
