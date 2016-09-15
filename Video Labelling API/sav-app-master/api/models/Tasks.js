/**
 * Tasks.js
 *
 * @description :: TODO: You might write a short summary of how this model works and what it represents here.
 * @docs        :: http://sailsjs.org/documentation/concepts/models-and-orm/models
 */

module.exports = {
  attributes: {
    file: {
      type: "array",
      required: true
    },
    name: {
      type: "string",
      required: true
    },
    userId: {
      type: "integer",
      required: true
    },
    type: {
      type: "string",
      required: true
    },
    status: {
      type: "string",
      required: true
    },
    dataKeyFrames: {
      type: "array"
    },
    dataClassify: {
      type: "json",
    },
    timeList: {
      type: "array"
    }
  }
};
