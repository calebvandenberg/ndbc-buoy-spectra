var express = require('express');
var router = express.Router();
var path = require('path');
var set_flags = require('./set_flags');



/* GET buoy page. */
router.get('/', function(req, res, next) {
  var buoy_id = req.query.buoy_id;
  set_flags.run_script();
	res.send(buoy_id);
});


module.exports = router;
