jQuery ($) ->
  bindDataset = ->
    ds = $ @
    ds_id = ds.attr 'data-oid'
    viewer = ds.find 'div.block-view'
    buttons = {
      delete: ds.find('a.delete').button
          icons: {primary: 'ui-icon-minus'}
          text: no
        .click (e) ->
            e.preventDefault()
            return unless confirm 'Are you sure you wish to delete this dataset?'
            $.get "/db/#{ds_id}/delete", {},
              (data) ->
                ds.remove()
                ds_list.reload()
        
      modify: ds.find('a.modify').button
          icons: {primary: 'ui-icon-pencil'}
          text: no
        .click (e) ->
          e.preventDefault()
          $.get "/db/#{ds_id}/edit", {},
            (data) ->
              dataset_form = $(data).appendTo('body')
              dataset_name = dataset_form.find('input[name=name]').val()
              dataset_form.formDialog
                title: "Edit Dataset #{dataset_name}"
              .bind('dialogclose', -> dataset_form.remove())
              .find(':input').uniform()
                .filter('.submit').click (e) ->
                  e.preventDefault()
                  $.post "/db/#{ds_id}/update",
                    dataset_form.formSerialize(),
                    (data) ->
                      if data.success is yes
                        new_ds = $(data.html).insertAfter(ds)
                        ds.remove()
                        bindDataset.call new_ds
                        dataset_form.dialog 'close'
                        
                        ds_list.reload()
                      else
                        $$.showErrors dataset_form, data
                .end()
                .filter('.cancel').click (e) ->
                  e.preventDefault()
                  dataset_form.dialog 'close'
            , 'html'
        
    }
    ds.find('.controls').buttonset()
    ds.find('ul.groups > li.group').each ->
      group = $ @
      group.children('span.group-name').click (e) -> 
        e.preventDefault()
        group.toggleClass('expanded')
      
      group.find('ul.blocks li.block').each ->
        block = $ @
        block_id = block.attr 'data-oid'
        bindComponent = ->
          cmp = $ @
          cmp_id = cmp.attr 'data-oid'
          graph_element = cmp.find '.component-image'
          if (type = graph_element.attr 'data-type')?
            grapher = new $G[type] graph_element
            grapher.prepare()
          
          cmp.find('a.delete').button
            icons: 
              primary: 'ui-icon-trash'
            text: no
          .click (e) ->
            e.preventDefault()
            cmp.loading()
            url = "/db/#{ds_id}/blocks/#{block_id}/components/#{cmp_id}/delete/"
            $.get url, {},
              (data) ->
                cmp.unblock()
                delete_form = $(data).appendTo 'body'
                delete_form.formDialog
                  title: 'Delete a component?'
                .bind('dialogclose', -> delete_form.remove())
                .find(':input').uniform().end()
                .find('.cancel').click (e) -> 
                  e.preventDefault()
                  delete_form.dialog 'close'
                .end().find('.submit').click (e) ->
                  e.preventDefault()
                  $.post url, delete_form.formSerialize(), ->
                    viewer.children(":not(.empty)").remove().end()
                      .find('.empty').show()
                    $("li.block ul.components li").filter(-> $(@).attr('data-oid') is cmp_id).remove()
                    delete_form.dialog 'close'
                  
          
          cmp.find('a.process').button
            icons: 
              primary: 'ui-icon-arrowthick-1-e'
            text: no
          .click (e) ->
            e.preventDefault()
            cmp.loading()
            url = "/db/#{ds_id}/blocks/#{block_id}/components/#{cmp_id}/process/"
            $.get url, {},
              (data) ->
                cmp.unblock()
                proc_form = $(data).appendTo 'body'
                form_body = proc_form.find '.process-form-body'
                console.log form_body
                proc_form.formDialog
                  title: 'Process this component?'
                .bind('dialogclose', -> proc_form.remove())
                .find(':input').uniform().end()
                .find('.cancel').click (e) -> 
                  e.preventDefault()
                  proc_form.dialog 'close'
                .end().find('[name=process_type]').change ->
                  $.get url, {'task': $(@).val()}, (data) ->
                    form_body.empty().append data
                    form_body.find(':input').uniform().end()
                    proc_form.find('.submit').removeAttr('disabled')
                    $.uniform.update()
                .end().find('.submit').click (e) ->
                  e.preventDefault()
                  $.post url, form_body.closest('form').formSerialize(),
                    (data) ->
                      if data.success
                        proc_form.dialog 'close'
                      else
                        $$.showErrors proc_form, data
                    , 'json'
          
          cmp.find('div.component-controls').buttonset()
        
        bindComponents = ->
          cmps = @
          cmps.find('li.cmp').each ->
            cmp = $ @
            cmp.find('span.cmp-name').click (e) ->
              e.preventDefault()
              cmp_title = $ @
              return if cmp.hasClass 'selected'
              block.loading()
              $.get "/db/#{ds_id}/blocks/#{block_id}/view/", 
                {component: _.strip(cmp_title.text())},
                (data) ->
                  block.unblock()
                  ds.find('li.cmp.selected').removeClass 'selected'
                  cmp.addClass 'selected'
                  cmp_viewer = $ data
                  viewer.children(":not(.empty)").remove().end()
                    .find('.empty').hide().end()
                    .append cmp_viewer
                  bindComponent.call cmp_viewer
        
        block.find('span.block-name > span.icon.delete').click (e) ->
          e.preventDefault()
          url = "/db/#{ds_id}/blocks/#{block_id}/delete/"
          return unless confirm "Are you sure you wish to delete this block?\nData on disk will be kept intact."
          block.loading()
          $.get url, {}, ->
            block.remove()
            viewer.children(':not(.empty)').remove().end().find('.empty').show()
        
        block.children('span.block-name').click (e) ->
          e.preventDefault()
          block_title = $ @
          if block.hasClass 'expanded'
            return block.removeClass 'expanded'
          else
            if block_title.siblings('ul.components').length > 0
              ds.find('li.block').removeClass 'expanded'
              return block.addClass 'expanded'
          
          block.loading()
          $.get "/db/#{ds_id}/blocks/#{block_id}/components/", {},
            (data) ->
              block.unblock()
              cmps = $ data
              cmps.insertAfter block_title
              ds.find('li.block').removeClass 'expanded'
              block.addClass 'expanded'
              bindComponents.call cmps
        
      
    
  
  bindDatasetList = ->
    @is_empty = -> @find('li.dataset').length is 0
    @list = @find 'ul.dataset-entries'
    @links = @find 'ul.links'
    
    @reload = ->
      if @tabs_on?
        @tabs('destroy')

      @links.empty()
      unless @is_empty()
        @tabs_on = yes
        _.each @list.children('li.dataset'), (el) =>
          @links.append "<li><a href=\"\##{(ds = $(el)).attr('id')}\">#{ds.find('h2').text()}</a></li>"
        
        @tabs({})
        @find('li.empty').hide()
      else
        delete @tabs_on if @tabs_on?
        @find('li.empty').show()
    
    @reload()
    @find('li.dataset').each bindDataset
  
  bindDatasetList.call ds_list = $('#dataset-list')
