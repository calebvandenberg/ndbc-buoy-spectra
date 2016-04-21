var path = require('path');
var exec = require('child_process').exec;

var pyArgs = {
  // make arguments that take no parameters (ie, --json) true or false
  "buoy": '46232',
  "datasource": 'http',
  "json": true,
  "datatype": "spectra",
  "units": 'ft'
};

pyArgs.datatype = '9band';

function flagGen(args) {
  var flags = '';
  for (var a in args) {
    if (args.hasOwnProperty(a)) {
      if (typeof(pyArgs[a]) == 'string'){
        flags += " --" + a + ' ' + pyArgs[a];
      }
      else {
        if (pyArgs[a] == true)
          flags += ' --' + a;
      }
    }
  }
  return flags;
}

function run_script(){
  var buoyData = ''
  var execstr = 'python ' + path.join('./', 'ndbc.py') + flagGen(pyArgs);
  var child = exec(execstr, function(error, stdout, stderr) {
    if (error) {
      console.log(stderr)
    }
    else {
      buoyData= JSON.parse(stdout);
      console.log(buoyData);
    }
  });
  return buoyData;
}

module.exports.run_script = run_script;