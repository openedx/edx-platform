;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'backbone',
            'js/arbisoft_exam/models/QuestionBlockModel'
        ],
        function($, _, Backbone, QuestionBlockModel) {
            return Backbone.View.extend({
              container: '#arbi-exam',
              template: _.template($('#arbisoft_exam').html()),
              questionBlocks: [],
              currentBlockIndex: 0,
              lastBlockIndex: 0,
              initialize: function (items) {
                  var QuestionBlockCollection = Backbone.Collection.extend({
                      model: QuestionBlockModel
                  });
                  this.questionBlocks = new QuestionBlockCollection(items);
                  this.lastBlockIndex = items.length - 1;

                  $('button.next').on('click', _.bind(this.loadNext, this));
                  $('button.previous').on('click', _.bind(this.loadPrevious, this));
                  $('a.question-link').on('click', _.bind(this.loadIndex, this));

                  this.renderCurrent();
              },
              loadNext: function(){
                  this.currentBlockIndex += 1;
                  this.renderCurrent();
              },
              loadPrevious: function(){
                  this.currentBlockIndex -= 1;
                  this.renderCurrent();
              },
              loadIndex: function(evt){
                  evt.preventDefault();
                  var questionIndex = $(evt.target).data('index');
                  this.currentBlockIndex = parseInt(questionIndex);
                  this.renderCurrent();
              },
              renderCurrent: function () {
                  var currentIndex = this.currentBlockIndex;
                  var currentBlock = this.questionBlocks.models[currentIndex];
                  this._render(currentBlock);
                  this._updateButtons();
                  this._updateNav();

                  return this;
              },
              _updateNav: function () {
                  $('a.highlight').removeClass('highlight');
                  $('a.question-link[data-index=' + this.currentBlockIndex + ']').addClass('highlight');
              },
              _updateButtons: function () {
                  if(this.currentBlockIndex > 0) {
                      this._enablePrevious();
                      if(this.currentBlockIndex >= this.lastBlockIndex) {
                          this._disableNext();
                      }else{
                          this._enableNext();
                      }
                  }
                  else{
                      this._enableNext();
                      this._disablePrevious();
                  }
              },
              _render: function (block) {
                  var url = "/xblock/" + block.attributes.id;
                  $(this.container).html(this.template({
                      url: url
                  }));
              },
              _disableNext: function () {
                   $('button.next').addClass('disabled');
              },
              _enableNext: function () {
                   $('button.next').removeClass('disabled');
              },
              _disablePrevious: function () {
                  $('button.previous').addClass('disabled');
              },
              _enablePrevious: function () {
                  $('button.previous').removeClass('disabled');
              }
            });
        }
    );
}).call(this, define || RequireJS.define);

