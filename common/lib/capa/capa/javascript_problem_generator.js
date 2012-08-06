var importAll = function (modulePath) {
  module = require(modulePath);
  for(key in module){
    global[key] = module[key];
  }
}

importAll("mersenne-twister-min");
importAll("xproblem");

generatorModulePath = process.argv[2];
seed                = process.argv[3];
params              = JSON.parse(process.argv[4]);

if(seed==null){
    seed = 4;
}else{
    seed = parseInt(seed);
}

generatorModule = require(generatorModulePath);
generatorClass  = generatorModule.generatorClass;
generator = new generatorClass(seed, params);
console.log(JSON.stringify(generator.generate()));
