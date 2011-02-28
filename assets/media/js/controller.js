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
    var Controller, EntryView, Inject, ListView, RemoteTemplate, Resource, Serializer, Template, UI, UIButton, UIButtonSet, UIViewExtension, ViewExtension, _ref;
    _ref = [this.Resource, this.Serializer], Resource = _ref[0], Serializer = _ref[1];
    $.controller = function() {
      var args;
      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      return $(document).data('controller');
    };
    $.controller.base = Controller = (function() {
      function Controller() {
        $(document).data('controller', this);
      }
      Controller.prototype.pageReady = function() {};
      Controller.prototype.handleData = function() {};
      return Controller;
    })();
    $(document).ready(function() {
      var _ref;
      return (_ref = $.controller()) != null ? _ref.pageReady(this) : void 0;
    });
    ViewExtension = (function() {
      function ViewExtension() {}
      return ViewExtension;
    })();
    $.template = Template = (function() {
      __extends(Template, ViewExtension);
      function Template(options) {
        this.options = options;
      }
      Template.prototype.extend = function(obj) {
        var _ref, _ref2, _render_templ;
        _render_templ = function(data, cb) {
          if (cb == null) {
            cb = (function() {});
          }
          return cb($.mustache(this.content, data));
        };
        (_ref = this.name) != null ? _ref : this.name = '_';
        (_ref2 = obj._templates) != null ? _ref2 : obj._templates = {};
        obj._templates[this.name] = _render_templ;
        if (!(obj.renderData != null)) {
          obj.renderData = function(data, name, cb) {
            var templ, _ref;
            if (_.isFunction(name)) {
              _ref = [null, name], name = _ref[0], cb = _ref[1];
            }
            if (name != null) {
              templ = this._templates[name];
            } else {
              templ = _.first(_.values(this._templates));
            }
            return templ(data, cb);
          };
        }
        if (obj instanceof ListView && !(obj.insertData != null)) {
          return obj.insertData = function(data, name, i, cb) {
            var _ref, _ref2;
            if (_.isNumber(name)) {
              _ref = [null, name, i], name = _ref[0], i = _ref[1], cb = _ref[2];
            }
            if (_.isFunction(i)) {
              _ref2 = [null, i], i = _ref2[0], cb = _ref2[1];
            }
            if (!(cb != null)) {
              cb = (function() {});
            }
            return this.renderData(data, name, __bind(function(content) {
              return this.insert(content, i, cb);
            }, this));
          };
        }
      };
      return Template;
    })();
    $.remoteTemplate = RemoteTemplate = (function() {
      function RemoteTemplate() {
        RemoteTemplate.__super__.constructor.apply(this, arguments);
      }
      __extends(RemoteTemplate, Template);
      RemoteTemplate.prototype.extend = function(obj) {
        var _contents;
        RemoteTemplate.__super__.extend.call(this, obj);
        _contents = null;
        return obj._templates[this.name] = function(data, cb) {
          if (cb == null) {
            cb = (function() {});
          }
          if (_contents != null) {
            cb($.mustache(_contents, data));
          }
          return $.get(this.content, {}, __bind(function(data) {
            _contents = data;
            return cb($.mustache(_contents, data));
          }, this), 'text');
        };
      };
      return RemoteTemplate;
    })();
    View.inject = Inject = (function() {
      __extends(Inject, ViewExtension);
      function Inject(options) {
        var _ref, _ref2;
        this.wrapper = options.wrapper;
        this.position = options.position;
        this.append = (_ref = options.append) != null ? _ref : true;
        this.container = (_ref2 = options.container) != null ? _ref2 : $('body');
      }
      Inject.prototype.extend = function(obj) {
        var child, container;
        if (this.container == null) {
          return;
        }
        container = _.isFunction(this.container) ? this.container(obj, this) : this.container instanceof View ? this.container.$ : $safe(this.container);
        if (this.wrapper != null) {
          obj.$.wrap(this.wrapper);
        }
        if (this.position != null) {
          child = container.children(":nth-child(" + (this.position + 1) + ")");
          if (child.length === 0) {
            return container.append(obj.$);
          } else {
            return child.before(obj.$);
          }
        } else {
          return obj.$[this.append ? 'appendTo' : 'prependTo'](container);
        }
      };
      return Inject;
    })();
    View.listview = ListView = (function() {
      __extends(ListView, ViewExtension);
      function ListView(options) {
        this.options = options;
      }
      ListView.prototype.extend = function(obj) {};
      return ListView;
    })();
    View.entry = EntryView = (function() {
      __extends(EntryView, ViewExtension);
      function EntryView(options) {
        this.options = options;
      }
      return EntryView;
    })();
    UI = View.ui = {};
    UIViewExtension = (function() {
      __extends(UIViewExtension, ViewExtension);
      UIViewExtension.actions = ['enable', 'disable', 'destroy', 'option'];
      function UIViewExtension(options, child) {
        this.options = options;
        this.child = child;
      }
      UIViewExtension.prototype.extend = function(obj) {};
      return UIViewExtension;
    })();
    UI.button = UIButton = (function() {
      function UIButton() {
        UIButton.__super__.constructor.apply(this, arguments);
      }
      __extends(UIButton, UIViewExtension);
      UIButton.widget = 'button';
      return UIButton;
    })();
    return UI.buttonset = UIButtonSet = (function() {
      function UIButtonSet() {
        UIButtonSet.__super__.constructor.apply(this, arguments);
      }
      __extends(UIButtonSet, UIViewExtension);
      UIButtonSet.widget = 'buttonset';
      return UIButtonSet;
    })();
  })(jQuery);
}).call(this);
