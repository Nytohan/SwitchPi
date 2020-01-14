var express = require('express');
var router = express.Router();

const session = require('express-session')

/* GET home page. */
router.get('/', function(req, res, next) {

res.render('index', { title: 'SwitchPi Controller', session: req.session });


});


module.exports = router;
