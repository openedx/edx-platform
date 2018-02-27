podTemplate(label: 'ubuntu-k8s', containers: [
    containerTemplate(name: 'ubuntu', image: 'ubuntu:16.04', ttyEnabled: true, 
        command: 'cat')    
  ]) {
    node('ubuntu-k8s') {
        container('ubuntu') {
            stage('Run Command') {
                sh 'cat /etc/issue'
            }
        }
    }
}
