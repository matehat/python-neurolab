(($) ->
  
  root = @
  
  # Utility Methods
  # ===============
  
  # References between Resources
  # ----------------------------
  
  References = (path, _type) ->
    return (callback=(->), error=(->)) ->
      return if @new
      Resource._request @requestURL(path), 'GET', {}, (data) =>
        return error(data) if data.errors?
        objects = []
        for obj in data
          continue unless obj._type is _type.name
          _obj = _type.new obj
          _type.trigger 'fetched', [_obj, data]
          objects.push _obj
        callback objects
    
  
  Reference = (obj, _type) ->
    if obj instanceof Resource
      return Reference {
        '_type': obj.constructor.name, 
        '_id': obj.id()
      }, obj.constructor
    
    func = (callback=(->), error=(->)) ->
      return if @new or _type.name is not obj._type
      _type.query obj._id, callback, error
    
    $.extend func, obj
    return func
  
  
  @Serializer = class Serializer
  
  # Event Types
  # -----------
  
  EVENTS = 
    changed: (type) -> "resourceChanged.#{type}"
    created: (type) -> "resourceCreated.#{type}"
    updated: (type) -> "resourceUpdated.#{type}"
    fetched: (type) -> "resourceFetched.#{type}"
    deleted: (type) -> "resourceDeleted.#{type}"
  
  # ===================
  # Base Resource Class
  # ===================
  
  @Resource = class Resource
    
    # =============
    # Class Methods
    # =============
    
    # Fundamental Ajax Methods
    # ------------------------
    
    @_request: (url, type, data='GET', callback=(->)) ->
      $.ajax
        url: url
        type: type
        data: data
        success: callback
        error: (xhr, text) ->
          console.error "Error requesting: #{url}, response: #{text}"
    
    @_requestURL: (bits..., data) ->
      (bits = ['base', bits...]).push(data) if _.isString data
      url = (@::urls[bit] ? bit for bit in bits)
      url = url.join ''
      for match in url.match(/:[a-zA-Z_]{1}[a-zA-Z0-9_]*/) or []
        key = match[1...match.length]
        if data[key]?
          url = url.replace match, "#{data[key]}"
      return url
    
    @_serialize: (data) ->
      result = {}
      for key of data
        val = data[key]
        if $.isPlainObject val or $.isArray val
          result[key] = JSON.stringify val
        else if _.isFunction(val) and val._type? and val._id?
          result["#{key}_id"] = val._id
          result["#{key}_type"] = val._type
        else if _.isString val or _.isNumber val
          result[key] = val
        else
          continue
      return result
    
    
    # Event-Related Methods
    # ---------------------
    
    @trigger: (eventType, data) ->
      $.event.trigger EVENTS[eventType](@name), data
    
    @bind: (eventType, data, callback) ->
      $(root).bind EVENTS[eventType](@name), data, callback
    
    
    # Server Interactions
    # -------------------
    
    @all: (params, callback=(->), error=(->)) ->
      return unless @::urls.all?
      [callback, params] = [params, {}] if _.isFunction params
      Resource._request @_requestURL('all'), 'GET', {}, (data) =>
        return error(data) if data.errors?
        objects = []
        for obj in data
          continue unless obj._type is @name
          _obj = @new obj
          @trigger 'fetched', [_obj, data]
          objects.push _obj
        callback objects
      
    
    @query: (id, callback=(->), error=(->)) ->
      return unless @::urls.get?
      Resource._request @_requestURL('base', 'get', {id: id}), 'GET', {}, (data) =>
        return error(data) if data.errors?
        return unless data._type is @name
        obj = @new data
        @trigger 'fetched', [obj, data]
        callback obj
    
    
    # Instance Creation
    # -----------------
    
    @new: (obj) ->
      _.bind(->
        @modified = no
        @_cache = {}
        @_data = {}
        @set obj
        @new = not @get('_id')?
        @
      , new @)()
    
    
    # ================
    # Instance Methods
    # ================
    
    # Event-Related Methods
    # ---------------------
    
    trigger: (eventType, data) ->  
      $.event.trigger EVENTS[eventType](@constructor.name), data
    
    bind: (eventType, data, callback) ->
      $(root).bind EVENTS[eventType](@constructor.name), data, callback
    
    
    # Properties Getter/Setter
    # ------------------------
    
    merge: (data) ->
      @_cache = {}
      @set data
      @new = no
    
    set: (key, value) ->
      if $.isPlainObject key
        for k of key
          @set k, key[k]
        return key
      else if value instanceof Resource
        value = Reference value
      
      return unless (value isnt @get key)
      if value? and value._type? and value._id? and not _.isFunction value
        return if value._type.match(/[^\w]/)?
        type = eval value._type
        @_data[key] = Reference(value, type)
      else
        @_data[key] = value
      @modified = yes
      @trigger 'changed', [@, key, value]
      value
    
    get: (key) -> @_data[key]
    getAsync: (key, cached=yes, callback=(->), error=(->)) ->
      [cached, callback, error] = [yes, cached, callback] if _.isFunction cached
      unless _.isFunction @_data[key] then  _.defer(=> callback(@_data[key], @))
      else if cached and @_cache[key]? then _.defer(=> callback(@_cache[key], @))
      else
        _cb = (value) =>
          @_cache[key] = value if cached
          callback value, @
        @_data[key].apply @, [_cb, error]
    
    
    # Data introspection
    # ------------------
    
    id: -> @.get('_id') ? null
    serialized: ->
      return @constructor._serialize @_data
    
    requestURL: (bits...) ->
      return @constructor._requestURL 'base', bits..., {id: @id()}
    
    
    # Upstream interactions
    # ---------------------
    save: (callback=(->), error=(->)) ->
      if @new then @create(callback, error) else @update(callback, error)
    
    update: (callback=(->), error=(->)) ->
      return if @new or not @urls.update? or not @modified
      Resource._request @requestURL('update'), 'POST', @serialized(), (data) =>
        return error(data) if data.errors?
        if data._id? and data._type is @constructor.name
          @merge data
        @modified = no
        @trigger 'updated', [@, data]
        callback @
    
    create: (callback=(->), error=(->)) ->
      return unless @new or not @urls.new?
      Resource._request @requestURL('new'), 'POST', @serialized(), (data) =>
        return error(data) if data.errors?
        if data._id? and data._type is @constructor.name
          @merge data
        @modified = no
        @trigger 'created', [@, data]
        callback @
    
    delete: (callback=(->), error=(->)) ->
      return if @new or not @urls.delete?
      Resource._request @requestURL('delete'), 'GET', {}, (data) =>
        return error(data) if data.errors?
        @trigger 'deleted', [@, data]
        callback @
    
  
  
  # ========================================
  # CUSTOM RESOURCES
  # Attached to window for global visibility 
  # (hence the @ - alias for window)
  # ========================================
  
  # Components
  
  @Component = class Component extends Resource
    urls:
      base:   '/components/'
      new:    "new/"
      get:    ":id/"
      update: ":id/update/"
      delete: ":id/delete/"
  
  @Component.Base = class ComponentBase extends Resource 
    urls:
      base:   '/components/bases/'
      new:    "new/"
      get:    ":id/"
      update: ":id/update/"
      delete: ":id/delete/"
    
    instances: References "instances/", Component
  
  
  # Blocks
  
  @Block = class Block extends Resource 
    urls:
      base:   '/blocks/'
      new:    'new/'
      get:    ':id/'
      update: ':id/put/'
      delete: ':id/delete/'

    components: References 'components/', Component
  
  @Block.Base = class BlockBase extends Resource 
    urls:
      base:   '/blocks/bases/'
      new:    'new/'
      get:    ':id/'
      update: ':id/put/'
      delete: ':id/delete/'

    instances:  References 'instances/', Block
    components: References 'components/', ComponentBase
  
  @Block.Template = class BlockTemplate extends Resource 
    urls:
      base:   '/blocks/templates/'
      new:    'new/'
      get:    ':id/'
      update: ':id/put/'
      delete: ':id/delete/'
  
  
  # Protocols
  
  @Protocol = class Protocol extends Resource
    urls:
      base:   '/protocols/'
      new:    "new/"
      all:    "all/"
      get:    "/"
      update: "/update/"
      delete: "/delete/"
    
    blocks: References "blocks/", BlockTemplate
  
  
  # Observables
  
  @Observable = class Observable extends Resource
    urls:
      base:   '/observables/'
      new:    'new/'
      get:    ':id/'
      update: ':id/put/'
      delete: ':id/delete/'
    
    blocks: References ':id/blocks/', Block
  
  @Observable.Base = class ObservableBase extends Resource
    urls:
      base:   '/observables/bases/'
      all:    'all/'
      new:    'new/'
      get:    ':id/'
      update: ':id/put/'
      delete: ':id/delete/'
    
    instances:  References ':id/instances/', Observable
    blocks:     References ':id/blocks/', BlockBase
  
  
  null
)(jQuery)