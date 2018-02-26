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
            unstash "artifacts-lms-unit-1"
            unstash "artifacts-lms-unit-2"
            unstash "artifacts-lms-unit-3"
            unstash "artifacts-lms-unit-4"
            unstash "artifacts-cms-unit-all"
            git_branch = env.BRANCH_NAME
            git_commit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
			
            if (git_branch == "PR-.") {
                merge_commit_parents= sh(returnStdout: true, script: 'git rev-parse HEAD | git log --pretty=%P -n 1 --date-order').trim()
                git_branch = sh(returnStdout: true, script: 'git rev-parse HEAD^1').trim()
                echo git_branch
                if (merge_commit_parents.length() > 40) {
                    echo 'More than one merge commit parent signifies that the merge commit is not the PR commit'
                    echo "Changing git_commit from '${git_commit}' to '${merge_commit_parents.take(40)}'"
                    git_commit = merge_commit_parents.take(40)
                } else {
                    echo 'Only one merge commit parent signifies that the merge commit is also the PR commit'
                    echo "Keeping git_commit as '${git_commit}'"
                }
            } else {
                echo 'Branch name singifies that its not PR.'
                echo "Changing target_branch to '${git_branch}'"
                target_branch = git_branch	
            }

            try {
                withCredentials([string(credentialsId: 'rg-codecov-edx-platform-token', variable: 'CODE_COV_TOKEN')]) {
                    sh """
                        source scripts/jenkins-common.sh \
                        paver coverage -b '${target_branch}' \
                        pip install codecov==2.0.5 \
                        codecov --token='${CODE_COV_TOKEN}' --branch='${git_commit}' \
                        touch `find . -name *.xml` || true \
                    """
                }
            } finally {
                archiveArtifacts 'reports/**, test_root/log/**'
                cobertura autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: 'reports/coverage.xml', conditionalCoverageTargets: '70, 0, 0', failUnhealthy: false, failUnstable: false, lineCoverageTargets: '80, 0, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '80, 0, 0', onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false
                deleteDir()
            }
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
}
