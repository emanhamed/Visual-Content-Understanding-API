/**
 * TasksController
 *
 * @description :: Server-side logic for managing tasks
 * @help        :: See http://sailsjs.org/#!/documentation/concepts/Controllers
 */

var mmm = require('mmmagic');
var redis = require('redis');
var amqp = require('amqplib/callback_api');

clientRedis = redis.createClient();

module.exports = {
	pushJob: function(req,res){
		clientRedis.get(req.body.token, function(err, value){
			if (err) res.json({err:err});
			else if (value === null) res.json({err: "Not authenticated"});
			else {
				req.file('data').upload({
						maxBytes: 1500000000
				}, function(err, uploaded){
					if (err) res.json({ err:err });
					else {
						Magic = mmm.Magic;
						var magic = new Magic(mmm.MAGIC_MIME_TYPE);
						magic.detectFile(uploaded[0].fd, function(err, filetype) {
							if (err) res.json({ err:err });
							else if (!((filetype.indexOf('image')+1)||(filetype.indexOf('video')+1))) res.json({err: "Not a Valid Image or video file"});
							else {
                var type = filetype.substring(0,5);
								Tasks.create({userId: value, file: [uploaded[0].fd], type: type, status: "added to queue", name: req.body.name}).exec(function(err,created){
									if (err) res.json({err: err});
									else {
                    amqp.connect('amqp://localhost', function(err, conn) {
                      conn.createChannel(function(err,ch){
                        var q = "initialization";
                        ch.assertQueue(q, {durable: true});
                        ch.sendToQueue(q, new Buffer(created.id.toString()));
                        res.json({'status': created.status, 'type': created.type, 'id': created.id});
                      });
                    });
									}
								});
							}
						});
					}
				});
			}
		});
	},
  getJobStatus: function(req,res){
    clientRedis.get(req.query.token, function(err,value){
      Tasks.findOne({userId: value, id: req.query.id}).exec(function(err,found){
        if (err) res.json({err: err});
        else if (found === null) res.json({err: "Job doesn't exists"});
        else res.json(found);
      });
    });
  },
  getAllJobs: function(req,res){
    clientRedis.get(req.query.token, function(err,value){
      Tasks.find({userId: value}).exec(function(err,found){
        if (err) res.json({err: err});
        else if (found.length === 0) res.json({err: "no jobs found"});
        else res.json(found);
      });
    });
  },
	searchByLabel: function(req,res){
		clientRedis.get(req.query.token, function(err,value){
      Tasks.findOne({userId: value, id: req.query.id}).exec(function(err,found){
        if (err) res.json({err: err});
        else if (!found) res.json({err: "no jobs found"});
        else {
					var framelist = [];
					Object.keys(found.dataClassify).forEach(function(key) {
						for (var i=0; i<found.dataClassify[key].length; i++){
							if (found.dataClassify[key][i].indexOf(req.query.search)!=-1) framelist.push(key);
						}
					});
					framelist_filtered = framelist.filter(function(elem, pos) {
					    return framelist.indexOf(elem) == pos;
					});
					res.json({framelist: framelist_filtered});
				}
      });
    });
	},
	searchByLabelView: function(req,res){
		if(!req.session.authenticated) return res.redirect('/');
		Tasks.findOne({userId: req.session.token, id: req.param('id')}).exec(function(err,found){
			if (err) console.log(err);
			else if (!found) console.log("no jobs found");
			else {
				var framelist = [];
				Object.keys(found.dataClassify).forEach(function(key) {
					for (var i=0; i<found.dataClassify[key].length; i++){
						if (found.dataClassify[key][i].indexOf(req.query.search)!=-1) framelist.push(key);
					}
				});
				framelist_filtered = framelist.filter(function(elem, pos) {
						return framelist.indexOf(elem) == pos;
				});
				var timelist = []
				var imagelist = []
				var labels = []
				for (var i=0; i<framelist_filtered.length; i++){
					timelist.push(found.timeList[found.dataKeyFrames.indexOf(parseInt(framelist_filtered[i]))]);
					imagelist.push(found.file[found.dataKeyFrames.indexOf(parseInt(framelist_filtered[i]))]);
					labels.push(found.dataClassify[framelist_filtered[i]])
				}
				res.view('search', {times: timelist, imagelist: imagelist, labels: labels});
			}
		});
	},
	renderJobs: function(req,res){
		if(!req.session.authenticated) return res.redirect('/');
		Tasks.find({userId: req.session.token}).exec(function(err,found){
			if(err) console.log(err);
			else res.view('jobs', {data: found});
		});
	},
	renderJob: function(req,res){
		if(!req.session.authenticated) return res.redirect('/');
		Tasks.findOne({userId: req.session.token, id: req.param('id')}).exec(function(err,found){
			if(err) console.log(err);
			else res.view('job', {data: found});
		});
	},
	renderPushJob: function(req,res){
		if(!req.session.authenticated) return res.redirect('/');
		else res.view('pushjob');
	}
};
