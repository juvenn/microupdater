/* Microupdater Controller
 * (c) 2009 Juvenn Woo
 *
 * http://twitter.com/juvenn
 *
 */

var PageInator = Class.create({
  initialize: function(selector, len) {
    this.slices = $$(selector).eachSlice(len);
    this.pageIndex = 0;
    $$('li.entry').invoke('hide');
    $$('#epi > span.lt').invoke('hide');
    this.update();
  },
  
  reset: function() {
    this.slices[this.pageIndex].invoke('hide');
    $$('#epi > span').invoke('show')
  },

  update: function() {
    this.slices[this.pageIndex].invoke('show');
    $('epiStatus').update('Page ' + (this.pageIndex + 1));
  },

  prev: function() {
    this.reset();
    this.pageIndex -= 1;
    if (this.pageIndex <= 0) {
      this.pageIndex = 0;
      $$('#epi > span.lt').invoke('hide');
    }
    this.update();
  },

  next: function() {
    this.reset();
    this.pageIndex += 1;
    if (this.pageIndex >= this.slices.length - 1) {
      this.pageIndex = this.slices.length - 1;
      $$('#epi > span.rt').invoke('hide')
    }
    this.update();
  },

  first: function() {
    this.reset();
    this.pageIndex = 0;
    $$('#epi > span.lt').invoke('hide');
    this.update();
  },

  last: function() {
    this.reset();
    this.pageIndex = this.slices.length - 1;
    $$('#epi > span.rt').invoke('hide');
    this.update();
  },
});

// Entry's PageInator
var epi;
document.observe('dom:loaded', function() {
  epi = new PageInator('li.entry', 25);
});
