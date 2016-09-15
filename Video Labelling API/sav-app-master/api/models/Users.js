/**
 * Users.js
 *
 * @description :: TODO: You might write a short summary of how this model works and what it represents here.
 * @docs        :: http://sailsjs.org/documentation/concepts/models-and-orm/models
 */

var bcrypt = require('bcrypt');

module.exports = {

  attributes: {
    name:{
      type: "string",
      required: true
    },
    email:{
      type: "string",
      unique: true,
      required: true,
      email: true
    },
    password: {
      type: "string",
      required: true

    },
    salt: {
      type: "string",
      required: true
    },
    tokenAPI: {
      type: "string"
    }
  },
  signup: function(data, callback) {
    var salt = bcrypt.genSaltSync(10);
    Users.create({
      name: data.name,
      email: data.email,
      salt: salt,
      password: bcrypt.hashSync(data.password, salt)
    }).exec(function(err,created){
      callback(err,created)
    });
  },
  login: function(data, callback) {
    Users.findOne({email: data.email}).exec(function(err,found){
      if (bcrypt.compareSync(data.password, found.password)){
        callback(err,found);
      } else {
        callback(1,found);
      }
    })
  },
  getToken: function(data,callback) {
    Users.findOne(data).exec(function(err,found){
      if (!found.hasOwnProperty("tokenAPI")) callback(err,undefined);
      else callback(err,found.tokenAPI);
    });
  },
  updateToken: function(data,callback){
    require('crypto').randomBytes(24, function(err, buffer) {
    var token = buffer.toString('hex');

    Users.update(data, {tokenAPI: token}).exec(function(err,found){
      callback(err,found.token)
    })
  });
  }

};
