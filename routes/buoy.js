var express = require('express');
var router = express.Router();
var path = require('path');
var set_flags = require('./set_flags');



/* GET buoy page. */
router.get('/', function(req, res, next) {
  var buoy_id = req.query.buoy_id;
  var buoyData = set_flags.run_script();
	res.send(set_flags.run_script());
});


module.exports = router;
