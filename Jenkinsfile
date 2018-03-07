def dockerImage = 'gcr.io/appsembler-testing/jenkins-worker:v0.2.0'
def k8sCloud = 'jnlp'

def makeNode(suite, shard) {
  return {
    echo "I am ${suite}:${shard}, and the worker is yet to be started!"
        node('edxapp') {
            container('edxapp') {
                checkout scm
                
                timeout(time: 55, unit: 'MINUTES') {
                    echo "Hi, it is me ${suite}:${shard} again, the worker just started!"
                    stage('install') {
                        sh """
npm install
source /tmp/ve/bin/activate
# temporary fix for openssl/cryptography==1.5.3 incompatibility on debian stretch
sed -i 's/cryptography==1.5.3/cryptography==1.9/' requirements/edx/base.txt
pip install --exists-action w -r requirements/edx/paver.txt
pip install --exists-action w -r requirements/edx/pre.txt
pip install --exists-action w -r requirements/edx/github.txt
pip install --exists-action w -r requirements/edx/local.txt
pip install --exists-action w pbr==0.9.0
pip install --exists-action w -r requirements/edx/base.txt
pip install --exists-action w -r requirements/edx/post.txt
"""
                    }
                    try {
                        if (suite == 'quality') {
                            stage('quality') {
                                sh """
export PYLINT_THRESHOLD=3600
export ESLINT_THRESHOLD=9850
export NO_PREREQ_INSTALL=true

source /tmp/ve/bin/activate
EXIT=0

mkdir reports

echo "Finding fixme's and storing report..."
paver find_fixme > reports/fixme.log || { cat reports/fixme.log; EXIT=1; }

echo "Finding pep8 violations and storing report..."
paver run_pep8 > reports/pep8.log || { cat reports/pep8.log; EXIT=1; }

echo "Finding pylint violations and storing in report..."
# paver run_pylint -l \${PYLINT_THRESHOLD} | tee pylint.log || EXIT=1

mkdir -p reports
PATH=\${PATH}:node_modules/.bin

echo "Finding ESLint violations and storing report..."
paver run_eslint -l \${ESLINT_THRESHOLD} > reports/eslint.log || { cat reports/eslint.log; EXIT=1; }

# Run quality task. Pass in the 'fail-under' percentage to diff-quality
# paver run_quality -p 100 || EXIT=1

echo "Running code complexity report (python)."
paver run_complexity > reports/code_complexity.log || echo "Unable to calculate code complexity. Ignoring error."

cat > reports/quality.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="quality" tests="1" errors="0" failures="0" skip="0">
<testcase classname="quality" name="quality" time="0.604"></testcase>
</testsuite>
END

exit \$EXIT
"""
                            }
                        } else {
                            stage('test') {
                                try {
                                    sh """
# prepare environment for tests
source /tmp/ve/bin/activate
mkdir /tmp/mongodata
mongod --fork --logpath=/tmp/mongod.log --nojournal --dbpath /tmp/mongodata
export NO_PREREQ_INSTALL=true

# run tests
paver test_lib --with-flaky --cov-args="-p" --with-xunit

# clean up
killall mongod

# coverage reporting
curl -s https://codecov.io/bash > /tmp/codecov
/bin/bash /tmp/codecov -t ${CODECOV_TOKEN}
"""
                                } finally {
                                    archiveArtifacts 'reports/**, test_root/log/**'
                                    junit 'reports/**/*.xml'
                                }
                            }
                        }
                    } finally {
                        deleteDir()
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

podTemplate(cloud: k8sCloud, label: 'edxapp', containers: [
        containerTemplate(name: 'edxapp',
            image: dockerImage,
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
