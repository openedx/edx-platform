var importAll = function (modulePath) {
  module = require(modulePath);
  for(key in module){
    global[key] = module[key];
  }
}

importAll("xproblem");
importAll("minimax.js");

graderModulePath    = process.argv[2];
submission          = JSON.parse(process.argv[3]);
problemState        = JSON.parse(process.argv[4]);
params              = JSON.parse(process.argv[5]);

graderModule = require(graderModulePath);
graderClass  = graderModule.graderClass;
grader = new graderClass(submission, problemState, params);
console.log(JSON.stringify(grader.grade()));
console.log(JSON.stringify(grader.evaluation));
console.log(JSON.stringify(grader.solution));
