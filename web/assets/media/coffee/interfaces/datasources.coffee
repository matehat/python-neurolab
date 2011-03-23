jQuery ($) ->
  bindFileTree = ->
    ftree = $ @
    if ftree.hasClass 'deferred'
      $.get "/datasources/#{ftree.closest('li.datasource').attr('data-oid')}/files", {},
        (data) ->
          new_filetree = $ data
          ftree.replaceWith new_filetree
          bindFileTree.call new_filetree
        , 'html'
    else
      viewer = ftree.find '.file-details'
      files = ftree.find '.level-0'
      files.find('li:not(.file) > span').each ->
        ($ @).siblings('ul').addClass 'collapsed'
      .click (e) ->
        e.preventDefault()
        level = ($ @).toggleClass 'expanded'
        ul = level.siblings('ul').toggleClass('collapsed')
        bindFiles.call(ul) if ul.hasClass 'files'
      .children('ul').removeClass 'collapsed'
  
  bindFiles = ->
    return if @data('bound')?
    datasource = @closest('li.datasource')
    viewer = datasource.find '.file-details'
    @data 'bound', yes
    
    @find('li.file').click ->
      item = $ @
      item.closest('ul.level-0').find('li.selected').removeClass 'selected'
      item.addClass 'selected'
      
      fid = item.attr 'data-oid'
      $.get "/datasources/#{datasource.attr('data-oid')}/files/#{fid}", {},
        (data) =>
          file = $ data
          file.data 'list-item', item
          viewer.find('.empty').hide().end()
            .find("[rel=#{fid}]").remove()
          viewer.find('.file').remove()
          viewer.append file
          bindFile.call file
        
    
  
  bindFile = ->
    file = @
    fid = @attr 'data-oid'
    dsid = @closest('li.datasource').attr 'data-oid'
    
    listItem = @data 'list-item'
    fileList = listItem.closest 'ul.files'
    
    bindFileStructure = ->
      structure = @
      @find('li.cmp').each ->
        cmp = $ @
        cmp.find('span.cmp-name').click (e) ->
          e.preventDefault()
          cmp.toggleClass 'expanded'
      
      @find('.file-controls').buttonset()
        .find('a.load').button
          icons: {primary: 'ui-icon-arrowthick-1-s'}
        .click (e) ->
          e.preventDefault()
          file.loading()
          $.get "/datasources/#{dsid}/files/#{fid}/load/", {},
            (data) ->
              file.unblock()
              load_form = $(data).appendTo 'body'
              load_form.formDialog
                title: "Choose dataset"
              .bind('dialogclose', -> load_form.remove())
              .find(':input').uniform().end()
              .find('ul.compatible-datasets').selectable().end()
              .find('.cancel').click (e) ->
                e.preventDefault()
                load_form.dialog 'close'
              .end().find('.submit').click (e) ->
                e.preventDefault()
                load_form.loading()
                datasets = _.map load_form.find('ul.compatible-datasets li.ui-selected'), 
                  (item) -> $(item).attr 'data-oid'
                $.post "/datasources/#{dsid}/files/#{fid}/load/",
                  $.param({datasets: datasets}),
                  (data) ->
                    load_form.unblock()
                    load_form.dialog 'close'
                    new_structure = $ data.html
                    structure.replaceWith new_structure
                    bindFileStructure.call new_structure
        
        .end().find('a.new-dataset').button
          icons: {primary: 'ui-icon-plus'}
        .click (e) ->
          e.preventDefault()
          file.loading()
          $.get '/db/new',
            {file: fid},
            (data) ->
              file.unblock()
              dataset_form = $(data).appendTo('body')
              component_list = dataset_form.find 'ul.components'
              dataset_form.formDialog 
                title: 'Create new Dataset'
              .bind('dialogclose', -> dataset_form.remove())
              dataset_form.find(':input').uniform()
                .filter('.cancel').click (e) -> 
                  dataset_form.dialog 'close'
                  e.preventDefault()
                .end().filter('.submit').click (e) ->
                  e.preventDefault()
                  dataset_form.loading()
                  $.post '/db/create',
                    dataset_form.formSerialize(),
                    (data) ->
                      dataset_form.unblock()
                      if data.success is yes
                        dataset_form.dialog 'close'
                      else
                        $$.showErrors dataset_form, data
        
    
    def = @find 'div.file.deferred'
    $.get "/datasources/#{dsid}/files/#{fid}/structure", {},
    (data) ->
      def.replaceWith (structure = $ data)
      bindFileStructure.call structure
    
  
  bindDatasource = ->
    ds = $(@)
    ds_id = ds.attr 'data-oid'
    buttons = {
      delete: ds.find('a.delete').button
          icons: {primary: 'ui-icon-minus'}
          text: no
        .click (e) ->
            e.preventDefault()
            return unless confirm 'Are you sure you wish to delete this datasource?'
            $(@).loading()
            $.get "/datasources/#{ds_id}/delete", {},
              (data) ->
                ds.remove()
                ds_list.reload()
        
      refresh: ds.find('a.refresh').button
          icons: {primary: 'ui-icon-refresh'}
          text: no
        .click (e) ->
          e.preventDefault()
          btn = $(@).loading()
          $.get "/datasources/#{ds_id}/files/refresh", {},
            (data) ->
              btn.unblock()
              ds.find('div.files').replaceWith data
              bindFileTree.call ds.find('div.files')
            , 'html'
        
      modify: ds.find('a.modify').button
          icons: {primary: 'ui-icon-pencil'}
          text: no
        .click (e) ->
          e.preventDefault()
          btn = $(@).loading()
          $.get "/datasources/#{ds_id}/edit", {},
            (data) ->
              btn.unblock()
              datasource_form = $(data).appendTo('body')
              datasource_name = datasource_form.find('input[name=name]').val()
              datasource_form.formDialog
                title: "Edit Datasource #{datasource_name}"
              .bind('dialogclose', -> datasource_form.remove())
              .find(':input').uniform()
                .filter('.submit').click (e) ->
                  e.preventDefault()
                  datasource_form.loading()
                  $.post "/datasources/#{ds_id}/update",
                    datasource_form.formSerialize(),
                    (data) ->
                      datasource_form.unblock()
                      if data.success is yes
                        new_ds = $(data.html).insertAfter(ds)
                        ds.remove()
                        bindDatasource.call new_ds
                        datasource_form.dialog 'close'
                        
                        ds_list.reload()
                      else
                        $$.showErrors datasource_form, data
                .end()
                .filter('.cancel').click (e) ->
                  e.preventDefault()
                  datasource_form.dialog 'close'
            , 'html'
        
    }
    ds.find('.controls').buttonset()
    bindFileTree.call ds.find('div.files')
  
  bindDatasourceList = ->
    @is_empty = -> @find('li.datasource').length is 0
    @list = @find 'ul.datasource-entries'
    @links = @find 'ul.links'
    
    @reload = ->
      if @tabs_on?
        @tabs('destroy')

      @links.empty()
      unless @is_empty()
        @tabs_on = yes
        _.each @list.children('li.datasource'), (el) =>
          @links.append "<li><a href=\"\##{(ds = $(el)).attr('id')}\">#{ds.find('h2').text()}</a></li>"
        
        @tabs({})
        @find('li.empty').hide()
      else
        delete @tabs_on if @tabs_on?
        @find('li.empty').show()
    
    @reload()
    @find('li.datasource').each bindDatasource
  
  bindDatasourceList.call ds_list = $('#datasource-list')
  
  $('#content a.create').button({icons: {primary: 'ui-icon-plus'}}).click ->
    btn = $(@).loading()
    $.get '/datasources/new',
      {}, (data) ->
        btn.unblock()
        datasource_form = $(data).appendTo('body')
        datasource_form.formDialog
          title: 'Create new Datasource'
        .bind('dialogclose', -> datasource_form.remove())
        .find(':input').uniform()
          .filter('.submit').click (e) ->
            datasource_form.loading()
            e.preventDefault()
            $.post '/datasources/create',
              datasource_form.formSerialize(),
              (data) ->
                datasource_form.unblock()
                if data.success is yes
                  datasource_form.dialog 'close'
                  new_ds = $(data.html).appendTo(ds_list.list)
                  bindDatasource.call new_ds
                  ds_list.reload()
                else
                  $$.showErrors datasource_form, data
          .end()
          .filter('.cancel').click (e) ->
            e.preventDefault()
            datasource_form.dialog 'close'
      , 'html'
  
