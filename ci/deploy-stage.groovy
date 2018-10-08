@NonCPS

def staging_server = "172.31.60.34,"

pipeline {
    agent { node { label 'master' } }
    parameters {
        string(name: 'edx_platform_version', defaultValue: 'master', description: 'which commit id to deploy')
        choice(name: 'migrate_db', choices: ['yes', 'no'], description: 'Run Migrate DB')
    }
    stages {
        stage('Deploy Stage Server') {
            steps {
                sh """
                cd /var/tmp/configuration/playbooks
                . /edx/app/edx_ansible/venvs/edx_ansible/bin/activate
                ansible-playbook -u ubuntu -i ${staging_server} --key-file=/root/STAGING_SG.pem --tags "lt-deploy" ./edxapp_deploy.yml -e "edx_platform_version=${edx_platform_version}" -e "migrate_db=${migrate_db}"
                """
            }
        }
    }
}