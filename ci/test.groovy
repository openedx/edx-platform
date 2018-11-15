
@NonCPS

def prevBuild = currentBuild.previousBuild
if (prevBuild)
    prevBuild.rawBuild._this().doTerm();


pipeline {
    agent { node { label 'master' } }
    stages {
        stage('Test') {
            steps {
                sh "make -f ci/ci.mk ci_up"
                sh "make -f ci/ci.mk ci_test"
                junit "unittest_reports/nosetests/*.xml"

            }
            post {
                always {
                    sh "make -f ci/ci.mk ci_down"
                }
            }
        }
    }
}