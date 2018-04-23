def runPythonTests() {
    ansiColor('gnome-terminal') {
        sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
            checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                url: 'git@github.com:edx/edx-platform.git']]]
            console_output = sh(returnStdout: true, script: 'bash scripts/all-tests.sh').trim()
            dir('stdout') {
                writeFile file: "${TEST_SUITE}-${SHARD}-stdout.log", text: console_output
            }
            stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}-${SHARD}-reports"
        }
    }
}

def savePythonTestArtifacts() {
    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,stdout/*.log,*.log'
    junit '**/nosetests.xml'
}

pipeline {

    agent { label "coverage-worker" }

    options {
        timestamps()
        timeout(75)
    }

    stages {
        stage('Run Tests') {
            parallel {
                stage('lms-unit-1') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 1
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-2') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 2
                        TEST_SUITE = 'lms-unit'
                    }
                    steps{
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-3') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 3
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-4') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 4
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-5') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 5
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-6') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 6
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-7') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 7
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-8') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 8
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-9') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 9
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('lms-unit-10') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 10
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('cms-unit-1') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 1
                        TEST_SUITE = 'cms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('cms-unit-2') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 2
                        TEST_SUITE = 'cms-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('commonlib-unit-1') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 1
                        TEST_SUITE = 'commonlib-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('commonlib-unit-2') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 2
                        TEST_SUITE = 'commonlib-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
                stage('commonlib-unit-3') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 3
                        TEST_SUITE = 'commonlib-unit'
                    }
                    steps {
                        script {
                            runPythonTests()
                        }
                    }
                    post {
                        always {
                            script {
                                savePythonTestArtifacts()
                            }
                        }
                    }
                }
            }
        }
        stage('Run coverage') {
            environment {
                CODE_COV_TOKEN = credentials('CODE_COV_TOKEN')
                TARGET_BRANCH = "origin/master"
                CI_BRANCH = "${ghprbSourceBranch}"
                SUBSET_JOB = "null" // Keep this variable until we can remove the $SUBSET_JOB path from .coveragerc
            }
            steps {
                ansiColor('gnome-terminal') {
                    sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                        checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                            doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                            userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                            refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                            url: 'git@github.com:edx/edx-platform.git']]]
                        unstash 'lms-unit-1-reports'
                        unstash 'lms-unit-2-reports'
                        unstash 'lms-unit-3-reports'
                        unstash 'lms-unit-4-reports'
                        unstash 'lms-unit-5-reports'
                        unstash 'lms-unit-6-reports'
                        unstash 'lms-unit-7-reports'
                        unstash 'lms-unit-8-reports'
                        unstash 'lms-unit-9-reports'
                        unstash 'lms-unit-10-reports'
                        unstash 'cms-unit-1-reports'
                        unstash 'cms-unit-2-reports'
                        unstash 'commonlib-unit-1-reports'
                        unstash 'commonlib-unit-2-reports'
                        unstash 'commonlib-unit-3-reports'
                        sh "./scripts/jenkins-report.sh"
                    }
                }
            }
            post {
                always {
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: true,
                        reportDir: 'reports', reportFiles: 'diff_coverage_combined.html',
                        reportName: 'Diff Coverage Report', reportTitles: ''])
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: true,
                        reportDir: 'reports/cover', reportFiles: 'index.html',
                        reportName: 'Coverage.py Report', reportTitles: ''])
                }
            }
        }
    }
}
