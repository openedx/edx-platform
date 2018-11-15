@NonCPS

def staging_server = "172.31.60.34,"

def commit_Id = null
def dbMigrate = null

pipeline {
    agent { node { label 'master' } }
    stages {
        stage('Setup parameters') {
            options {
                timeout(time: 1, unit: 'MINUTES')
            }
            steps {
                echo 'Run script'
                script {
                    def commitIds = []
                    Jenkins.instance.getAllItems(Job).each{
                      def jobName = it.fullName
                      if("${jobName}".matches("platform-unittest(.*)")){
                        def jobBuilds = it.getBuilds()
                        jobBuilds.each{
                          def jobResult = it.getResult().toString()
                          if(!"$jobResult".matches("SUCCESS")){
                            def buildLog = it.getLog().toString()
                            buildLog.split('\n').find {
                              if (it =~ /git checkout -f/) {
                                commitId = it.minus(" > git checkout -f ")
                                if (!commitIds.contains(commitId)){
                                  commitIds.add(commitId)
                                  true
                                }
                                true
                              }
                            }
                          }
                        }
                      }
                    }
                    println commitIds
                    def commitList = ["NULL"].plus(commitIds)
                    commit_Id = input message: "which commit id to deploy", 
                        parameters: [choice(name: 'edx_platform_version', choices: commitList, description: 'which commit id to deploy')]
                    if(commit_Id == "NULL"){
                        commit_Id = input message: "which commit id to deploy",
                            parameters: [string(name: 'edx_platform_version', defaultValue: 'master', description: 'which commit id to deploy')]
                    }
                    println commit_Id
                    dbMigrate = input message: "Run Migrate DB",
                        parameters: [choice(name: 'migrate_db', choices: ['no', 'yes'], description: 'Run Migrate DB')]
                }
            }
        }
        stage('Confirm otherwise Timeout') {
            options {
                timeout(time: 1, unit: 'MINUTES')
            }
            input {
                message "Should coutinue to deploy?"
                ok "Sure!"
            }
            steps {
                echo 'Start deploying...'
            }
        }
        stage('Deploy Stage Server') {
            steps {
                sh """
                echo ${commit_Id}
                echo ${dbMigrate}
                cd /var/tmp/configuration/playbooks
                . /edx/app/edx_ansible/venvs/edx_ansible/bin/activate
                ansible-playbook -u ubuntu -i ${staging_server} --key-file=/root/STAGING_SG.pem --tags "lt-deploy" ./edxapp_deploy.yml -e "edx_platform_version=${commit_Id}" -e "migrate_db=${dbMigrate}"

                """
            }
        }
    }
}