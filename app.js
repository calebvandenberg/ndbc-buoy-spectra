var express = require('express');
var path = require('path');
var favicon = require('serve-favicon');
var logger = require('morgan');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser');
var routes = require('./routes/index');
var users = require('./routes/users');
var exec = require('child_process').exec;

var app = express();

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// uncomment after placing your favicon in /public
//app.use(favicon(path.join(__dirname, 'public', 'favicon.ico')));
app.use(logger('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', routes);
app.use('/users', users);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  var err = new Error('Not Found');
  err.status = 404;
  next(err);
});

// error handlers

// development error handler
// will print stacktrace
if (app.get('env') === 'development') {
  app.use(function(err, req, res, next) {
    res.status(err.status || 500);
    res.render('error', {
      message: err.message,
      error: err
    });
  });
}

var pyArgs = {
  // make arguments that take no parameters (ie, --json) true or false
  "buoy": '46232',
  "datasourceno": 'http',
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

var pyPath = '/var/scripts';
var buoyData = ''
var execstr = 'python ' + path.join(pyPath, 'ndbc.py') + flagGen(pyArgs);
//console.log(execstr);
var child = exec(execstr, function(error, stdout, stderr) {
  if (error) {
    console.log(stderr)
  }
  else {
    buoyData= JSON.parse(stdout);
    console.log(buoyData);
  }
});

//var PythonShell = require('python-shell');
//
//var options = {
//  mode: 'text',
//  pythonOptions: ['-b'],
//  scriptPath: './',
//  args: [46232]
//};
//
//PythonShell.run('ndbc.py', options, function (err, results) {
//  if (err) throw err;
//  // results is an array consisting of messages collected during execution
//  console.log('results: %j', results);
//});

// production error handler
// no stacktraces leaked to user
app.use(function(err, req, res, next) {
  res.status(err.status || 500);
  res.render('error', {
    message: err.message,
    error: {}
  });
});


module.exports = app;
