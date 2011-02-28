(($) ->

  _previousAK = [@AppKit, $.AppKit]
  AppKit = @AppKit = $.AppKit = (fn) ->
    if _.isFunction fn
      AppKit.viewport.hasWaken fn
    else if $.isPlainObject fn
      AppKit.viewport.hasWaken -> 
        AppKit.register fn
  
  AppKit.noConflict = ->
    [@AppKit, $.AppKit] = _previousAK
    return AppKit
  
  
  jinit = $.fn.init
  isJquery = (o) -> o instanceof jinit
  $safe = (obj, context) ->
    if isJquery obj
      if context? then $safe(jq.selector, context) else obj
    else if _.isString(obj) then $(obj, context)
    else if _.isElement(obj) or obj is document or $.isWindow obj then $(obj)
    else $()
  
  
  class BaseEvent
    @eventType: (type) -> type
    constructor: (eventType) ->
      @event = $.Event eventType
      @event.stopPropagation()
      @halted = no
    
    halt: -> @halted = yes
    trigger: (view, args...) ->
      view.trigger @event, [@, args...]
    
    
  class Property
    constructor: (@parent, @name, @field) ->
    
    triggerEvent: (eventType, value, readonly, args...) ->
      event = new Property.Event(@, eventType, value, readonly)
      event.trigger args...
      return event
    
  
  Property.Event = class PropertyEvent extends BaseEvent
    constructor: (@property, event, @value, readonly=no) ->
      super event
      @valueChanged = no
      @view = @property.parent
      @propertyName = @property.name
      @getValue = => @value
      unless readonly
        @setValue = (newValue) => 
          @valueChanged or= newValue isnt @value
          @value = newValue
    
    trigger: (args...) ->
      super @view, args...
    
  
  AppKit.DOMProperty =    class DOMProperty extends Property
    constructor: (parent, name, @selector, @attr, field) ->
      super parent, name, field
      @$().live 'change', (event) =>
        local = @triggerEvent 'HasChanged', @getter()
    
    $: ->
      if @attr and not @selector then @parent.$
      else @parent.$.find(@selector)
    
    getter: ->
      if @attr
        return @$().attr @attr
      else
        if (jq = @$()).is ":checkbox, :radio"
          jq.filter(":checked").val()
        else if jq.is ":input"
          jq.val() or ''
        else
          jq.text()
    
    setter: (value) ->
      if @attr
        @$().attr(@attr, value)
      else
        if (jq = @$()).is ":input"
          return jq.val(value)
        else
          return jq.text(value)
    
  
  AppKit.ViewProperty =   class ViewProperty extends Property
    constructor: (parent, name, @view, @propertyName, field) ->
      super parent, name, field
      
      @view.bind PropertyEvent.eventType('propertyWillChange'), (remote) =>
        return unless remote.propertyName is @propertyName
        local = @triggerEvent 'propertyWillChange', remote.getValue()
        remote.halt() if local.halted
        remote.setValue local.value
      
      @view.bind PropertyEvent.eventType('propertyHasChanged'), (remote) =>
        return unless remote.propertyName is @propertyName
        local = @triggerEvent 'propertyHasChanged', remote.getValue()
      
    
    getter: -> @view.get @property
    setter: (value) -> @view.set @property, value
  
  AppKit.CustomProperty = class CustomProperty extends Property
    constructor: (parent, name, getter, setter, binder, field) ->
      super parent, name, field
      @getter = getter
      @setter = setter
      if _.isFunction binder
        _.bind(binder, @)()
      else
        [@field, binder] = [binder, null]
    
  
  
  # // TODO : Integrate field validation & normalization
  #           in properties behavior
  
  class Field
    constructor: (options, @property) ->
      @required = options.required ? no
      @choices = options.choices
      @default = options.default ? @constructor.default
      if (criteria = @constructor.criteria)?
        _.each criteria, (crit) -> @[crit] = options[crit]
    
    errors: (criteria) ->
      if criteria? then (@property.errors ?= []).push criteria
      else return @property.errors
    
    valid: -> not (@property.errors? and @property.length > 0)
    clearErrors: -> @property.errors = []
    validate: (value) ->
      @clearErrors()
      if @required?
        if not value? or _.trim(value)
          @errors "required"
          return @default
      else if @choices?
        if not value in @choices
          @errors "choices"
      return value
    
  
  AppKit.fields = {  
    text:     class StringField   extends Field
      @criteria = ['min_length', 'max_length']
      @default = ''
      
      validate: (value) ->
        value = super value
        if not _.isString value
          value = _.sprintf "%s", value
        if @min_length? and value.length < @min_length
          @errors 'min_length'
        if @max_length? and value.length > @max_length
          @errors 'max_length'
        value
      
      stringValue: (value) -> _.sprintf "%s", value
      serialized: (value) -> @stringValue()
    
    integer:  class IntegerField  extends Field
      @criteria = ['min_value', 'max_value']
      @default = 0
      @events = {
        keydown: (event) ->
          return false unless event.which in _.range(48, 58)
      }
      
      constructor: (options, property) ->
        @rounding = options.rounding ? 'round'
        super options, property
      
      validate: (value) ->
        value = @serialized super(value)
        if _.isNaN value
          @errors 'invalid'
          value = @default
        if @min_value? and value < @min_value
          @errors 'min_value'
          value = @min_value
        if @max_value? and value > @max_value
          @errors 'max_value'
          value = @max_value
        value
      
      stringValue: (value) -> _.sprintf "%d", @serialized(value)
      serialized: (value) -> Math[@rounding](value)
    
    float:    class FloatField    extends Field
      @criteria = ['min_value', 'max_value']
      @default = 0
      @events = {
        keydown: (event) ->
          return false unless (key = event.which) in [_.range(48, 58)..., 190]
          return false if _.isContains($(event.target).val(), '.') and key is 190
      }
      
      validate: IntegerField::validate
      stringValue: (value) -> _.sprintf "%e", @serialized(value)
      serialized: (value) -> 
        if not _.isNumber(value) then new Number(value) else value
      
    
    boolean:  class BooleanField  extends Field
      @default = false
      serialized: (value) ->
        value = _.trim value if _.isString value
        if value in ['', null, false] then false
        else true
      
      stringValue: (value) -> _.sprintf "%s", @serialized(value)
    
    date:     class DateField     extends Field
      @dateFormat = "yy-mm-dd"
      constructor: (options, @property) ->
        super options, @property
        @default ?= new Date
        @dateFormat = options.format ? @constructor.dateFormat
        @parseDate = _.bind $.datepicker.parseDate, $, @dateFormat
        @formatDate = _.bind $.datepicker.formatDate, $, @dateFormat
      
      validate: (value) ->
        if _.isString value
          try value = @parseDate value
          catch errormsg
            @errors 'invalid'
            value = @default
        else unless _.isDate value
          @errors 'invalid'
          value = @default
        value
      
      stringValue: (value) ->
        return @formatDate @serialized(value)
      
      serialized: (value) ->
        if _.isString value
          try value = @parseDate value
          catch errormsg
            value = @default
        else unless _.isDate value
          value = @default
        return value
      
    
  }
  
  AppKit.getViewForPath = (path, ref) ->
    cur = ref ?= AppKit.viewport
    bits = path.split '.'
    found = _.all(bits, (bit) ->
      if cur.getView?
        if (target = cur.getView bit)?
          cur = target
          return true
        else return false
      else if cur is (window = AppKit.window)
        if bit of window
          cur = window[bit]
          return true
        else return false
    )
    return if found and cur isnt ref then cur
    else null
  
  
  AppKit.View = class View
    constructor: (@options, @target={}) ->
      if @ instanceof View
        @awake = no
      else
        view = new View options
        if (parent = options.parent)?
          view.parent = parent
        if (templ = options.template)?
          if $.isPlainObject templ
            options.template = AppKit.template templ
        
        if options.awake ? no and options.target
          view.wakeFromSelector(if options.parent? then options.parent.$ else null)
        else view
        return view
    
    clone: (options={}) ->
      View(_.extend _.clone(@options), options, {'awake': false})
    
    extend: (options, name) ->
      _.each options, @extend unless name?
      _apply = (_ext) =>
        if _.isFunction _ext then _ext @, options
        else if (_ext = _ext.extend)? then _ext @, options
      
      if (ext = AppKit.exts[name])? then _apply(ext)
      else if _.count(name, '.') is 1
        [repo, name] = name.split('.')
        if (repo = AppKit.exts.repositories[repo])?
          _apply(ext) if (ext = repo[name])?
    
    
    wake: (jq) ->
      return @wakeFromSelector() unless jq?
      return @HasWaken(jq) if _.isFunction jq
      return if @awake
      
      (@$ = jq).data 'view', @
      @awake = yes
      @bindQueue()
      if @willWake().halted
        return @destroy()
      
      _.each @options.events ? [],      _.bind @addEvent,   @
      _.each @options.properties ? [],  _.bind @addProperty,@
      _.each @options.methods ? [],     _.bind @addMethod,  @
      _.each @options.extensions ? {},  _.bind @extend,     @
      
      @hasWaken()
      return @
    
    wakeFromNode: (elem) ->
      @wake $safe(elem)
    
    createFromNode: (elem, options) ->
      @clone(options).wakeFromNode elem
    
    wakeFromSelector: (context) ->
      return unless @options.target?
      @wake $safe(@options.target, context)
    
    createFromSelector: (context) ->
      return unless @options.target?
      @clone().wakeFromSelector(context)
    
    wakeFromTemplate: (data, cb=(->)) ->
      return unless @options.template?
      @options.template data, (content) =>
        cb @wake($(content))
    
    createFromTemplate: (data, cb=(->)) ->
      return unless @options.template?
      @clone().wakeFromTemplate(data, cb)
    
    wakeFromContent: (data, cb=(->)) ->
      return unless @options.content?
      if _.isFunction @options.content
        cb @wake($(_.bind(@options.content, @)(data)))
      if _.isString @options.content
        cb @wake($(@options.content))
      if @options.content.remote?
        data = _.extend(@options.content.data)
        $.get @options.content.remote, data, (content) =>
          cb @wake($(content))
    
    createFromContent: (data, cb=(->)) ->
      return unless @options.content?
      @clone().wakeFromContent data, cb
    
    
    destroy: ->
      return if @willDestroy().halted
      
      delete @__subviews
      delete @__properties
      
      @hasDestroyed()
      @$.remove()
      delete @$
      @awake = no
    
    inject: ->
      if (inj = @options.inject ?= 'append') in ['append', 'prepend']
        @parent.$[inj] @$
      else if _.isNumber inj
        @parent.$.children("nth-child(#{inj+1})").before @$
      else if _.isFunction inj
        _.bind(inj, @) @parent
    
    
    willWake: (fn) ->
      if _.isFunction fn
        @bind 'viewWillWake', fn
      else
        @triggerEvent 'viewWillWake'
    
    hasWaken: (fn) ->
      if _.isFunction fn
        return fn() if @awake
        @bind 'viewHasWaken', fn
      else
        @triggerEvent 'viewHasWaken'
    
    willDestroy: (fn) ->
      if _.isFunction fn
        return fn() if @awake
        @bind 'viewWillDestroy', fn
      else
        @triggerEvent 'viewWillDestroy'
    
    hasDestroyed: (fn) ->
      if _.isFunction fn
        return fn() if @awake
        @bind 'viewHasDestroyed', fn
      else
        @triggerEvent 'viewHasDestroyed'
    
    
    addMethod: (method, name) ->
      # Create methods bound to owner
      if method.method?
        eventType = method.eventType ? name
        method = _.bind method.method, @
        @[name] = (args...) =>
          @trigger eventType, [args...]
          method args...
      else
        @[name] = _.bind(method, @)
    
    addEvent: (handler, eventType) ->
      if _.isArray handler
        (@addEvent handlr, eventType) for handlr in handler
      else if _.isString handler
        if _.isStartsWith handler, '@'
          target = @
          handler = handler[1...]
        else if @parent? then target = @parent
        @bind eventType, (event, args...) =>
          target.trigger handler, [event, args...]
      else
        @bind eventType, _.bind(handler, @)
    
    addView: (view, name) ->
      view.parent = @
      (@__subviews ?= {})[name] = view
    
    getView: (name) -> (@__subviews ?= {})[name]
    getViewForPath: (path) -> AppKit.getViewForPath path, @
    
    find: (sel) -> if @$? then @$.find sel else $()
    
    has: (name) -> (@getProperty name)?
    get: (name, fallback=null) ->
      if (prop = @getProperty name)? then prop.getter()
      else fallback
    
    getMany: (names...) ->
      values = {}
      _.each names, (name) => values[name] = @get name
      values
    
    set: (name, value) ->
      if (prop = @getProperty name)?
        return if (event = prop.triggerEvent('propertyWillChange', value)).halted
        prop.setter event.value
        prop.triggerEvent 'propertyHasChanged', event.value, yes
    
    getProperty: (name) -> (@__properties ?= {})[name]
    addProperty: (property, name) -> 
     if property.selector? or _.isString(property)
        unless property.selector?
          property = {selector: property}
        [selector, attr] = if (splitted = property.selector.split('/')).length == 2
          splitted
        else
          [property.selector, '']
        property = new DOMProperty(@, name, selector, attr, property.field)
      
      else if (view = property.subview)? or (view = property.view)?
        property = new ViewProperty @, name, 
          (if property.subview? then @ else AppKit).getViewForPath(view),
          view.property, view.field
      
      else if property.getter? or property.setter?  
        property = new CustomProperty @, name,
          property.getter, property.setter, property.binder, property.field
      
      else return
      return if @triggerEvent('viewWillAddProperty', property).halted
      (@__properties ?= {})[name] = property
      @triggerEvent 'viewHasAddedProperty', property
    
    
    triggerEvent: (eventType, args...) -> 
      event = new View.Event @, eventType
      event.trigger args...
      return event
    
    trigger: (eventType, data) ->   
      @$.triggerHandler eventType, data
    
    
    bind: (eventType, data, cb) ->
      cb = _.bind cb, @
      if @awake then @$.bind eventType, data, cb
      else (@__bindQueue ?= []).push [eventType, data, cb]
    
    live: (eventType, data, cb) ->
      cb = _.bind cb, @
      if @awake then @$.live eventType, data, cb
      else ($__liveQueue ?= []).push [eventType, data, cb]
    
    
    bindQueue: ->
      _.each (@__bindQueue ? []), (args) => @bind args...
      delete @__bindQueue
      _.each (@__liveQueue ? []), (args) => @live args...
      delete @__liveQueue
    
  
  View.Event = class ViewEvent extends BaseEvent
    constructor: (@view, eventType) ->
      super eventType
      @event.view = @view
    
    @eventType: (type) -> "view#{type}"
    trigger: (args...) -> super @view, args...
  
  AppKit.template = (options) ->
    return options if _.isFunction options
    engine = AppKit.template
      .engines[options.engine ? AppKit.template.defaultEngine]
    return (data, cb) ->
      if (content = options.content)?
        engine content, data, cb
      else if (remote = options.remote)?
        if _.isFunction remote
          remote = _.bind(remote, this)(data)
        
        _data = options.data ? {}
        _data = _.bind(_data, this)(data) if _.isFunction _data
        
        $.get remote, _data, ((content) ->
          options.content = content if options.cache is yes
          engine content, data, cb
        ), 'text'
  
  AppKit.template.engines = {
    mustache: (content, data, cb) ->
      cb _.mustache(content, data)
    
  }
  AppKit.template.defaultEngine = 'mustache'
  
  AppKit.exts = {
    subviews: (obj, views) ->
      _.each views, (viewopts, name) =>
        viewopts.awake ?= yes
        viewopts.parent = obj
        
        subview = View viewopts
        subview.willWake -> subview.inject()
        obj.addView subview, name
    
    listview: (obj, options) ->
      container = if options.selector?
                    obj.find(options.selector).eq 0
                  else obj.$ ? $()
      return unless container.length > 0
      return unless (_selector = (entryopts = options.entry).selector)?
      
      entryopts.parent = obj
      entryview = View entryopts
      
      $$ = obj.entries = -> $$.get()
      _.each {
        Q: (sel) ->
          if sel? then container.find "#{_selector}#{sel}"
          else container.find _selector
        
        get: (index) ->
          if index?
            jq = $$.Q ":nth-child(#{index+1})"
            return view if (view = jq.data 'view')?
            return entryview.createFromNode jq
          
          else _.map _.range($$.size()), $$.get
        
        size: -> $$.Q().length
        
        filterIterator: (spec, entry, index) ->
          return _.all spec, (value, key) -> $$.get(key) is value
        
        find: (spec) ->
          return $$.select _.bind $$.filterIterator, @, spec
        
        findOne: (spec) ->
          return $$.detect _.bind $$.filterIterator, @, spec
        
        
        each: (cb) ->    _.each $$(),   cb, @
        map: (cb) ->     _.map $$(),    cb, @
        detect: (cb) ->  _.detect $$(), cb, @
        select: (cb) ->  _.select $$(), cb, @
        detect: (cb) ->  _.detect $$(), cb, @
        reject: (cb) ->  _.reject $$(), cb, @
        any  : (cb) ->   _.any $$(),    cb, @
        every: (cb) ->   _.every $$(),  cb, @
        pluck: (names...) ->
          $$.map (entry) ->
            data = {}
            _.each names, (name) ->
              if entry.has name
                data[name] = entry.get name
              else if (method = entry[name])? and _.isFunction method
                data[name] = method()
            return data
        
        
        insert: (content, i, cb=(->)) ->
          if $.isPlainObject(content)
            if entryview.createFromTemplate?
              entryview.createFromTemplate content, (view) =>
                @entries.insert view.$, i, cb
              return
            else return
          
          [i, cb] = [null, i] if _.isFunction i
          _jq = $safe content
          
          _view = unless _jq.data('view')?
                    entryview.createFromNode _jq
                  else _jq.data('view')
          
          if not i? or (_size = $$.size()) <= i
            container.append _jq
            i = _size
          else $$.Q(":nth-child(#{i+1})").before _jq
          cb _view
        
        append: (content, cb) ->   $$.insert content, cb
        prepend: (content, cb) ->  $$.insert content, 0, cb
        remove: (i, cb) ->
          if _.isNumber i then view = $$.get i
          else if i instanceof View then view = i
          else if (jq = $safe(i)).length == 1
            return unless (view = jq.data('view'))?
          else return
          event = $.Event('beforeRemoveEntry')
          
          @trigger 'beforeRemoveEntry', [view]
          view.$.remove()
          _.bind(cb, @) view
        
        detach: (i, cb) ->
          if _.isNumber i then view = $$.get i 
          else if i instanceof View then view = i
          else return
          view.$.detach()
          _.bind(cb, @) view
        
      }, (func, name) -> $$[name] = _.bind(func, obj)
      
      $$()
    
    
    register: (exts) ->
      _.extend AppKit.exts.repositories, exts
    
    repositories: {}
  }
  
  UI = {
    extension: UIExtension = (opt) ->
      return (obj, options) ->
        widget = obj[opt.widget] = _.bind obj.$[opt.widget], obj.$
        widget options ? {}
        actions = ['destroy', 'disable', 'enable', 
          'option', 'refresh', (opt.actions ? [])...]
        _.each actions, (action) =>
          widget[action] = _.bind widget, obj.$, action
    
    
    # // TODO : Take care of "special" event binding mechanisms
    #           in some UI extensions (datepicker for instance)
    
    exts: {
      button:       UIExtension {
        widget: 'button'
      }
      buttonset:    UIExtension {
        widget: 'buttonset'
      }
      slider:       UIExtension {
        actions: ['value', 'values']
        widget: 'slider'
      }
      tabs:         UIExtension {
        actions: [
          'add', 'remove', 'select', 'load'
          'url', 'length', 'abort', 'rotate'
        ]
        widget: 'tabs'
      }
      progressbar:  UIExtension {
        actions: ['value']
        widget: 'progressbar'
      }
      accordion:    UIExtension {
        actions: ['activate', 'restart']
        widget: 'accordion'
      }
      autocomplete: UIExtension {
        action: ['search', 'close']
        widget: 'autocomplete'
      }
      datepicker:   UIExtension {
        action: [
          'dialog', 'isDisabled', 'hide', 'show'
          'refresh', 'getDate', 'setDate'
        ]
        widget: 'datepicker'
      }
      dialog:       UIExtension {
        action: [
          'close', 'isOpen', 'moveToTop', 'open'
        ]
        widget: 'dialog'
      }
      
      draggable:    UIExtension {
        widget: 'draggable'
      }
      droppable:    UIExtension {
        widget: 'droppable'
      }
      resizable:    UIExtension {
        widget: 'resizable'
      }
      selectable:   UIExtension {
        actions: ['refresh']
        widget: 'selectable'
      }
      sortable:     UIExtension {
        actions: [
          'serialize', 'toArray', 'refresh'
          'refreshPositions', 'cancel'
        ]
        widget: 'sortable'   
      }
    }
  }
  
  AppKit.exts.register {
    ui: UI.exts
  }
  AppKit.options = (options, fallback) ->
    if $.isPlainObject options
      _.extend (AppKit.__options ?= {}), options
    else if _.isString options
      (AppKit.__options ?= {})[options] ? fallback
  
  
  AppKit.loadView = (url) -> 
    $.getScript "#{AppKit.options('viewURL', '')}#{url}.js"
  
  AppKit.register = (views) ->
    _.each views, (view, name) ->
      view.parent ?= AppKit.viewport
      if _.isString view.parent
        view.parent = AppKit.getViewForPath view.parent
      return unless view.parent instanceof View
      view.parent.addView view, name
  
  
  AppKit.viewport = View {target: 'body', awake: no}
  $ -> AppKit.viewport.wake()
  
)(jQuery)