pipeline {

    agent { label "coverage-worker" }

    options {
        timestamps()
        timeout(75)
    }

    stages {
        stage('Run Tests') {
            parallel {
                stage('lms_unit_1') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 1
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        ansiColor('gnome-terminal') {
                            sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                                    doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                                    userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                                    refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                                    url: 'git@github.com:edx/edx-platform.git']]]
                                sh "bash scripts/all-tests.sh"
                                stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}_${SHARD}_reports"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,*.log'
                            junit '**/nosetests.xml'
                        }
                    }
                }
                stage('lms_unit_2') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 2
                        TEST_SUITE = 'lms-unit'
                    }
                    steps{
                        ansiColor('gnome-terminal') {
                            sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                                    doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                                    userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                                    refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                                    url: 'git@github.com:edx/edx-platform.git']]]
                                sh "bash scripts/all-tests.sh"
                                stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}_${SHARD}_reports"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,*.log'
                            junit '**/nosetests.xml'
                        }
                    }
                }
                stage('lms_unit_3') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 3
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        ansiColor('gnome-terminal') {
                            sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                                    doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                                    userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                                    refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                                    url: 'git@github.com:edx/edx-platform.git']]]
                                sh "bash scripts/all-tests.sh"
                                stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}_${SHARD}_reports"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,*.log'
                            junit '**/nosetests.xml'
                        }
                    }
                }
                stage('lms_unit_4') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 4
                        TEST_SUITE = 'lms-unit'
                    }
                    steps {
                        ansiColor('gnome-terminal') {
                            sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                                    doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                                    userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                                    refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                                    url: 'git@github.com:edx/edx-platform.git']]]
                                sh "bash scripts/all-tests.sh"
                                stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}_${SHARD}_reports"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,*.log'
                            junit '**/nosetests.xml'
                        }
                    }
                }
                stage('cms_unit') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 1
                        TEST_SUITE = 'cms-unit'
                    }
                    steps {
                        ansiColor('gnome-terminal') {
                            sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                                    doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                                    userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                                    refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                                    url: 'git@github.com:edx/edx-platform.git']]]
                                sh "bash scripts/all-tests.sh"
                                stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}_${SHARD}_reports"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,*.log'
                            junit '**/nosetests.xml'
                        }
                    }
                }
                stage('commonlib_unit') {
                    agent { label "jenkins-worker" }
                    environment {
                        SHARD = 1
                        TEST_SUITE = 'commonlib-unit'
                    }
                    steps {
                        ansiColor('gnome-terminal') {
                            sshagent(credentials: ['jenkins-worker'], ignoreMissing: true) {
                                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '${sha1}']],
                                    doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [],
                                    userRemoteConfigs: [[credentialsId: 'jenkins-worker',
                                    refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*',
                                    url: 'git@github.com:edx/edx-platform.git']]]
                                sh "bash scripts/all-tests.sh"
                                stash includes: 'reports/**/*coverage*', name: "${TEST_SUITE}_${SHARD}_reports"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*,test_root/log/**/*.log,**/nosetests.xml,*.log'
                            junit '**/nosetests.xml'
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
                        unstash 'lms-unit_1_reports'
                        unstash 'lms-unit_2_reports'
                        unstash 'lms-unit_3_reports'
                        unstash 'lms-unit_4_reports'
                        unstash 'cms-unit_1_reports'
                        unstash 'commonlib-unit_1_reports'
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
