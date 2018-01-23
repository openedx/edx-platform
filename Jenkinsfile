#!groovy

def startTests(suite, shard) {
        return {
                node("${suite}-${shard}-worker") {
                        wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 1, 'defaultBg': 2]) {
                                cleanWs()
                                checkout scm
                                try {
                                        withEnv(["TEST_SUITE=${suite}", "SHARD=${shard}"]) {
                                                sh './scripts/all-tests.sh'
                                        }
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


def coverageTest() {
        node('coverage-report-worker') {
                wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 1, 'defaultBg': 2]) {
                        cleanWs()
                        checkout scm
                        try {
                                unstash 'artifacts-lms-unit-1'
                                unstash 'artifacts-lms-unit-2'
                                unstash 'artifacts-lms-unit-3'
                                unstash 'artifacts-lms-unit-4'
                                unstash 'artifacts-cms-unit-all'
                                withCredentials([string(credentialsId: 'rg-codecov-edx-platform-token', variable: 'CODE_COV_TOKEN')]) {
                                        sh "git rev-parse --short HEAD^1 > .git/ci-branch-id"
                                        sh "git rev-parse --short HEAD^2 > .git/target-branch-id"
                                        def CI_BRANCH = readFile('.git/ci-branch-id')
                                        def TARGET_BRANCH = readFile('.git/target-branch-id')
                                        sh './scripts/jenkins-report.sh'
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

def buildParallelSteps() {
        def parallelSteps = [:]

        for (def suite in getSuites()) {
                def name = suite['name']

                for (def shard in suite['shards']) {
                        parallelSteps["${name}_${shard}"] = startTests(name, shard)
                }
        }

        return parallelSteps
}

stage('Prepare') {
        echo 'Starting the build...'
}

stage('Unit tests') {
        parallel buildParallelSteps()
}

stage('Coverage') {
        coverageTest()
}

stage('Done') {
        echo 'Done! :)'
}

