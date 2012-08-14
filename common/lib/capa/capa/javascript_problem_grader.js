require('coffee-script');
var importAll = function (modulePath) {
  module = require(modulePath);
  for(key in module){
    global[key] = module[key];
  }
}

importAll("xproblem");

graderModulePath    = process.argv[2];
dependencies        = JSON.parse(process.argv[3]);
submission          = JSON.parse(process.argv[4]);
problemState        = JSON.parse(process.argv[5]);
params              = JSON.parse(process.argv[6]);

for(var i = 0; i < dependencies.length; i++){
    importAll(dependencies[i]);
}

graderModule = require(graderModulePath);
graderClass  = graderModule.graderClass;
grader = new graderClass(submission, problemState, params);
console.log(JSON.stringify(grader.grade()));
console.log(JSON.stringify(grader.evaluation));
console.log(JSON.stringify(grader.solution));
