var express = require('express');
var router = express.Router();
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
//example
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

var pyPath = './';
var buoyData = ''
var execstr = 'python ' + path.join(pyPath, 'ndbc.py') + flagGen(pyArgs);
var child = exec(execstr, function(error, stdout, stderr) {
  if (error) {
    console.log(stderr)
  }
  else {
    buoyData= JSON.parse(stdout);
    console.log(buoyData);
  }
});

/* GET buoy page. */
router.get('/', function(req, res, next) {
  var buoy_id = req.query.buoy_id;
	res.send(buoy_id);
});


module.exports = router;
