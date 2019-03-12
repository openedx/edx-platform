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
def vars = "LT_KEY_FILE=/root/.ssh/id_rsa "
def machine = null
def proceed = true

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
                    try {
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
                        s3Download(file:"/tmp/${machine}_password.yml", bucket:'ltdps-jenkins', path:"${machine}_password.yml", force:true)
                        s3Download(file:"/tmp/${machine}_host.yml", bucket:'ltdps-jenkins', path:"${machine}_host.yml", force:true)

                        def ipAddresses = readFile("/tmp/${machine}.txt").tokenize("\n")
                        def para = input message: 'choose machine, use all for full deployment',
                            parameters: [choice(choices: ["all"] + ipAddresses, description: "", name: 'ipAddress'),
                                         string(defaultValue: '1', description: "", name: 'step', trim: true),
                                         string(defaultValue: '10', description: "", name: 'failPercentage', trim: true)]


                        def contents = input message: 'Content you want to deploy, all/platform/themes. Optionally theme name, split by `,`,(stage only allow one theme) empty for all themes',
                            parameters: [choice(choices: ["full", "platform", "themes"], description: "", name: 'repo'),
                                         string(defaultValue: '', description: "", name: 'themes', trim: true)]

                        themes = contents['themes'].tokenize(',')

                        if(themes){
                            if(machine == 'stage') {
                                writeFile file: "/tmp/themes.yml", text: """LT_THEMES:\n  - {name: 'triboo', repo: "git@github.com:Learningtribes/triboo-theme.git", version: "${themes[0]}"}"""
                            } else {
                                vars += "DEPLOY_THEMES=${themes} "
                            }
                        }

                        def repo = contents['repo']

                        // post process parameters
                        if(repo == 'full'){
                            tags = "deploy,assets"
                        } else if (repo == 'platform') {
                            tags = "deploy"
                        } else {
                            tags = "assets"
                        }

                        vars += "fail_percentage=${para['failPercentage']} serial_count=${para['step']} "

                        selectedIpAddress = para['ipAddress']
                        if (selectedIpAddress == 'all') {
                            selectedIpAddress = ipAddresses.join(",")
                        }

                        if (commitId.contains('~')) {
                            commitId = env.GIT_BRANCH + commitId.substring(4)
                        } else if (commitId == 'HEAD') {
                            commitId = env.GIT_BRANCH
                        }
                        vars += "edx_platform_version=${commitId}"
                    }
                    } catch (err) {
                        proceed = false
                    }
                }
            }
        }
        stage("Get Deployment repo") {
            when {
                expression { return proceed == true }
            }
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
            when {
                expression { return proceed == true }
            }
            steps {
                dir("configuration/playbooks") {
                    sh """
                    . /tmp/.venv/bin/activate
                    ansible-playbook --ssh-common-args='-o "StrictHostKeyChecking no"' \
                    -u ubuntu -i ${selectedIpAddress}, --key-file="/tmp/STAGING_SG.pem" \
                    -e "${vars}" -e "@/tmp/${machine}_password.yml" -e "@/tmp/${machine}_host.yml" -e "@/tmp/themes.yml" \
                    -t ${tags} lt_edxapp_with_worker.yml
                    """
                }

            }
        }
    }
    post {
        always {
            sh "rm -rf configuration"
            script {
                currentBuild.result = "SUCCESS"
                echo "RESULT: ${currentBuild.result}"
            }
        }
    }

}
