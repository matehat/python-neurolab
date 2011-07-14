(function() {
  var __slice = Array.prototype.slice, __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  (function($) {
    var GraphPatch, Grapher, ScalogramGrapher, ScalogramGroupGrapher, ScalogramSubGrapher, SubGraphPatch, SubWaveGrapher, WaveGrapher, WaveGroupGrapher;
    if (!('min' in Math)) {
      Math.min = function() {
        var num, numbers, sm, _i, _len, _results;
        numbers = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
        sm = null;
        _results = [];
        for (_i = 0, _len = numbers.length; _i < _len; _i++) {
          num = numbers[_i];
          _results.push(sm == null ? sm = num : sm = num < sm ? num : sm);
        }
        return _results;
      };
    }
    Grapher = (function() {
      function Grapher(element) {
        var jq;
        jq = this.jq = $(element);
        this.data = function(key, value) {
          return jq.attr("data-" + key, value);
        };
        this.numData = function(key, value) {
          var val;
          if (value != null) {
            return this.data(key, new String(value));
          } else {
            val = parseFloat(this.data(key));
            if (_.isNaN(val)) {
              return null;
            } else {
              return val;
            }
          }
        };
      }
      return Grapher;
    })();
    GraphPatch = (function() {
      function GraphPatch(grapher, i, j) {
        this.grapher = grapher;
        this.wall = grapher.wall;
        this.i = i;
        this.j = j;
      }
      GraphPatch.prototype.W = function() {
        return this.grapher.pW;
      };
      GraphPatch.prototype.H = function() {
        return this.grapher.pH;
      };
      GraphPatch.prototype.scales = function() {
        return this.grapher.scales();
      };
      GraphPatch.prototype.left = function() {
        return this.i * this.W();
      };
      GraphPatch.prototype.top = function() {
        return this.j * this.H();
      };
      GraphPatch.prototype.width = function() {
        return Math.min(this.W(), this.grapher.wW() - this.left());
      };
      GraphPatch.prototype.height = function() {
        return Math.min(this.H(), this.grapher.wH() - this.top());
      };
      GraphPatch.prototype.valid = function() {
        return this.left() < this.grapher.wW() && this.top() < this.grapher.wH();
      };
      GraphPatch.prototype.draw = function() {
        var url, _h, _ref, _w;
        this.element = $("<div class=\"graphic-patch\" />");
        _ref = [this.height(), this.width()], _h = _ref[0], _w = _ref[1];
        url = "/g/" + this.grapher.oid + "/" + _w + "x" + _h + ".png?" + ($.param(this.params()));
        return this.element.appendTo(this.wall).css({
          position: 'absolute',
          left: "" + (this.left()) + "px",
          top: "" + (this.top()) + "px",
          width: "" + _w + "px",
          height: "" + _h + "px",
          'background-image': "url(" + url + ")"
        });
      };
      GraphPatch.prototype.params = function() {
        var scales, _x, _y;
        scales = this.scales();
        return {
          x_start: _x = this.left() * scales.x + this.grapher.xRange[0],
          x_stop: _x + this.width() * scales.x,
          y_stop: _y = this.grapher.yRange[1] - this.top() * scales.y,
          y_start: _y - this.height() * scales.y
        };
      };
      return GraphPatch;
    })();
    SubGraphPatch = (function() {
      __extends(SubGraphPatch, GraphPatch);
      function SubGraphPatch() {
        SubGraphPatch.__super__.constructor.apply(this, arguments);
      }
      SubGraphPatch.prototype.params = function() {
        return _.extend(SubGraphPatch.__super__.params.call(this), {
          index: this.grapher.data('index')
        });
      };
      return SubGraphPatch;
    })();
    WaveGrapher = (function() {
      __extends(WaveGrapher, Grapher);
      function WaveGrapher(element) {
        var _ref;
        Grapher.call(this, element);
        this.xRange = [this.numData('xmin'), this.numData('xmax')];
        this.yRange = [this.numData('ymin'), this.numData('ymax')];
        this.xDelta = this.xRange[1] - this.xRange[0];
        this.yDelta = this.yRange[1] - this.yRange[0];
        this.jq.height((_ref = this.numData('image-height')) != null ? _ref : 200);
        this.wall = $('<div class="graphic-wall" />').appendTo(this.jq);
        this.patches = {};
        this.oid = this.data('oid');
      }
      WaveGrapher.Patch = GraphPatch;
      WaveGrapher.prototype.wW = function(val) {
        var _ref;
        return (_ref = this.numData('fullwidth', val)) != null ? _ref : this.jW();
      };
      WaveGrapher.prototype.wH = function(val) {
        var _ref;
        return (_ref = this.numData('fullheight', val)) != null ? _ref : this.jH();
      };
      WaveGrapher.prototype.jW = function() {
        return this.jq.width();
      };
      WaveGrapher.prototype.jH = function() {
        return this.jq.height();
      };
      WaveGrapher.prototype.scales = function() {
        return {
          x: this.xDelta / (this.wW()),
          y: this.yDelta / (this.wH())
        };
      };
      WaveGrapher.prototype.drawPatches = function(x, y) {
        var i, j, patch, r1, r2, res, _i, _j, _len, _m, _n, _ref, _ref2, _ref3, _results, _results2;
        res = [];
        _ref3 = r1 = (function() {
          _results2 = [];
          for (var _j = _ref = (_m = Math.floor(x / this.pW)), _ref2 = _m + Math.ceil(this.jW() / this.pW); _ref <= _ref2 ? _j <= _ref2 : _j >= _ref2; _ref <= _ref2 ? _j++ : _j--){ _results2.push(_j); }
          return _results2;
        }).apply(this, arguments);
        _results = [];
        for (_i = 0, _len = _ref3.length; _i < _len; _i++) {
          i = _ref3[_i];
          _results.push((function() {
            var _k, _l, _len2, _ref4, _ref5, _ref6, _results3, _results4;
            _ref6 = r2 = (function() {
              _results4 = [];
              for (var _l = _ref4 = (_n = Math.floor(y / this.pH)), _ref5 = _n + Math.ceil(this.jH() / this.pH); _ref4 <= _ref5 ? _l <= _ref5 : _l >= _ref5; _ref4 <= _ref5 ? _l++ : _l--){ _results4.push(_l); }
              return _results4;
            }).apply(this, arguments);
            _results3 = [];
            for (_k = 0, _len2 = _ref6.length; _k < _len2; _k++) {
              j = _ref6[_k];
              if (!(this.patches["" + i + "," + j] != null)) {
                patch = new this.constructor.Patch(this, i, j);
                if (!patch.valid()) {
                  continue;
                }
                (this.patches["" + i + "," + j] = patch).draw();
              }
            }
            return _results3;
          }).call(this));
        }
        return _results;
      };
      WaveGrapher.prototype.draw = function() {
        var pos;
        pos = this.wall.position();
        return this.drawPatches(pos.left * -1, pos.top * -1);
      };
      WaveGrapher.prototype.rescale = function() {
        var k, _results;
        this.wall.height(this.wH());
        this.wall.width(this.wW());
        _results = [];
        for (k in this.patches) {
          this.patches[k].destroy();
          _results.push(del(this.patches[k]));
        }
        return _results;
      };
      WaveGrapher.prototype.prepare = function() {
        var _ref;
        this.jq.css({
          position: 'relative',
          overflow: 'hidden'
        });
        this.wall.css({
          position: 'absolute',
          top: "0px",
          left: "0px"
        });
        _ref = [this.jW(), this.jH()], this.pW = _ref[0], this.pH = _ref[1];
        this.rescale();
        this.wall.draggable({
          scroll: false
        });
        this.wall.bind('drag', __bind(function(event, ui) {
          var drag;
          drag = this.wall.data('draggable').position;
          if (drag.left > 0) {
            drag.left = 0;
          } else if (drag.left < -(this.wW() - this.pW)) {
            drag.left = -(this.wW() - this.pW);
          }
          if (drag.top > 0) {
            drag.top = 0;
          } else if (drag.top < -(this.wH() - this.pH)) {
            drag.top = -(this.wH() - this.pH);
          }
          return this.jq.trigger('walldrag', [drag]);
        }, this));
        this.jq.bind('walldrag', __bind(function(event, drag) {
          return this.draw();
        }, this));
        return this.draw();
      };
      return WaveGrapher;
    })();
    SubWaveGrapher = (function() {
      __extends(SubWaveGrapher, WaveGrapher);
      function SubWaveGrapher() {
        SubWaveGrapher.__super__.constructor.apply(this, arguments);
      }
      SubWaveGrapher.prototype.prepare = function() {
        SubWaveGrapher.__super__.prepare.call(this);
        return this.jq.css('position', 'absolute');
      };
      SubWaveGrapher.Patch = SubGraphPatch;
      return SubWaveGrapher;
    })();
    WaveGroupGrapher = (function() {
      __extends(WaveGroupGrapher, Grapher);
      function WaveGroupGrapher(element) {
        var num, prop, _ref;
        Grapher.call(this, element);
        this.xRange = [this.numData('xmin'), this.numData('xmax')];
        this.yRanges = (function() {
          var _i, _len, _ref, _results;
          _ref = ['ymins', 'ymaxs'];
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            prop = _ref[_i];
            _results.push((function() {
              var _j, _len2, _ref2, _results2;
              _ref2 = _.words(this.data(prop), ',');
              _results2 = [];
              for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
                num = _ref2[_j];
                _results2.push(parseFloat(num));
              }
              return _results2;
            }).call(this));
          }
          return _results;
        }).call(this);
        this.count = this.numData('count');
        this.oid = this.data('oid');
        this.jq.height((_ref = this.numData('image-height')) != null ? _ref : this.count * 100);
      }
      WaveGroupGrapher.prototype.prepare = function() {
        var gH, gW, i, _ref, _results;
        gH = Math.floor(this.jq.height() / this.count);
        gW = this.jq.width();
        this.graphers = [];
        this.jq.css({
          position: 'relative'
        });
        _results = [];
        for (i = 0, _ref = this.count; 0 <= _ref ? i < _ref : i > _ref; 0 <= _ref ? i++ : i--) {
          _results.push(__bind(function(i) {
            var g;
            g = $('<div class=\"graphic-subgraph\" />').appendTo(this.jq);
            g.height(gH);
            g.width(gW);
            g.attr({
              'data-xmin': this.xRange[0],
              'data-xmax': this.xRange[1],
              'data-ymin': this.yRanges[0][i],
              'data-ymax': this.yRanges[1][i],
              'data-fullwidth': this.data('fullwidth'),
              'data-fullheight': this.data('fullheight'),
              'data-image-height': gH,
              'data-oid': this.oid,
              'data-index': i
            });
            g.css({
              top: "" + (i * gH) + "px",
              left: "0px",
              position: 'absolute'
            });
            g = this.graphers[i] = new SubWaveGrapher(g);
            g.prepare();
            return g.jq.bind('walldrag', __bind(function(event, drag) {
              var j, _ref2, _results2;
              _results2 = [];
              for (j = 0, _ref2 = this.count; 0 <= _ref2 ? j < _ref2 : j > _ref2; 0 <= _ref2 ? j++ : j--) {
                if (i === j) {
                  continue;
                }
                this.graphers[j].wall.css('left', "" + drag.left + "px");
                _results2.push(this.graphers[j].draw());
              }
              return _results2;
            }, this));
          }, this)(i));
        }
        return _results;
      };
      return WaveGroupGrapher;
    })();
    ScalogramGrapher = (function() {
      __extends(ScalogramGrapher, WaveGrapher);
      function ScalogramGrapher(element) {
        var _ref;
        Grapher.call(this, element);
        this.xRange = [this.numData('xmin'), this.numData('xmax')];
        this.yRange = [this.numData('ymin'), this.numData('ymax')];
        this.vRange = [this.numData('vmin'), this.numData('vmax')];
        this.xDelta = this.xRange[1] - this.xRange[0];
        this.yDelta = this.yRange[1] - this.yRange[0];
        this.jq.height((_ref = this.numData('image-height')) != null ? _ref : 200);
        this.wall = $('<div class="graphic-wall" />').appendTo(this.jq);
        this.patches = {};
        this.oid = this.data('oid');
      }
      ScalogramGrapher.Patch = GraphPatch;
      return ScalogramGrapher;
    })();
    ScalogramSubGrapher = (function() {
      __extends(ScalogramSubGrapher, ScalogramGrapher);
      function ScalogramSubGrapher() {
        ScalogramSubGrapher.__super__.constructor.apply(this, arguments);
      }
      ScalogramSubGrapher.prototype.prepare = function() {
        ScalogramSubGrapher.__super__.prepare.call(this);
        return this.jq.css('position', 'absolute');
      };
      ScalogramSubGrapher.Patch = SubGraphPatch;
      return ScalogramSubGrapher;
    })();
    ScalogramGroupGrapher = (function() {
      __extends(ScalogramGroupGrapher, WaveGroupGrapher);
      function ScalogramGroupGrapher(element) {
        var num, prop, _ref;
        Grapher.call(this, element);
        this.xRange = [this.numData('xmin'), this.numData('xmax')];
        this.yRange = [this.numData('ymin'), this.numData('ymax')];
        this.vRanges = (function() {
          var _i, _len, _ref, _results;
          _ref = ['vmins', 'vmaxs'];
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            prop = _ref[_i];
            _results.push((function() {
              var _j, _len2, _ref2, _results2;
              _ref2 = _.words(this.data(prop), ',');
              _results2 = [];
              for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
                num = _ref2[_j];
                _results2.push(parseFloat(num));
              }
              return _results2;
            }).call(this));
          }
          return _results;
        }).call(this);
        this.count = this.numData('count');
        this.oid = this.data('oid');
        this.jq.height((_ref = this.numData('image-height')) != null ? _ref : this.count * 100);
      }
      ScalogramGroupGrapher.prototype.prepare = function() {
        var gH, gW, i, _ref, _results;
        gH = Math.floor(this.jq.height() / this.count);
        gW = this.jq.width();
        this.graphers = [];
        this.jq.css({
          position: 'relative'
        });
        console.log('Preparing', this.count);
        _results = [];
        for (i = 0, _ref = this.count; 0 <= _ref ? i < _ref : i > _ref; 0 <= _ref ? i++ : i--) {
          _results.push(__bind(function(i) {
            var g;
            console.log(i);
            g = $('<div class=\"graphic-subgraph\" />').appendTo(this.jq);
            g.height(gH);
            g.width(gW);
            g.attr({
              'data-xmin': this.xRange[0],
              'data-xmax': this.xRange[1],
              'data-ymin': this.yRange[0],
              'data-ymax': this.yRange[1],
              'data-vmin': this.vRanges[0][i],
              'data-vmax': this.vRanges[1][i],
              'data-fullwidth': this.data('fullwidth'),
              'data-fullheight': this.data('fullheight'),
              'data-image-height': gH,
              'data-oid': this.oid,
              'data-index': i
            });
            g.css({
              top: "" + (i * gH) + "px",
              left: "0px",
              position: 'absolute'
            });
            g = this.graphers[i] = new ScalogramSubGrapher(g);
            console.log(g, this.jq);
            g.prepare();
            return g.jq.bind('walldrag', __bind(function(event, drag) {
              var j, _ref2, _results2;
              _results2 = [];
              for (j = 0, _ref2 = this.count; 0 <= _ref2 ? j < _ref2 : j > _ref2; 0 <= _ref2 ? j++ : j--) {
                if (i === j) {
                  continue;
                }
                this.graphers[j].wall.css('left', "" + drag.left + "px");
                _results2.push(this.graphers[j].draw());
              }
              return _results2;
            }, this));
          }, this)(i));
        }
        return _results;
      };
      return ScalogramGroupGrapher;
    })();
    return this.$G = {
      'wave': WaveGrapher,
      'wave-group': WaveGroupGrapher,
      'scalogram': ScalogramGrapher,
      'scalogram-group': ScalogramGroupGrapher
    };
  })(jQuery);
}).call(this);
