pipeline {
    agent any
    options {
        timestamps()
    }
    environment {
        BUILD_TAG = "${env.BUILD_TAG.toLowerCase()}"
    }
    stages {
        stage("Stop Old Build") {
            steps {
                milestone label: "", ordinal:  Integer.parseInt(env.BUILD_ID) - 1
                milestone label: "", ordinal:  Integer.parseInt(env.BUILD_ID)
            }
        }
        stage("Test") {
            steps {
                sh "BUILD_TAG=${BUILD_TAG} make ci_up"
                sh "BUILD_TAG=${BUILD_TAG} make ci_test"
                junit "reports/**/nosetests.xml"
                cobertura coberturaReportFile: "reports/coverage.xml", failUnstable: false, maxNumberOfBuilds: 20, onlyStable: false, zoomCoverageChart: false
            }
            post {
                always {

                    sh "BUILD_TAG=${BUILD_TAG} make ci_clean || true"
                    sh "BUILD_TAG=${BUILD_TAG} make ci_down || true"
                }
            }
        }
    }
}
