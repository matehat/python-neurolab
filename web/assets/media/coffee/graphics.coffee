(($) ->
  unless 'min' of Math
    Math.min = (numbers...) ->
      sm = null
      for num in numbers
        unless sm? then sm = num
        else sm = if num < sm then num else sm
  
  
  class Grapher
    constructor: (element) ->
      jq = @jq = $ element
      @data = (key, value) ->
        jq.attr "data-#{key}", value
      
      @numData = (key, value) ->
        if value?
          @data key, new String(value)
        else
          val = parseFloat @data key
          if _.isNaN val then null else val
      
    
  
  class GraphPatch
    constructor: (grapher, i, j) ->
      @grapher = grapher
      @wall = grapher.wall
      @i = i
      @j = j
    
    W: -> @grapher.pW
    H: -> @grapher.pH
    
    scales: -> @grapher.scales()
    
    left: -> @i * @W()
    top:  -> @j * @H()
    
    width:  -> Math.min @W(), @grapher.wW() - @left()
    height: -> Math.min @H(), @grapher.wH() - @top()
    
    valid: -> @left() < @grapher.wW() and @top() < @grapher.wH()
    draw: ->
      @element = $ "<div class=\"graphic-patch\" />"
      [_h, _w] = [@height(), @width()]
      url = "/g/#{@grapher.oid}/#{_w}x#{_h}.png?#{$.param @params()}"
      @element.appendTo(@wall)
      .css
        position: 'absolute'
        left: "#{@left()}px"
        top: "#{@top()}px"
        width: "#{_w}px"
        height: "#{_h}px"
        opacity: 0.0
      image = $("<img src=\"#{url}\" />").css(opacity: 0, position: 'absolute', left: 0, top: 0).appendTo 'body'
      image.load =>
        _.defer =>
          @element.css('background-image': "url(#{url})").animate {opacity: 1}, 500
          image.remove()
    
    params: ->
      scales = @scales()
      x_start:  _x = @left() * scales.x + @grapher.xRange[0]
      x_stop:   _x + @width() * scales.x
      y_stop:   _y = @grapher.yRange[1] - @top() * scales.y
      y_start:  _y - @height() * scales.y
    
  
  class SubGraphPatch extends GraphPatch
    params: ->
      _.extend super(),
        index: @grapher.data 'index'
    
  
  class WaveGrapher extends Grapher
    constructor: (element) ->
      Grapher.call @, element
      @xRange = [@numData('xmin'), @numData('xmax')]
      @yRange = [@numData('ymin'), @numData('ymax')]
      
      @xDelta = @xRange[1] - @xRange[0]
      @yDelta = @yRange[1] - @yRange[0]
      
      @jq.height @numData('image-height') ? 200
      @wall = $('<div class="graphic-wall" />').appendTo @jq
      @patches = {}
      @oid = @data 'oid'
    
    @Patch: GraphPatch
    
    wW: (val) -> @numData('fullwidth', val)   ? @jW()
    wH: (val) -> @numData('fullheight', val)  ? @jH()
    
    jW: -> @jq.width()
    jH: -> @jq.height()
    
    scales: -> x: @xDelta / (@wW()), y: @yDelta / (@wH())
    drawPatches: (x, y) ->
      res = []
      for i in r1 = [(_m=Math.floor(x/@pW))..(_m+Math.ceil(@jW()/@pW))]
        for j in r2 = [(_n=Math.floor(y/@pH))..(_n+Math.ceil(@jH()/@pH))]
          if not @patches["#{i},#{j}"]?
            patch = new @constructor.Patch @, i, j
            continue unless patch.valid()
            (@patches["#{i},#{j}"] = patch).draw()
    
    draw: -> 
      pos = @wall.position()
      @drawPatches pos.left * -1, pos.top * -1
    
    rescale: ->
      @wall.height @wH()
      @wall.width @wW()
      
      for k of @patches
        @patches[k].destroy()
        del @patches[k]
    
    prepare: ->
      @jq.css
        position: 'relative'
        overflow: 'hidden'
      @wall.css
        position: 'absolute'
        top: "0px"
        left: "0px"
      
      [@pW, @pH] = [@jW(), @jH()]
      
      @rescale()
      
      @wall.draggable scroll: no
      @wall.bind 'drag', (event, ui) =>
        drag = @wall.data('draggable').position
        
        if drag.left > 0
          drag.left = 0
        else if drag.left < - (@wW() - @pW)
          drag.left = - (@wW() - @pW)
        
        if drag.top > 0
          drag.top = 0
        else if drag.top < - (@wH() - @pH)
          drag.top = - (@wH() - @pH)
        
        @jq.trigger 'walldrag', [drag]
      
      @jq.bind 'walldrag', (event, drag) => @draw()
      
      @draw()
    
  
  class SubWaveGrapher extends WaveGrapher
    prepare: ->
      super()
      @jq.css 'position', 'absolute'
    
    @Patch: SubGraphPatch
  
  class WaveGroupGrapher extends Grapher
    constructor: (element) ->
      Grapher.call @, element
      @xRange = [@numData('xmin'), @numData('xmax')]
      @yRanges = ((parseFloat(num) for num in _.words(@data(prop), ',')) for prop in ['ymins', 'ymaxs'])
      @count = @numData 'count'
      @oid = @data 'oid'
      
      @jq.height @numData('image-height') ? @count * 100
    
    prepare: ->
      gH = Math.floor @jq.height() / @count
      gW = @jq.width()
      
      @graphers = []
      @jq.css position: 'relative'
      
      for i in [0...@count]
        do (i) =>
          g = $('<div class=\"graphic-subgraph\" />').appendTo @jq
          g.height gH
          g.width gW
          g.attr
            'data-xmin': @xRange[0]
            'data-xmax': @xRange[1]
            'data-ymin': @yRanges[0][i]
            'data-ymax': @yRanges[1][i]
            'data-fullwidth': @data 'fullwidth'
            'data-fullheight': @data 'fullheight'
            'data-image-height': gH
            'data-oid': @oid
            'data-index': i
          
          g.css
            top: "#{i*gH}px"
            left: "0px"
            position: 'absolute'
          
          g = @graphers[i] = new SubWaveGrapher g
          g.prepare()
          g.jq.bind 'walldrag', (event, drag) =>
            for j in [0...@count]
              continue unless i != j
              @graphers[j].wall.css 'left', "#{drag.left}px"
              @graphers[j].draw()
        
    
  
  class ScalogramGrapher extends WaveGrapher
    constructor: (element) ->
      Grapher.call @, element
      @xRange = [@numData('xmin'), @numData('xmax')]
      @yRange = [@numData('ymin'), @numData('ymax')]
      @vRange = [@numData('vmin'), @numData('vmax')]
      
      @xDelta = @xRange[1] - @xRange[0]
      @yDelta = @yRange[1] - @yRange[0]
      
      @jq.height @numData('image-height') ? 200
      @wall = $('<div class="graphic-wall" />').appendTo @jq
      @patches = {}
      @oid = @data 'oid'
    
    @Patch: GraphPatch
  
  class ScalogramSubGrapher extends ScalogramGrapher
    prepare: ->
      super()
      @jq.css 'position', 'absolute'
    
    @Patch: SubGraphPatch
  
  class ScalogramGroupGrapher extends WaveGroupGrapher
    constructor: (element) ->
      Grapher.call @, element
      @xRange = [@numData('xmin'), @numData('xmax')]
      @yRange = [@numData('ymin'), @numData('ymax')]
      @vRanges = ((parseFloat(num) for num in _.words(@data(prop), ',')) for prop in ['vmins', 'vmaxs'])
      @count = @numData 'count'
      @oid = @data 'oid'
      @jq.height @numData('image-height') ? @count * 100
    
    prepare: ->
      gH = Math.floor @jq.height() / @count
      gW = @jq.width()
      
      @graphers = []
      @jq.css position: 'relative'
      console.log 'Preparing', @count
      
      for i in [0...@count]
        do (i) =>
          console.log i
          g = $('<div class=\"graphic-subgraph\" />').appendTo @jq
          g.height gH
          g.width gW
          g.attr
            'data-xmin': @xRange[0]
            'data-xmax': @xRange[1]
            'data-ymin': @yRange[0]
            'data-ymax': @yRange[1]
            'data-vmin': @vRanges[0][i]
            'data-vmax': @vRanges[1][i]
            'data-fullwidth': @data 'fullwidth'
            'data-fullheight': @data 'fullheight'
            'data-image-height': gH
            'data-oid': @oid
            'data-index': i
          
          g.css
            top: "#{i*gH}px"
            left: "0px"
            position: 'absolute'
          
          g = @graphers[i] = new ScalogramSubGrapher g
          console.log g, @jq
          g.prepare()
          g.jq.bind 'walldrag', (event, drag) =>
            for j in [0...@count]
              continue unless i != j
              @graphers[j].wall.css 'left', "#{drag.left}px"
              @graphers[j].draw()
        
    
  
  @$G =
    'wave': WaveGrapher
    'wave-group': WaveGroupGrapher
    'scalogram': ScalogramGrapher
    'scalogram-group': ScalogramGroupGrapher
  
)(jQuery)