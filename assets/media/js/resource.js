(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; }, __slice = Array.prototype.slice, __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  };
  (function($) {
    var Block, BlockBase, BlockTemplate, Component, ComponentBase, EVENTS, Observable, ObservableBase, Protocol, Reference, References, Resource, Serializer, root;
    root = this;
    References = function(path, _type) {
      return function(callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this["new"]) {
          return;
        }
        return Resource._request(this.requestURL(path), 'GET', {}, __bind(function(data) {
          var obj, objects, _i, _len, _obj;
          if (data.errors != null) {
            return error(data);
          }
          objects = [];
          for (_i = 0, _len = data.length; _i < _len; _i++) {
            obj = data[_i];
            if (obj._type !== _type.name) {
              continue;
            }
            _obj = _type["new"](obj);
            _type.trigger('fetched', [_obj, data]);
            objects.push(_obj);
          }
          return callback(objects);
        }, this));
      };
    };
    Reference = function(obj, _type) {
      var func;
      if (obj instanceof Resource) {
        return Reference({
          '_type': obj.constructor.name,
          '_id': obj.id()
        }, obj.constructor);
      }
      func = function(callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this["new"] || _type.name === !obj._type) {
          return;
        }
        return _type.query(obj._id, callback, error);
      };
      $.extend(func, obj);
      return func;
    };
    this.Serializer = Serializer = (function() {
      function Serializer() {}
      return Serializer;
    })();
    EVENTS = {
      changed: function(type) {
        return "resourceChanged." + type;
      },
      created: function(type) {
        return "resourceCreated." + type;
      },
      updated: function(type) {
        return "resourceUpdated." + type;
      },
      fetched: function(type) {
        return "resourceFetched." + type;
      },
      deleted: function(type) {
        return "resourceDeleted." + type;
      }
    };
    this.Resource = Resource = (function() {
      function Resource() {}
      Resource._request = function(url, type, data, callback) {
        if (data == null) {
          data = 'GET';
        }
        if (callback == null) {
          callback = (function() {});
        }
        return $.ajax({
          url: url,
          type: type,
          data: data,
          success: callback,
          error: function(xhr, text) {
            return console.error("Error requesting: " + url + ", response: " + text);
          }
        });
      };
      Resource._requestURL = function() {
        var bit, bits, data, key, match, url, _i, _j, _len, _ref;
        bits = 2 <= arguments.length ? __slice.call(arguments, 0, _i = arguments.length - 1) : (_i = 0, []), data = arguments[_i++];
        if (_.isString(data)) {
          (bits = ['base'].concat(__slice.call(bits))).push(data);
        }
        url = (function() {
          var _i, _len, _ref, _results;
          _results = [];
          for (_i = 0, _len = bits.length; _i < _len; _i++) {
            bit = bits[_i];
            _results.push((_ref = this.prototype.urls[bit]) != null ? _ref : bit);
          }
          return _results;
        }).call(this);
        url = url.join('');
        _ref = url.match(/:[a-zA-Z_]{1}[a-zA-Z0-9_]*/) || [];
        for (_j = 0, _len = _ref.length; _j < _len; _j++) {
          match = _ref[_j];
          key = match.slice(1, match.length);
          if (data[key] != null) {
            url = url.replace(match, "" + data[key]);
          }
        }
        return url;
      };
      Resource._serialize = function(data) {
        var key, result, val;
        result = {};
        for (key in data) {
          val = data[key];
          if ($.isPlainObject(val || $.isArray(val))) {
            result[key] = JSON.stringify(val);
          } else if (_.isFunction(val) && (val._type != null) && (val._id != null)) {
            result["" + key + "_id"] = val._id;
            result["" + key + "_type"] = val._type;
          } else if (_.isString(val || _.isNumber(val))) {
            result[key] = val;
          } else {
            continue;
          }
        }
        return result;
      };
      Resource.trigger = function(eventType, data) {
        return $.event.trigger(EVENTS[eventType](this.name), data);
      };
      Resource.bind = function(eventType, data, callback) {
        return $(root).bind(EVENTS[eventType](this.name), data, callback);
      };
      Resource.all = function(params, callback, error) {
        var _ref;
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this.prototype.urls.all == null) {
          return;
        }
        if (_.isFunction(params)) {
          _ref = [params, {}], callback = _ref[0], params = _ref[1];
        }
        return Resource._request(this._requestURL('all'), 'GET', {}, __bind(function(data) {
          var obj, objects, _i, _len, _obj;
          if (data.errors != null) {
            return error(data);
          }
          objects = [];
          for (_i = 0, _len = data.length; _i < _len; _i++) {
            obj = data[_i];
            if (obj._type !== this.name) {
              continue;
            }
            _obj = this["new"](obj);
            this.trigger('fetched', [_obj, data]);
            objects.push(_obj);
          }
          return callback(objects);
        }, this));
      };
      Resource.query = function(id, callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this.prototype.urls.get == null) {
          return;
        }
        return Resource._request(this._requestURL('base', 'get', {
          id: id
        }), 'GET', {}, __bind(function(data) {
          var obj;
          if (data.errors != null) {
            return error(data);
          }
          if (data._type !== this.name) {
            return;
          }
          obj = this["new"](data);
          this.trigger('fetched', [obj, data]);
          return callback(obj);
        }, this));
      };
      Resource["new"] = function(obj) {
        return _.bind(function() {
          this.modified = false;
          this._cache = {};
          this._data = {};
          this.set(obj);
          this["new"] = !(this.get('_id') != null);
          return this;
        }, new this)();
      };
      Resource.prototype.trigger = function(eventType, data) {
        return $.event.trigger(EVENTS[eventType](this.constructor.name), data);
      };
      Resource.prototype.bind = function(eventType, data, callback) {
        return $(root).bind(EVENTS[eventType](this.constructor.name), data, callback);
      };
      Resource.prototype.merge = function(data) {
        this._cache = {};
        this.set(data);
        return this["new"] = false;
      };
      Resource.prototype.set = function(key, value) {
        var k, type;
        if ($.isPlainObject(key)) {
          for (k in key) {
            this.set(k, key[k]);
          }
          return key;
        } else if (value instanceof Resource) {
          value = Reference(value);
        }
        if (!(value !== this.get(key))) {
          return;
        }
        if ((value != null) && (value._type != null) && (value._id != null) && !_.isFunction(value)) {
          if (value._type.match(/[^\w]/) != null) {
            return;
          }
          type = eval(value._type);
          this._data[key] = Reference(value, type);
        } else {
          this._data[key] = value;
        }
        this.modified = true;
        this.trigger('changed', [this, key, value]);
        return value;
      };
      Resource.prototype.get = function(key) {
        return this._data[key];
      };
      Resource.prototype.getAsync = function(key, cached, callback, error) {
        var _cb, _ref;
        if (cached == null) {
          cached = true;
        }
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (_.isFunction(cached)) {
          _ref = [true, cached, callback], cached = _ref[0], callback = _ref[1], error = _ref[2];
        }
        if (!_.isFunction(this._data[key])) {
          return _.defer(__bind(function() {
            return callback(this._data[key], this);
          }, this));
        } else if (cached && (this._cache[key] != null)) {
          return _.defer(__bind(function() {
            return callback(this._cache[key], this);
          }, this));
        } else {
          _cb = __bind(function(value) {
            if (cached) {
              this._cache[key] = value;
            }
            return callback(value, this);
          }, this);
          return this._data[key].apply(this, [_cb, error]);
        }
      };
      Resource.prototype.id = function() {
        var _ref;
        return (_ref = this.get('_id')) != null ? _ref : null;
      };
      Resource.prototype.serialized = function() {
        return this.constructor._serialize(this._data);
      };
      Resource.prototype.requestURL = function() {
        var bits, _ref;
        bits = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
        return (_ref = this.constructor)._requestURL.apply(_ref, ['base'].concat(__slice.call(bits), [{
          id: this.id()
        }]));
      };
      Resource.prototype.save = function(callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this["new"]) {
          return this.create(callback, error);
        } else {
          return this.update(callback, error);
        }
      };
      Resource.prototype.update = function(callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this["new"] || !(this.urls.update != null) || !this.modified) {
          return;
        }
        return Resource._request(this.requestURL('update'), 'POST', this.serialized(), __bind(function(data) {
          if (data.errors != null) {
            return error(data);
          }
          if ((data._id != null) && data._type === this.constructor.name) {
            this.merge(data);
          }
          this.modified = false;
          this.trigger('updated', [this, data]);
          return callback(this);
        }, this));
      };
      Resource.prototype.create = function(callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (!(this["new"] || !(this.urls["new"] != null))) {
          return;
        }
        return Resource._request(this.requestURL('new'), 'POST', this.serialized(), __bind(function(data) {
          if (data.errors != null) {
            return error(data);
          }
          if ((data._id != null) && data._type === this.constructor.name) {
            this.merge(data);
          }
          this.modified = false;
          this.trigger('created', [this, data]);
          return callback(this);
        }, this));
      };
      Resource.prototype["delete"] = function(callback, error) {
        if (callback == null) {
          callback = (function() {});
        }
        if (error == null) {
          error = (function() {});
        }
        if (this["new"] || !(this.urls["delete"] != null)) {
          return;
        }
        return Resource._request(this.requestURL('delete'), 'GET', {}, __bind(function(data) {
          if (data.errors != null) {
            return error(data);
          }
          this.trigger('deleted', [this, data]);
          return callback(this);
        }, this));
      };
      return Resource;
    })();
    this.Component = Component = (function() {
      function Component() {
        Component.__super__.constructor.apply(this, arguments);
      }
      __extends(Component, Resource);
      Component.prototype.urls = {
        base: '/components/',
        "new": "new/",
        get: ":id/",
        update: ":id/update/",
        "delete": ":id/delete/"
      };
      return Component;
    })();
    this.Component.Base = ComponentBase = (function() {
      function ComponentBase() {
        ComponentBase.__super__.constructor.apply(this, arguments);
      }
      __extends(ComponentBase, Resource);
      ComponentBase.prototype.urls = {
        base: '/components/bases/',
        "new": "new/",
        get: ":id/",
        update: ":id/update/",
        "delete": ":id/delete/"
      };
      ComponentBase.prototype.instances = References("instances/", Component);
      return ComponentBase;
    })();
    this.Block = Block = (function() {
      function Block() {
        Block.__super__.constructor.apply(this, arguments);
      }
      __extends(Block, Resource);
      Block.prototype.urls = {
        base: '/blocks/',
        "new": 'new/',
        get: ':id/',
        update: ':id/put/',
        "delete": ':id/delete/'
      };
      Block.prototype.components = References('components/', Component);
      return Block;
    })();
    this.Block.Base = BlockBase = (function() {
      function BlockBase() {
        BlockBase.__super__.constructor.apply(this, arguments);
      }
      __extends(BlockBase, Resource);
      BlockBase.prototype.urls = {
        base: '/blocks/bases/',
        "new": 'new/',
        get: ':id/',
        update: ':id/put/',
        "delete": ':id/delete/'
      };
      BlockBase.prototype.instances = References('instances/', Block);
      BlockBase.prototype.components = References('components/', ComponentBase);
      return BlockBase;
    })();
    this.Block.Template = BlockTemplate = (function() {
      function BlockTemplate() {
        BlockTemplate.__super__.constructor.apply(this, arguments);
      }
      __extends(BlockTemplate, Resource);
      BlockTemplate.prototype.urls = {
        base: '/blocks/templates/',
        "new": 'new/',
        get: ':id/',
        update: ':id/put/',
        "delete": ':id/delete/'
      };
      return BlockTemplate;
    })();
    this.Protocol = Protocol = (function() {
      function Protocol() {
        Protocol.__super__.constructor.apply(this, arguments);
      }
      __extends(Protocol, Resource);
      Protocol.prototype.urls = {
        base: '/protocols/',
        "new": "new/",
        all: "all/",
        get: "/",
        update: "/update/",
        "delete": "/delete/"
      };
      Protocol.prototype.blocks = References("blocks/", BlockTemplate);
      return Protocol;
    })();
    this.Observable = Observable = (function() {
      function Observable() {
        Observable.__super__.constructor.apply(this, arguments);
      }
      __extends(Observable, Resource);
      Observable.prototype.urls = {
        base: '/observables/',
        "new": 'new/',
        get: ':id/',
        update: ':id/put/',
        "delete": ':id/delete/'
      };
      Observable.prototype.blocks = References(':id/blocks/', Block);
      return Observable;
    })();
    this.Observable.Base = ObservableBase = (function() {
      function ObservableBase() {
        ObservableBase.__super__.constructor.apply(this, arguments);
      }
      __extends(ObservableBase, Resource);
      ObservableBase.prototype.urls = {
        base: '/observables/bases/',
        all: 'all/',
        "new": 'new/',
        get: ':id/',
        update: ':id/put/',
        "delete": ':id/delete/'
      };
      ObservableBase.prototype.instances = References(':id/instances/', Observable);
      ObservableBase.prototype.blocks = References(':id/blocks/', BlockBase);
      return ObservableBase;
    })();
    return null;
  })(jQuery);
}).call(this);
