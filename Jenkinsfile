#!groovy

timeout_ci = env.CI_TIMEOUT.toInteger() ?: 35
assert timeout_ci instanceof Integer
channel_name = env.CHANNEL_NAME ?: "ci-open-edx"

def startTests(suite, shard) {
    return {
        timeout(timeout_ci.toInteger()) {
            node("${suite}-${shard}-worker") {
                wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 1, 'defaultBg': 2]) {
                    cleanWs()
                    checkout scm
                    try {
                        withEnv(["TEST_SUITE=${suite}", "SHARD=${shard}"]) {
                            sh './scripts/all-tests.sh'
                        }
                    } catch (err) {
                        slackSend channel: channel_name, color: 'danger', message: "Test ${suite}-${shard} failed in ${env.JOB_NAME}. Please check build info. (<${env.BUILD_URL}|Open>)", teamDomain: 'raccoongang', tokenCredentialId: 'slack-secret-token'
                    } finally {
                        archiveArtifacts 'reports/**, test_root/log/**'
                        stash includes: 'reports/**, test_root/log/**', name: "artifacts-${suite}-${shard}"
                        junit 'reports/**/*.xml'
                        deleteDir()
                    }
                }
            }
        }
    }
}

def coverageTest() {
    node('coverage-report-worker') {
        wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 1, 'defaultBg': 2]) {
            cleanWs()
            checkout scm
            branch_name = env.BRANCH_NAME
            change_target = env.CHANGE_TARGET

            withCredentials([string(credentialsId: 'rg-codecov-edx-platform-token', variable: 'CODE_COV_TOKEN')]) {
                codecov_token = env.CODE_COV_TOKEN
            }
            
            echo "Unstash unit-tests artifacts."
            unstash "artifacts-lms-unit-1"
            unstash "artifacts-lms-unit-2"
            unstash "artifacts-lms-unit-3"
            unstash "artifacts-lms-unit-4"
            unstash "artifacts-cms-unit-all"
            
            try {
                echo "Changing ci_commit to HEAD."
                ci_commit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                echo "CI_COMMIT = '${ci_commit}'"
                echo "BRANCH_NAME = '${branch_name}'"
                echo "CHANGE_TARGET = '${change_target}'"
                if (change_target != null) {
                    codecov_pr = "true"
                    codecov_branch = ci_commit
                    coverage_branch = "origin/${change_target}"
                } else {
                    codecov_pr = "false"
                    codecov_branch = branch_name
                    coverage_branch = "origin/${branch_name}"
                }
                sh """source ./scripts/jenkins-common.sh
                paver coverage -b ${coverage_branch}
                pip install codecov==2.0.15
                codecov --token=${codecov_token} --branch=${codecov_branch} --commit=${ci_commit} --pr=${codecov_pr}"""
            } catch (err) {
                slackSend channel: channel_name, color: 'danger', message: "Coverage report failed in ${env.JOB_NAME}. Please check build info. (<${env.BUILD_URL}|Open>)", teamDomain: 'raccoongang', tokenCredentialId: 'slack-secret-token'
            } finally {
                archiveArtifacts 'reports/**, test_root/log/**'
                cobertura autoUpdateHealth: false, autoUpdateStability: false, classCoverageTargets: '95, 95, 0', coberturaReportFile: 'reports/coverage.xml', failUnhealthy: false, failUnstable: false, fileCoverageTargets: '95, 95, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '95, 95, 0', onlyStable: false, packageCoverageTargets: '95, 95, 0', sourceEncoding: 'ASCII', zoomCoverageChart: true
                publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: '', reportFiles: 'reports/diff_coverage_combined.html', reportName: 'Diff Coverage Report', reportTitles: ''])
            }                
            deleteDir()
        }
    }
}

def getSuites() {
    return [
        [name: 'lms-unit', 'shards': [
            1,
            2,
            3,
            4,
            ]],
        [name: 'cms-unit', 'shards': ['all']],
    ]
}

def startParallelSteps() {
    def suiteNames = [:]

    for (def suite in getSuites()) {
        def name = suite['name']

        for (def shard in suite['shards']) {
            suiteNames["${name}_${shard}"] = startTests(name, shard)
        }
    }
    return suiteNames
}

stage('Prepare') {
    echo 'Starting the build...'
    slackSend channel: channel_name, color: 'good', message: "CI Tests started! ${env.JOB_NAME} (<${env.BUILD_URL}|Open>)", teamDomain: 'raccoongang', tokenCredentialId: 'slack-secret-token'
}

stage('Unit tests') {
    parallel startParallelSteps()
}

stage('Coverage') {
    coverageTest()
}

stage('Done') {
    echo 'Done! :)'
    slackSend channel: channel_name, color: 'good', message: "CI Tests finished! ${env.JOB_NAME} (<${env.BUILD_URL}|Open>)", teamDomain: 'raccoongang', tokenCredentialId: 'slack-secret-token'
}
