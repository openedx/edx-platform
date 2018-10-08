pipeline {
    agent { node { label 'master' } }
    stages {
        stage('Test') {
            steps {
                sh "make -f ci/ci.mk ci_up"
                sh "make -f ci/ci.mk ci_test"
                junit "unittest_reports/nosetests/*.xml"
                cobertura coberturaReportFile: "unittest_reports/coverage/lmscoverage.xml"
                cobertura coberturaReportFile: "unittest_reports/coverage/cmscoverage.xml"
                cobertura coberturaReportFile: "unittest_reports/coverage/commoncoverage.xml"
            }
            post {
                always {
                    sh "make -f ci/ci.mk ci_down"
                }
            }
        }
    }
}