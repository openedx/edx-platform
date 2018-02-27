def makeNode(suite, shard) {
  return {
    echo "I am ${suite}:${shard}, and the worker is yet to be started!"

								node('edxapp') {
										container('edxapp') {
      // Cleaning up previous builds. Heads up! Not sure if `WsCleanup` actually works.
      step([$class: 'WsCleanup'])

      checkout scm

      sh 'git log --oneline | head'

      timeout(time: 55, unit: 'MINUTES') {
        echo "Hi, it is me ${suite}:${shard} again, the worker just started!"

        try {
          if (suite == 'accessibility') {
            sh './scripts/accessibility-tests.sh'
          } else {
            withEnv(["TEST_SUITE=${suite}", "SHARD=${shard}"]) {
              sh './scripts/all-tests.sh'
            }
          }
        } finally {
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
    [name: 'lms-acceptance', 'shards': ['all']],
    [name: 'cms-acceptance', 'shards': ['all']],
    [name: 'bok-choy', 'shards': [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
    ]],
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
    containerTemplate(name: 'edxapp', image: 'gcr.io/appsembler-testing/jenkins-worker:v0.1.3', ttyEnabled: true, 
        command: 'cat')    
  ]) {
stage('Prepare') {
  echo 'Starting the build...'
  echo 'It it always nice to have a green checkmark :D'
}

stage('Test') {
  // This commit should be removed via
  parallel buildParallelSteps()
}

stage('Done') {
  echo 'I am done, hurray!'
}

}




