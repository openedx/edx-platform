@NonCPS
def commitHashForBuild(build) {
  def scmAction = build?.actions.find { action -> action instanceof jenkins.scm.api.SCMRevisionAction }
  return scmAction?.revision?.hash
}
def commitId = null
def upstreamProjectName = "edxapp.test"
def selectedIpAddress = null
def step = null
def failPercentage = null
def tags = null
def themes = null
def vars = ""

pipeline {
    agent any
    options {
        timestamps()
        withAWS(credentials:'aws')
    }
    stages {
        stage("Get parameters") {
            steps {
                script {
                    def machine = null
                    timeout(time: 2) {
                        // get parameters
                        if(env.GIT_BRANCH =~ "(master|hotfix).*"){
                            machine = input message: "environment you want to deploy to?",
                                parameters: [choice(choices: ['stage', 'production'], description: '', name: 'machine')]
                        } else {
                            machine = "stage"
                        }
                        if (machine == "stage" || env.GIT_BRANCH =~ "(hotfix).*") {
                            commitId = input message: "you are going to deploy to ${machine} environment, which commit id you want to use?",
                                parameters: [string(defaultValue: 'HEAD', description: '', name: 'commitId', trim: true)]
                        } else {
                            def build = input message: "you are going to deploy to ${machine} environment, choose a build to use.",
                                parameters: [run(description: '', filter: 'SUCCESSFUL', name: 'commitId', projectName: "${upstreamProjectName}/${env.GIT_BRANCH}")]

                            commitId = commitHashForBuild(build)
                        }
                        s3Download(file:"/tmp/${machine}.txt", bucket:'ltdps-jenkins', path:"edxapp_${machine}.txt", force:true)
                        def ipAddresses = readFile("/tmp/${machine}.txt").tokenize("\n")
                        def para = input message: 'choose machine, use all for full deployment',
                            parameters: [choice(choices: ["all"] + ipAddresses, description: "", name: 'ipAddress'),
                                         string(defaultValue: '1', description: "", name: 'step', trim: true),
                                         string(defaultValue: '10', description: "", name: 'failPercentage', trim: true)]

                        def contents = input message: 'Content you want to deploy, platform/theme/all, and themes name, split by `,`, empty for all themes',
                            parameters: [choice(choices: ["all", "themes", "platform"], description: "", name: 'repo'),
                                         string(defaultValue: '', description: "", name: 'themes', trim: true)]

                        themes = contents['themes'].tokenize(',')
                        if(themes){
                            vars += "DEPLOY_THEMES=${themes} "
                        }

                        def repo = contents['repo']

                        // post process parameters
                        if(repo == 'all'){
                            tags = "deploy,assets"
                        } else if (repo == 'themes') {
                            tags = "assets"
                        } else {
                            tags = "deploy"
                        }

//                        failPercentage = para['failPercentage'] as int
//                        step = para['step'] as int
                        vars += "fail_percentage=${para['failPercentage']} serial_count=${para['step']} "

                        selectedIpAddress = para['ipAddress']
                        if (selectedIpAddress == 'all') {
                            selectedIpAddress = ipAddresses.join(",")
                        } else {
                            selectedIpAddress += ","
                        }
                        vars += "EDXAPP_HOST=${selectedIpAddress} APP_HOST=${selectedIpAddress} "

                        if (commitId.contains('~')) {
                            commitId = env.GIT_BRANCH + commitId.substring(4)
                        } else if (commitId == 'HEAD') {
                            commitId = env.GIT_BRANCH
                        }
                        vars += "edx_platform_version=${commitId} STATEFUL_HOST=54.255.229.123 "
                    }
                }
            }
        }
        stage("Get Deployment repo") {
            steps {
                dir("configuration") {
                    git credentialsId: 'github', url: 'https://github.com/Learningtribes/configuration.git'
                    sh """
                    virtualenv /tmp/.venv
                    . /tmp/.venv/bin/activate
                    make requirements
                    """
                }


            }

        }
        stage("Deploy") {
            steps {
                dir("configuration/playbooks") {
                    sh """
                    . /tmp/.venv/bin/activate
                    ansible-playbook --ssh-common-args='-o "StrictHostKeyChecking no"' \
                    -u ubuntu -i ${selectedIpAddress}, --key-file="/tmp/STAGING_SG.pem" \
                    -e "${vars}" -t ${tags} lt_edxapp_with_worker.yml
                    """
                }
            }
        }
    }
    post {
        always {
            sh "rm -rf configuration"
        }
    }

}
