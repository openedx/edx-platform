def makeNode(suite, shard) {
  return {
    echo "I am ${suite}:${shard}, and the worker is yet to be started!"
        node('edxapp') {
            container('edxapp') {
                checkout scm

                sh 'git log --oneline | head'

                
                timeout(time: 55, unit: 'MINUTES') {
                    echo "Hi, it is me ${suite}:${shard} again, the worker just started!"
                    sh """
mkdir /tmp/mongodata
mongod --fork --logpath=/tmp/mongod.log --nojournal --dbpath /tmp/mongodata
npm install
source /tmp/ve/bin/activate
sed -i 's/cryptography==1.5.3/cryptography==1.9/' requirements/edx/base.txt
pip install --exists-action w -r requirements/edx/paver.txt
pip install --exists-action w -r requirements/edx/pre.txt
pip install --exists-action w -r requirements/edx/github.txt
pip install --exists-action w -r requirements/edx/local.txt
pip install  --exists-action w pbr==0.9.0
pip install --exists-action w -r requirements/edx/base.txt
pip install --exists-action w -r requirements/edx/post.txt
pip install coveralls==1.0
"""
                    try {
                        if (suite == 'accessibility') {
                            sh 'source /tmp/ve/bin/activate && ./scripts/accessibility-tests.sh'
                        } else {
                            withEnv(["TEST_SUITE=${suite}", "SHARD=${shard}", "NO_PREREQ_INSTALL=True"]) {
                                sh 'source /tmp/ve/bin/activate && ./scripts/all-tests.sh'
                            }
                        }
                    } finally {
                        sh 'killall mongod'
                        archiveArtifacts 'reports/**, test_root/log/**'
                        try {
                            junit 'reports/**/*.xml'
                        } finally {
                            // This works, but only for the current build files.
                            deleteDir()
                        }
                    }
                }
            }
        }
    }
}

def getSuites() {
    return [
        [name: 'commonlib-js-unit', 'shards': ['all']],
        [name: 'quality', 'shards': ['all']],
        [name: 'lms-unit', 'shards': [
                1,
                2,
                3,
                4,
            ]],
        [name: 'cms-unit', 'shards': ['all']],
        [name: 'accessibility', 'shards': ['all']],
        [name: 'cms-acceptance', 'shards': ['all']],
    ]
}

def buildParallelSteps() {
    def parallelSteps = [:]

    for (def suite in getSuites()) {
        def name = suite['name']

        for (def shard in suite['shards']) {
            parallelSteps["${name}_${shard}"] = makeNode(name, shard)
        }
    }

    return parallelSteps
}

podTemplate(cloud: 'jnlp', label: 'edxapp', containers: [
        containerTemplate(name: 'edxapp',
            image: 'gcr.io/appsembler-testing/jenkins-worker:v0.1.3',
            ttyEnabled: true, 
            command: 'cat')
    ]) {
    stage('Prepare') {
        echo 'Starting the build...'
        echo 'It it always nice to have a green checkmark :D'
    }
    stage('Test') {
        parallel buildParallelSteps()
    }
    stage('Done') {
        echo 'I am done, hurray!'
    }
}
