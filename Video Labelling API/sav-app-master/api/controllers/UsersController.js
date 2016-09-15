/**
 * UsersController
 *
 * @description :: Server-side logic for managing users
 * @help        :: See http://sailsjs.org/#!/documentation/concepts/Controllers
 */

var redis = require('redis');
client = redis.createClient();


module.exports = {
	renderLogin: function(req,res){
		res.view('login');
	},
	renderSignup: function(req,res){
		res.view('signup');
	},
	renderToken: function(req,res){
		Users.getToken(req.session.token, function(err,token){
			return res.view('token',{token: token});
		});
	},
	generateToken: function(req,res){
		Users.updateToken(req.session.token, function(err,token){
			if (err) console.log(err);
			return res.redirect('/token');
		});
	},
	login: function(req,res){
		Users.login(req.body, function(err,found){
			if (err === 1) console.log("wrong password");
			else if (err) console.log(err);
			else {
				req.session.token = found.id;
				req.session.name = found.name;
				req.session.authenticated = true;
				res.redirect('/');
			}
		});
	},
	signup: function(req,res){
		if (req.body.password === req.body.password){
				Users.signup(req.body, function(err,created){
					if (err) console.log(err);
				});
		}
		res.redirect('/login');
	},
	authenticateApi: function(req,res){
		Users.login(req.body, function(err,found){
			if (err === 1) console.log(err);
			else if (err) console.log(err);
			else if (req.body.token != found.tokenAPI) console.log("Wrong Token");
			else {
				client.set(found.tokenAPI,found.id);
				client.expire(found.tokenAPI,86400);
				res.json({"session": found.tokenAPI});
			}
		});
	},
	isAuthenticatedApi: function(req,res){
		client.get(req.query.token, function(err, value){
			console.log(value);
			if (err) res.json({err: err});
			else if (value===null) res.json({err: "Not authenticated"});
			else res.json({session: value});
		})
	}
};
