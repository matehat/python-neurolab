(function() {
  var __slice = Array.prototype.slice, __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; }, __indexOf = Array.prototype.indexOf || function(item) {
    for (var i = 0, l = this.length; i < l; i++) {
      if (this[i] === item) return i;
    }
    return -1;
  };
  (function($) {
    var $safe, AppKit, BaseEvent, BooleanField, CustomProperty, DOMProperty, DateField, Field, FloatField, IntegerField, Property, PropertyEvent, StringField, UI, UIExtension, View, ViewEvent, ViewProperty, isJquery, jinit, _previousAK;
    _previousAK = [this.AppKit, $.AppKit];
    AppKit = this.AppKit = $.AppKit = function(fn) {
      if (_.isFunction(fn)) {
        return AppKit.viewport.hasWaken(fn);
      } else if ($.isPlainObject(fn)) {
        return AppKit.viewport.hasWaken(function() {
          return AppKit.register(fn);
        });
      }
    };
    AppKit.noConflict = function() {
      this.AppKit = _previousAK[0], $.AppKit = _previousAK[1];
      return AppKit;
    };
    jinit = $.fn.init;
    isJquery = function(o) {
      return o instanceof jinit;
    };
    $safe = function(obj, context) {
      if (isJquery(obj)) {
        if (context != null) {
          return $safe(jq.selector, context);
        } else {
          return obj;
        }
      } else if (_.isString(obj)) {
        return $(obj, context);
      } else if (_.isElement(obj) || obj === document || $.isWindow(obj)) {
        return $(obj);
      } else {
        return $();
      }
    };
    BaseEvent = (function() {
      BaseEvent.eventType = function(type) {
        return type;
      };
      function BaseEvent(eventType) {
        this.event = $.Event(eventType);
        this.event.stopPropagation();
        this.halted = false;
      }
      BaseEvent.prototype.halt = function() {
        return this.halted = true;
      };
      BaseEvent.prototype.trigger = function() {
        var args, view;
        view = arguments[0], args = 2 <= arguments.length ? __slice.call(arguments, 1) : [];
        return view.trigger(this.event, [this].concat(__slice.call(args)));
      };
      return BaseEvent;
    })();
    Property = (function() {
      function Property(parent, name, field) {
        this.parent = parent;
        this.name = name;
        this.field = field;
      }
      Property.prototype.triggerEvent = function() {
        var args, event, eventType, readonly, value;
        eventType = arguments[0], value = arguments[1], readonly = arguments[2], args = 4 <= arguments.length ? __slice.call(arguments, 3) : [];
        event = new Property.Event(this, eventType, value, readonly);
        event.trigger.apply(event, args);
        return event;
      };
      return Property;
    })();
    Property.Event = PropertyEvent = (function() {
      __extends(PropertyEvent, BaseEvent);
      function PropertyEvent(property, event, value, readonly) {
        this.property = property;
        this.value = value;
        if (readonly == null) {
          readonly = false;
        }
        PropertyEvent.__super__.constructor.call(this, event);
        this.valueChanged = false;
        this.view = this.property.parent;
        this.propertyName = this.property.name;
        this.getValue = __bind(function() {
          return this.value;
        }, this);
        if (!readonly) {
          this.setValue = __bind(function(newValue) {
            this.valueChanged || (this.valueChanged = newValue !== this.value);
            return this.value = newValue;
          }, this);
        }
      }
      PropertyEvent.prototype.trigger = function() {
        var args;
        args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
        return PropertyEvent.__super__.trigger.apply(this, [this.view].concat(__slice.call(args)));
      };
      return PropertyEvent;
    })();
    AppKit.DOMProperty = DOMProperty = (function() {
      __extends(DOMProperty, Property);
      function DOMProperty(parent, name, selector, attr, field) {
        this.selector = selector;
        this.attr = attr;
        DOMProperty.__super__.constructor.call(this, parent, name, field);
        this.$().live('change', __bind(function(event) {
          var local;
          return local = this.triggerEvent('HasChanged', this.getter());
        }, this));
      }
      DOMProperty.prototype.$ = function() {
        if (this.attr && !this.selector) {
          return this.parent.$;
        } else {
          return this.parent.$.find(this.selector);
        }
      };
      DOMProperty.prototype.getter = function() {
        var jq;
        if (this.attr) {
          return this.$().attr(this.attr);
        } else {
          if ((jq = this.$()).is(":checkbox, :radio")) {
            return jq.filter(":checked").val();
          } else if (jq.is(":input")) {
            return jq.val() || '';
          } else {
            return jq.text();
          }
        }
      };
      DOMProperty.prototype.setter = function(value) {
        var jq;
        if (this.attr) {
          return this.$().attr(this.attr, value);
        } else {
          if ((jq = this.$()).is(":input")) {
            return jq.val(value);
          } else {
            return jq.text(value);
          }
        }
      };
      return DOMProperty;
    })();
    AppKit.ViewProperty = ViewProperty = (function() {
      __extends(ViewProperty, Property);
      function ViewProperty(parent, name, view, propertyName, field) {
        this.view = view;
        this.propertyName = propertyName;
        ViewProperty.__super__.constructor.call(this, parent, name, field);
        this.view.bind(PropertyEvent.eventType('propertyWillChange'), __bind(function(remote) {
          var local;
          if (remote.propertyName !== this.propertyName) {
            return;
          }
          local = this.triggerEvent('propertyWillChange', remote.getValue());
          if (local.halted) {
            remote.halt();
          }
          return remote.setValue(local.value);
        }, this));
        this.view.bind(PropertyEvent.eventType('propertyHasChanged'), __bind(function(remote) {
          var local;
          if (remote.propertyName !== this.propertyName) {
            return;
          }
          return local = this.triggerEvent('propertyHasChanged', remote.getValue());
        }, this));
      }
      ViewProperty.prototype.getter = function() {
        return this.view.get(this.property);
      };
      ViewProperty.prototype.setter = function(value) {
        return this.view.set(this.property, value);
      };
      return ViewProperty;
    })();
    AppKit.CustomProperty = CustomProperty = (function() {
      __extends(CustomProperty, Property);
      function CustomProperty(parent, name, getter, setter, binder, field) {
        var _ref;
        CustomProperty.__super__.constructor.call(this, parent, name, field);
        this.getter = getter;
        this.setter = setter;
        if (_.isFunction(binder)) {
          _.bind(binder, this)();
        } else {
          _ref = [binder, null], this.field = _ref[0], binder = _ref[1];
        }
      }
      return CustomProperty;
    })();
    Field = (function() {
      function Field(options, property) {
        var criteria, _ref, _ref2;
        this.property = property;
        this.required = (_ref = options.required) != null ? _ref : false;
        this.choices = options.choices;
        this["default"] = (_ref2 = options["default"]) != null ? _ref2 : this.constructor["default"];
        if ((criteria = this.constructor.criteria) != null) {
          _.each(criteria, function(crit) {
            return this[crit] = options[crit];
          });
        }
      }
      Field.prototype.errors = function(criteria) {
        var _base, _ref;
        if (criteria != null) {
          return ((_ref = (_base = this.property).errors) != null ? _ref : _base.errors = []).push(criteria);
        } else {
          return this.property.errors;
        }
      };
      Field.prototype.valid = function() {
        return !((this.property.errors != null) && this.property.length > 0);
      };
      Field.prototype.clearErrors = function() {
        return this.property.errors = [];
      };
      Field.prototype.validate = function(value) {
        var _ref;
        this.clearErrors();
        if (this.required != null) {
          if (!(value != null) || _.trim(value)) {
            this.errors("required");
            return this["default"];
          }
        } else if (this.choices != null) {
          if (_ref = !value, __indexOf.call(this.choices, _ref) >= 0) {
            this.errors("choices");
          }
        }
        return value;
      };
      return Field;
    })();
    AppKit.fields = {
      text: StringField = (function() {
        function StringField() {
          StringField.__super__.constructor.apply(this, arguments);
        }
        __extends(StringField, Field);
        StringField.criteria = ['min_length', 'max_length'];
        StringField["default"] = '';
        StringField.prototype.validate = function(value) {
          value = StringField.__super__.validate.call(this, value);
          if (!_.isString(value)) {
            value = _.sprintf("%s", value);
          }
          if ((this.min_length != null) && value.length < this.min_length) {
            this.errors('min_length');
          }
          if ((this.max_length != null) && value.length > this.max_length) {
            this.errors('max_length');
          }
          return value;
        };
        StringField.prototype.stringValue = function(value) {
          return _.sprintf("%s", value);
        };
        StringField.prototype.serialized = function(value) {
          return this.stringValue();
        };
        return StringField;
      })(),
      integer: IntegerField = (function() {
        __extends(IntegerField, Field);
        IntegerField.criteria = ['min_value', 'max_value'];
        IntegerField["default"] = 0;
        IntegerField.events = {
          keydown: function(event) {
            var _ref;
            if (_ref = event.which, __indexOf.call(_.range(48, 58), _ref) < 0) {
              return false;
            }
          }
        };
        function IntegerField(options, property) {
          var _ref;
          this.rounding = (_ref = options.rounding) != null ? _ref : 'round';
          IntegerField.__super__.constructor.call(this, options, property);
        }
        IntegerField.prototype.validate = function(value) {
          value = this.serialized(IntegerField.__super__.validate.call(this, value));
          if (_.isNaN(value)) {
            this.errors('invalid');
            value = this["default"];
          }
          if ((this.min_value != null) && value < this.min_value) {
            this.errors('min_value');
            value = this.min_value;
          }
          if ((this.max_value != null) && value > this.max_value) {
            this.errors('max_value');
            value = this.max_value;
          }
          return value;
        };
        IntegerField.prototype.stringValue = function(value) {
          return _.sprintf("%d", this.serialized(value));
        };
        IntegerField.prototype.serialized = function(value) {
          return Math[this.rounding](value);
        };
        return IntegerField;
      })(),
      float: FloatField = (function() {
        function FloatField() {
          FloatField.__super__.constructor.apply(this, arguments);
        }
        __extends(FloatField, Field);
        FloatField.criteria = ['min_value', 'max_value'];
        FloatField["default"] = 0;
        FloatField.events = {
          keydown: function(event) {
            var key, _ref;
            if ((_ref = (key = event.which)) !== _.range(48, 58) && _ref !== 190) {
              return false;
            }
            if (_.isContains($(event.target).val(), '.') && key === 190) {
              return false;
            }
          }
        };
        FloatField.prototype.validate = IntegerField.prototype.validate;
        FloatField.prototype.stringValue = function(value) {
          return _.sprintf("%e", this.serialized(value));
        };
        FloatField.prototype.serialized = function(value) {
          if (!_.isNumber(value)) {
            return new Number(value);
          } else {
            return value;
          }
        };
        return FloatField;
      })(),
      boolean: BooleanField = (function() {
        function BooleanField() {
          BooleanField.__super__.constructor.apply(this, arguments);
        }
        __extends(BooleanField, Field);
        BooleanField["default"] = false;
        BooleanField.prototype.serialized = function(value) {
          if (_.isString(value)) {
            value = _.trim(value);
          }
          if (value === '' || value === null || value === false) {
            return false;
          } else {
            return true;
          }
        };
        BooleanField.prototype.stringValue = function(value) {
          return _.sprintf("%s", this.serialized(value));
        };
        return BooleanField;
      })(),
      date: DateField = (function() {
        __extends(DateField, Field);
        DateField.dateFormat = "yy-mm-dd";
        function DateField(options, property) {
          var _ref, _ref2;
          this.property = property;
          DateField.__super__.constructor.call(this, options, this.property);
          (_ref = this["default"]) != null ? _ref : this["default"] = new Date;
          this.dateFormat = (_ref2 = options.format) != null ? _ref2 : this.constructor.dateFormat;
          this.parseDate = _.bind($.datepicker.parseDate, $, this.dateFormat);
          this.formatDate = _.bind($.datepicker.formatDate, $, this.dateFormat);
        }
        DateField.prototype.validate = function(value) {
          if (_.isString(value)) {
            try {
              value = this.parseDate(value);
            } catch (errormsg) {
              this.errors('invalid');
              value = this["default"];
            }
          } else if (!_.isDate(value)) {
            this.errors('invalid');
            value = this["default"];
          }
          return value;
        };
        DateField.prototype.stringValue = function(value) {
          return this.formatDate(this.serialized(value));
        };
        DateField.prototype.serialized = function(value) {
          if (_.isString(value)) {
            try {
              value = this.parseDate(value);
            } catch (errormsg) {
              value = this["default"];
            }
          } else if (!_.isDate(value)) {
            value = this["default"];
          }
          return value;
        };
        return DateField;
      })()
    };
    AppKit.getViewForPath = function(path, ref) {
      var bits, cur, found;
      cur = ref != null ? ref : ref = AppKit.viewport;
      bits = path.split('.');
      found = _.all(bits, function(bit) {
        var target, window;
        if (cur.getView != null) {
          if ((target = cur.getView(bit)) != null) {
            cur = target;
            return true;
          } else {
            return false;
          }
        } else if (cur === (window = AppKit.window)) {
          if (bit in window) {
            cur = window[bit];
            return true;
          } else {
            return false;
          }
        }
      });
      if (found && cur !== ref) {
        return cur;
      } else {
        return null;
      }
    };
    AppKit.View = View = (function() {
      function View(options, target) {
        var parent, templ, view, _ref;
        this.options = options;
        this.target = target != null ? target : {};
        if (this instanceof View) {
          this.awake = false;
        } else {
          view = new View(options);
          if ((parent = options.parent) != null) {
            view.parent = parent;
          }
          if ((templ = options.template) != null) {
            if ($.isPlainObject(templ)) {
              options.template = AppKit.template(templ);
            }
          }
          if (((_ref = options.awake) != null) ? _ref : false && options.target) {
            view.wakeFromSelector(options.parent != null ? options.parent.$ : null);
          } else {
            view;
          }
          return view;
        }
      }
      View.prototype.clone = function(options) {
        if (options == null) {
          options = {};
        }
        return View(_.extend(_.clone(this.options), options, {
          'awake': false
        }));
      };
      View.prototype.extend = function(options, name) {
        var ext, repo, _apply, _ref;
        if (name == null) {
          _.each(options, this.extend);
        }
        _apply = __bind(function(_ext) {
          if (_.isFunction(_ext)) {
            return _ext(this, options);
          } else if ((_ext = _ext.extend) != null) {
            return _ext(this, options);
          }
        }, this);
        if ((ext = AppKit.exts[name]) != null) {
          return _apply(ext);
        } else if (_.count(name, '.') === 1) {
          _ref = name.split('.'), repo = _ref[0], name = _ref[1];
          if ((repo = AppKit.exts.repositories[repo]) != null) {
            if ((ext = repo[name]) != null) {
              return _apply(ext);
            }
          }
        }
      };
      View.prototype.wake = function(jq) {
        var _ref, _ref2, _ref3, _ref4;
        if (jq == null) {
          return this.wakeFromSelector();
        }
        if (_.isFunction(jq)) {
          return this.HasWaken(jq);
        }
        if (this.awake) {
          return;
        }
        (this.$ = jq).data('view', this);
        this.awake = true;
        this.bindQueue();
        if (this.willWake().halted) {
          return this.destroy();
        }
        _.each((_ref = this.options.events) != null ? _ref : [], _.bind(this.addEvent, this));
        _.each((_ref2 = this.options.properties) != null ? _ref2 : [], _.bind(this.addProperty, this));
        _.each((_ref3 = this.options.methods) != null ? _ref3 : [], _.bind(this.addMethod, this));
        _.each((_ref4 = this.options.extensions) != null ? _ref4 : {}, _.bind(this.extend, this));
        this.hasWaken();
        return this;
      };
      View.prototype.wakeFromNode = function(elem) {
        return this.wake($safe(elem));
      };
      View.prototype.createFromNode = function(elem, options) {
        return this.clone(options).wakeFromNode(elem);
      };
      View.prototype.wakeFromSelector = function(context) {
        if (this.options.target == null) {
          return;
        }
        return this.wake($safe(this.options.target, context));
      };
      View.prototype.createFromSelector = function(context) {
        if (this.options.target == null) {
          return;
        }
        return this.clone().wakeFromSelector(context);
      };
      View.prototype.wakeFromTemplate = function(data, cb) {
        if (cb == null) {
          cb = (function() {});
        }
        if (this.options.template == null) {
          return;
        }
        return this.options.template(data, __bind(function(content) {
          return cb(this.wake($(content)));
        }, this));
      };
      View.prototype.createFromTemplate = function(data, cb) {
        if (cb == null) {
          cb = (function() {});
        }
        if (this.options.template == null) {
          return;
        }
        return this.clone().wakeFromTemplate(data, cb);
      };
      View.prototype.wakeFromContent = function(data, cb) {
        if (cb == null) {
          cb = (function() {});
        }
        if (this.options.content == null) {
          return;
        }
        if (_.isFunction(this.options.content)) {
          cb(this.wake($(_.bind(this.options.content, this)(data))));
        }
        if (_.isString(this.options.content)) {
          cb(this.wake($(this.options.content)));
        }
        if (this.options.content.remote != null) {
          data = _.extend(this.options.content.data);
          return $.get(this.options.content.remote, data, __bind(function(content) {
            return cb(this.wake($(content)));
          }, this));
        }
      };
      View.prototype.createFromContent = function(data, cb) {
        if (cb == null) {
          cb = (function() {});
        }
        if (this.options.content == null) {
          return;
        }
        return this.clone().wakeFromContent(data, cb);
      };
      View.prototype.destroy = function() {
        if (this.willDestroy().halted) {
          return;
        }
        delete this.__subviews;
        delete this.__properties;
        this.hasDestroyed();
        this.$.remove();
        delete this.$;
        return this.awake = false;
      };
      View.prototype.inject = function() {
        var inj, _base, _ref, _ref2;
        if ((_ref = (inj = (_ref2 = (_base = this.options).inject) != null ? _ref2 : _base.inject = 'append')) === 'append' || _ref === 'prepend') {
          return this.parent.$[inj](this.$);
        } else if (_.isNumber(inj)) {
          return this.parent.$.children("nth-child(" + (inj + 1) + ")").before(this.$);
        } else if (_.isFunction(inj)) {
          return _.bind(inj, this)(this.parent);
        }
      };
      View.prototype.willWake = function(fn) {
        if (_.isFunction(fn)) {
          return this.bind('viewWillWake', fn);
        } else {
          return this.triggerEvent('viewWillWake');
        }
      };
      View.prototype.hasWaken = function(fn) {
        if (_.isFunction(fn)) {
          if (this.awake) {
            return fn();
          }
          return this.bind('viewHasWaken', fn);
        } else {
          return this.triggerEvent('viewHasWaken');
        }
      };
      View.prototype.willDestroy = function(fn) {
        if (_.isFunction(fn)) {
          if (this.awake) {
            return fn();
          }
          return this.bind('viewWillDestroy', fn);
        } else {
          return this.triggerEvent('viewWillDestroy');
        }
      };
      View.prototype.hasDestroyed = function(fn) {
        if (_.isFunction(fn)) {
          if (this.awake) {
            return fn();
          }
          return this.bind('viewHasDestroyed', fn);
        } else {
          return this.triggerEvent('viewHasDestroyed');
        }
      };
      View.prototype.addMethod = function(method, name) {
        var eventType, _ref;
        if (method.method != null) {
          eventType = (_ref = method.eventType) != null ? _ref : name;
          method = _.bind(method.method, this);
          return this[name] = __bind(function() {
            var args;
            args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
            this.trigger(eventType, __slice.call(args));
            return method.apply(null, args);
          }, this);
        } else {
          return this[name] = _.bind(method, this);
        }
      };
      View.prototype.addEvent = function(handler, eventType) {
        var handlr, target, _i, _len, _results;
        if (_.isArray(handler)) {
          _results = [];
          for (_i = 0, _len = handler.length; _i < _len; _i++) {
            handlr = handler[_i];
            _results.push(this.addEvent(handlr, eventType));
          }
          return _results;
        } else if (_.isString(handler)) {
          if (_.isStartsWith(handler, '@')) {
            target = this;
            handler = handler.slice(1);
          } else if (this.parent != null) {
            target = this.parent;
          }
          return this.bind(eventType, __bind(function() {
            var args, event;
            event = arguments[0], args = 2 <= arguments.length ? __slice.call(arguments, 1) : [];
            return target.trigger(handler, [event].concat(__slice.call(args)));
          }, this));
        } else {
          return this.bind(eventType, _.bind(handler, this));
        }
      };
      View.prototype.addView = function(view, name) {
        var _ref;
        view.parent = this;
        return ((_ref = this.__subviews) != null ? _ref : this.__subviews = {})[name] = view;
      };
      View.prototype.getView = function(name) {
        var _ref;
        return ((_ref = this.__subviews) != null ? _ref : this.__subviews = {})[name];
      };
      View.prototype.getViewForPath = function(path) {
        return AppKit.getViewForPath(path, this);
      };
      View.prototype.find = function(sel) {
        if (this.$ != null) {
          return this.$.find(sel);
        } else {
          return $();
        }
      };
      View.prototype.has = function(name) {
        return (this.getProperty(name)) != null;
      };
      View.prototype.get = function(name, fallback) {
        var prop;
        if (fallback == null) {
          fallback = null;
        }
        if ((prop = this.getProperty(name)) != null) {
          return prop.getter();
        } else {
          return fallback;
        }
      };
      View.prototype.getMany = function() {
        var names, values;
        names = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
        values = {};
        _.each(names, __bind(function(name) {
          return values[name] = this.get(name);
        }, this));
        return values;
      };
      View.prototype.set = function(name, value) {
        var event, prop;
        if ((prop = this.getProperty(name)) != null) {
          if ((event = prop.triggerEvent('propertyWillChange', value)).halted) {
            return;
          }
          prop.setter(event.value);
          return prop.triggerEvent('propertyHasChanged', event.value, true);
        }
      };
      View.prototype.getProperty = function(name) {
        var _ref;
        return ((_ref = this.__properties) != null ? _ref : this.__properties = {})[name];
      };
      View.prototype.addProperty = function(property, name) {
        var attr, selector, splitted, view, _ref, _ref2;
        if ((property.selector != null) || _.isString(property)) {
          if (property.selector == null) {
            property = {
              selector: property
            };
          }
          _ref = (splitted = property.selector.split('/')).length === 2 ? splitted : [property.selector, ''], selector = _ref[0], attr = _ref[1];
          property = new DOMProperty(this, name, selector, attr, property.field);
        } else if (((view = property.subview) != null) || ((view = property.view) != null)) {
          property = new ViewProperty(this, name, (property.subview != null ? this : AppKit).getViewForPath(view), view.property, view.field);
        } else if ((property.getter != null) || (property.setter != null)) {
          property = new CustomProperty(this, name, property.getter, property.setter, property.binder, property.field);
        } else {
          return;
        }
        if (this.triggerEvent('viewWillAddProperty', property).halted) {
          return;
        }
        ((_ref2 = this.__properties) != null ? _ref2 : this.__properties = {})[name] = property;
        return this.triggerEvent('viewHasAddedProperty', property);
      };
      View.prototype.triggerEvent = function() {
        var args, event, eventType;
        eventType = arguments[0], args = 2 <= arguments.length ? __slice.call(arguments, 1) : [];
        event = new View.Event(this, eventType);
        event.trigger.apply(event, args);
        return event;
      };
      View.prototype.trigger = function(eventType, data) {
        return this.$.triggerHandler(eventType, data);
      };
      View.prototype.bind = function(eventType, data, cb) {
        var _ref;
        cb = _.bind(cb, this);
        if (this.awake) {
          return this.$.bind(eventType, data, cb);
        } else {
          return ((_ref = this.__bindQueue) != null ? _ref : this.__bindQueue = []).push([eventType, data, cb]);
        }
      };
      View.prototype.live = function(eventType, data, cb) {
        cb = _.bind(cb, this);
        if (this.awake) {
          return this.$.live(eventType, data, cb);
        } else {
          return (typeof $__liveQueue != "undefined" && $__liveQueue !== null ? $__liveQueue : $__liveQueue = []).push([eventType, data, cb]);
        }
      };
      View.prototype.bindQueue = function() {
        var _ref, _ref2;
        _.each((_ref = this.__bindQueue) != null ? _ref : [], __bind(function(args) {
          return this.bind.apply(this, args);
        }, this));
        delete this.__bindQueue;
        _.each((_ref2 = this.__liveQueue) != null ? _ref2 : [], __bind(function(args) {
          return this.live.apply(this, args);
        }, this));
        return delete this.__liveQueue;
      };
      return View;
    })();
    View.Event = ViewEvent = (function() {
      __extends(ViewEvent, BaseEvent);
      function ViewEvent(view, eventType) {
        this.view = view;
        ViewEvent.__super__.constructor.call(this, eventType);
        this.event.view = this.view;
      }
      ViewEvent.eventType = function(type) {
        return "view" + type;
      };
      ViewEvent.prototype.trigger = function() {
        var args;
        args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
        return ViewEvent.__super__.trigger.apply(this, [this.view].concat(__slice.call(args)));
      };
      return ViewEvent;
    })();
    AppKit.template = function(options) {
      var engine, _ref;
      if (_.isFunction(options)) {
        return options;
      }
      engine = AppKit.template.engines[(_ref = options.engine) != null ? _ref : AppKit.template.defaultEngine];
      return function(data, cb) {
        var content, remote, _data, _ref;
        if ((content = options.content) != null) {
          return engine(content, data, cb);
        } else if ((remote = options.remote) != null) {
          if (_.isFunction(remote)) {
            remote = _.bind(remote, this)(data);
          }
          _data = (_ref = options.data) != null ? _ref : {};
          if (_.isFunction(_data)) {
            _data = _.bind(_data, this)(data);
          }
          return $.get(remote, _data, (function(content) {
            if (options.cache === true) {
              options.content = content;
            }
            return engine(content, data, cb);
          }), 'text');
        }
      };
    };
    AppKit.template.engines = {
      mustache: function(content, data, cb) {
        return cb(_.mustache(content, data));
      }
    };
    AppKit.template.defaultEngine = 'mustache';
    AppKit.exts = {
      subviews: function(obj, views) {
        return _.each(views, __bind(function(viewopts, name) {
          var subview, _ref;
          (_ref = viewopts.awake) != null ? _ref : viewopts.awake = true;
          viewopts.parent = obj;
          subview = View(viewopts);
          subview.willWake(function() {
            return subview.inject();
          });
          return obj.addView(subview, name);
        }, this));
      },
      listview: function(obj, options) {
        var $$, container, entryopts, entryview, _ref, _selector;
        container = options.selector != null ? obj.find(options.selector).eq(0) : (_ref = obj.$) != null ? _ref : $();
        if (!(container.length > 0)) {
          return;
        }
        if ((_selector = (entryopts = options.entry).selector) == null) {
          return;
        }
        entryopts.parent = obj;
        entryview = View(entryopts);
        $$ = obj.entries = function() {
          return $$.get();
        };
        _.each({
          Q: function(sel) {
            if (sel != null) {
              return container.find("" + _selector + sel);
            } else {
              return container.find(_selector);
            }
          },
          get: function(index) {
            var jq, view;
            if (index != null) {
              jq = $$.Q(":nth-child(" + (index + 1) + ")");
              if ((view = jq.data('view')) != null) {
                return view;
              }
              return entryview.createFromNode(jq);
            } else {
              return _.map(_.range($$.size()), $$.get);
            }
          },
          size: function() {
            return $$.Q().length;
          },
          filterIterator: function(spec, entry, index) {
            return _.all(spec, function(value, key) {
              return $$.get(key) === value;
            });
          },
          find: function(spec) {
            return $$.select(_.bind($$.filterIterator, this, spec));
          },
          findOne: function(spec) {
            return $$.detect(_.bind($$.filterIterator, this, spec));
          },
          each: function(cb) {
            return _.each($$(), cb, this);
          },
          map: function(cb) {
            return _.map($$(), cb, this);
          },
          detect: function(cb) {
            return _.detect($$(), cb, this);
          },
          select: function(cb) {
            return _.select($$(), cb, this);
          },
          detect: function(cb) {
            return _.detect($$(), cb, this);
          },
          reject: function(cb) {
            return _.reject($$(), cb, this);
          },
          any: function(cb) {
            return _.any($$(), cb, this);
          },
          every: function(cb) {
            return _.every($$(), cb, this);
          },
          pluck: function() {
            var names;
            names = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
            return $$.map(function(entry) {
              var data;
              data = {};
              _.each(names, function(name) {
                var method;
                if (entry.has(name)) {
                  return data[name] = entry.get(name);
                } else if (((method = entry[name]) != null) && _.isFunction(method)) {
                  return data[name] = method();
                }
              });
              return data;
            });
          },
          insert: function(content, i, cb) {
            var _jq, _ref, _size, _view;
            if (cb == null) {
              cb = (function() {});
            }
            if ($.isPlainObject(content)) {
              if (entryview.createFromTemplate != null) {
                entryview.createFromTemplate(content, __bind(function(view) {
                  return this.entries.insert(view.$, i, cb);
                }, this));
                return;
              } else {
                return;
              }
            }
            if (_.isFunction(i)) {
              _ref = [null, i], i = _ref[0], cb = _ref[1];
            }
            _jq = $safe(content);
            _view = _jq.data('view') == null ? entryview.createFromNode(_jq) : _jq.data('view');
            if (!(i != null) || (_size = $$.size()) <= i) {
              container.append(_jq);
              i = _size;
            } else {
              $$.Q(":nth-child(" + (i + 1) + ")").before(_jq);
            }
            return cb(_view);
          },
          append: function(content, cb) {
            return $$.insert(content, cb);
          },
          prepend: function(content, cb) {
            return $$.insert(content, 0, cb);
          },
          remove: function(i, cb) {
            var event, jq, view;
            if (_.isNumber(i)) {
              view = $$.get(i);
            } else if (i instanceof View) {
              view = i;
            } else if ((jq = $safe(i)).length === 1) {
              if ((view = jq.data('view')) == null) {
                return;
              }
            } else {
              return;
            }
            event = $.Event('beforeRemoveEntry');
            this.trigger('beforeRemoveEntry', [view]);
            view.$.remove();
            return _.bind(cb, this)(view);
          },
          detach: function(i, cb) {
            var view;
            if (_.isNumber(i)) {
              view = $$.get(i);
            } else if (i instanceof View) {
              view = i;
            } else {
              return;
            }
            view.$.detach();
            return _.bind(cb, this)(view);
          }
        }, function(func, name) {
          return $$[name] = _.bind(func, obj);
        });
        return $$();
      },
      register: function(exts) {
        return _.extend(AppKit.exts.repositories, exts);
      },
      repositories: {}
    };
    UI = {
      extension: UIExtension = function(opt) {
        return function(obj, options) {
          var actions, widget, _ref;
          widget = obj[opt.widget] = _.bind(obj.$[opt.widget], obj.$);
          widget(options != null ? options : {});
          actions = ['destroy', 'disable', 'enable', 'option', 'refresh'].concat(__slice.call((_ref = opt.actions) != null ? _ref : []));
          return _.each(actions, __bind(function(action) {
            return widget[action] = _.bind(widget, obj.$, action);
          }, this));
        };
      },
      exts: {
        button: UIExtension({
          widget: 'button'
        }),
        buttonset: UIExtension({
          widget: 'buttonset'
        }),
        slider: UIExtension({
          actions: ['value', 'values'],
          widget: 'slider'
        }),
        tabs: UIExtension({
          actions: ['add', 'remove', 'select', 'load', 'url', 'length', 'abort', 'rotate'],
          widget: 'tabs'
        }),
        progressbar: UIExtension({
          actions: ['value'],
          widget: 'progressbar'
        }),
        accordion: UIExtension({
          actions: ['activate', 'restart'],
          widget: 'accordion'
        }),
        autocomplete: UIExtension({
          action: ['search', 'close'],
          widget: 'autocomplete'
        }),
        datepicker: UIExtension({
          action: ['dialog', 'isDisabled', 'hide', 'show', 'refresh', 'getDate', 'setDate'],
          widget: 'datepicker'
        }),
        dialog: UIExtension({
          action: ['close', 'isOpen', 'moveToTop', 'open'],
          widget: 'dialog'
        }),
        draggable: UIExtension({
          widget: 'draggable'
        }),
        droppable: UIExtension({
          widget: 'droppable'
        }),
        resizable: UIExtension({
          widget: 'resizable'
        }),
        selectable: UIExtension({
          actions: ['refresh'],
          widget: 'selectable'
        }),
        sortable: UIExtension({
          actions: ['serialize', 'toArray', 'refresh', 'refreshPositions', 'cancel'],
          widget: 'sortable'
        })
      }
    };
    AppKit.exts.register({
      ui: UI.exts
    });
    AppKit.options = function(options, fallback) {
      var _ref, _ref2, _ref3;
      if ($.isPlainObject(options)) {
        return _.extend(((_ref = AppKit.__options) != null ? _ref : AppKit.__options = {}), options);
      } else if (_.isString(options)) {
        return (_ref2 = ((_ref3 = AppKit.__options) != null ? _ref3 : AppKit.__options = {})[options]) != null ? _ref2 : fallback;
      }
    };
    AppKit.loadView = function(url) {
      return $.getScript("" + (AppKit.options('viewURL', '')) + url + ".js");
    };
    AppKit.register = function(views) {
      return _.each(views, function(view, name) {
        var _ref;
        (_ref = view.parent) != null ? _ref : view.parent = AppKit.viewport;
        if (_.isString(view.parent)) {
          view.parent = AppKit.getViewForPath(view.parent);
        }
        if (!(view.parent instanceof View)) {
          return;
        }
        return view.parent.addView(view, name);
      });
    };
    AppKit.viewport = View({
      target: 'body',
      awake: false
    });
    return $(function() {
      return AppKit.viewport.wake();
    });
  })(jQuery);
}).call(this);
