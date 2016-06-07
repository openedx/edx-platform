require('coffee-script');
var importAll = function (modulePath) {
  module = require(modulePath);
  for(key in module){
    global[key] = module[key];
  }
}

importAll("mersenne-twister-min");
importAll("xproblem");

generatorModulePath = process.argv[2];
dependencies        = JSON.parse(process.argv[3]);
seed                = JSON.parse(process.argv[4]);
params              = JSON.parse(process.argv[5]);

if(seed==null){
    seed = 4;
}

for(var i = 0; i < dependencies.length; i++){
    importAll(dependencies[i]);
}

generatorModule = require(generatorModulePath);
generatorClass  = generatorModule.generatorClass;
generator = new generatorClass(seed, params);
console.log(JSON.stringify(generator.generate()));
