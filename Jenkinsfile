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
                        echo suite
                        if (suite == 'quality') {
                            sh """
export PYLINT_THRESHOLD=3600
export ESLINT_THRESHOLD=9850

source /tmp/ve/bin/activate
EXIT=0

echo "Finding fixme's and storing report..."
paver find_fixme > reports/fixme.log || { cat reports/fixme.log; EXIT=1; }

echo "Finding pep8 violations and storing report..."
paver run_pep8 > reports/pep8.log || { cat reports/pep8.log; EXIT=1; }

echo "Finding pylint violations and storing in report..."
paver run_pylint -l $PYLINT_THRESHOLD | tee pylint.log || EXIT=1

mkdir -p reports
PATH=$PATH:node_modules/.bin

echo "Finding ESLint violations and storing report..."
paver run_eslint -l $ESLINT_THRESHOLD > reports/eslint.log || { cat reports/eslint.log; EXIT=1; }

# Run quality task. Pass in the 'fail-under' percentage to diff-quality
paver run_quality -p 100 || EXIT=1

echo "Running code complexity report (python)."
paver run_complexity > reports/code_complexity.log || echo "Unable to calculate code complexity. Ignoring error."
"""
                        } else {
                            sh """
source /tmp/ve/bin/activate
mongod --fork --logpath=/tmp/mongod.log --nojournal --dbpath /tmp/mongodata
paver test_lib --with-flaky --cov-args="-p" --with-xunitmp
killall mongod
"""
                        }
                    } finally {
//                        archiveArtifacts 'reports/**, test_root/log/**'
                        try {
//                            junit 'reports/**/*.xml'
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
        [name: 'quality', 'shards': ['all']],
        [name: 'test_lib', 'shards': ['all']]
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
