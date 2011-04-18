jQuery ($) ->
  bindDataset = ->
    ds = $ @
    ds_id = ds.attr 'data-oid'
    ds_url = "/db/#{ds_id}"
    
    viewer = ds.find 'div.right-pane'
    controls = ds.children('.controls').buttonset()
    buttons = {
      delete: controls.children('a.delete').button
          icons: {primary: 'ui-icon-trash'}
        .click (e) ->
            e.preventDefault()
            return unless confirm 'Are you sure you wish to delete this dataset?'
            $.get "#{ds_url}/delete/", {},
              (data) ->
                ds.remove()
                ds_list.reload()
        
      modify: controls.children('a.modify').button
          icons: {primary: 'ui-icon-pencil'}
        .click (e) ->
          e.preventDefault()
          $.get "#{ds_url}/edit/", {},
            (data) ->
              dataset_form = $(data).appendTo('body')
              dataset_name = dataset_form.find('input[name=name]').val()
              dataset_form.formDialog
                title: "Edit Dataset #{dataset_name}"
              .bind('dialogclose', -> dataset_form.remove())
              .find(':input').uniform()
                .filter('.submit').click (e) ->
                  e.preventDefault()
                  $.post "#{ds_url}/edit/",
                    dataset_form.formSerialize(),
                    (data) ->
                      if data.success is yes
                        new_ds = $(data.html).insertAfter ds
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
    
    bindOutputTemplate = ->
      template = $ @
      templ_id = template.attr 'data-oid'
      templ_url = "#{ds_url}/output/#{templ_id}"
      template.children('.controls').buttonset()
        .children('.modify')
          .button
            icons: {primary: 'ui-icon-pencil'}
            text: no
          .click (e) ->
            e.preventDefault()
            template.loading()
            $.get "#{templ_url}/edit/", {},
              (data) ->
                template.unblock()
                template_form = $(data).appendTo 'body'
                template_form.formDialog title: "Edit template of output process"
                template_form.bind 'dialogclose', -> template_form.remove()
                template_form.find(":input").uniform()
                  .filter('.submit').click (e) ->
                    e.preventDefault()
                    template_form.loading()
                    $.post "#{templ_url}/edit/",
                      template_form.formSerialize(),
                      (data) ->
                        template_form.unblock()
                        if data.success is yes
                          new_template = $(data.html).insertAfter template
                          template.remove()
                          bindOutputTemplate.call new_template
                          template_form.dialog 'close'
                        else
                          $$.showErrors template_form, data
                          
                  .end().filter('.cancel').click (e) ->
                    e.preventDefault()
                    template_form.dialog 'close'
              
        .end().children('.delete')
          .button
            icons: {primary: 'ui-icon-trash'}
            text: no
          .click (e) ->
            e.preventDefault()
            return unless confirm "Are you sure you wish to delete this output process?"
            template.loading()
            $.get "#{templ_url}/delete/", {},
              (data) ->
                template.slideUp 100, -> template.remove()
            
    
    bindBlock = ->
      block = $ @
      block_id = block.attr 'data-oid'
      block_url = "#{ds_url}/blocks/#{block_id}"
      
      bindOutputEntry = ->
        entry = $ @
        templ_id = entry.attr 'data-template-oid'
        entry_url = "#{block_url}/output/#{templ_id}"
        
        entry.find('a.make').button
          icons: {primary: 'ui-icon-play'}
          text: no
        .click (e) ->
          e.preventDefault()
          entry.loading()
          $.get "#{entry_url}/make/", {},
            (data) ->
              entry.unblock()
              entry_form = $(data).appendTo 'body'
              entry_form.formDialog title: "Initiate an processed output"
              entry_form.bind 'dialogclose', -> entry_form.remove()
              entry_form.find(":input").uniform()
                .filter('.submit').click (e) ->
                  e.preventDefault()
                  entry_form.loading()
                  $.post "#{entry_url}/make/",
                    entry_form.formSerialize(),
                    (data) ->
                      entry_form.unblock()
                      console.log data.success, data.success is yes
                      if data.success is yes
                        entry.addClass 'initiated'
                        entry_form.dialog 'close'
                      else
                        $$.showErrors entry_form, data
                    , 'json'
                        
                .end().filter('.cancel').click (e) ->
                  e.preventDefault()
                  entry_form.dialog 'close'
              
              
        
        .end().find('a.discard').button
          icons: {primary: 'ui-icon-trash'}
          text: no
        .click (e) ->
          e.preventDefault()
          return unless confirm "Are you sure you wish to discard that processed output?"
          entry.loading()
          $.get "#{entry_url}/discard/", {}, (data) -> 
            entry.unblock()
            entry.removeClass 'initiated'
        
        .end().find('a.show-files').button
          icons: {primary: 'ui-icon-folder-open'}
          text: no
        .click (e) ->
          e.preventDefault()
          entry.find('ul.output-entry-files').show()
          $(@).hide()
        
        .end().find('ul.output-entry-files').hide()
      
      block.find('div.block-controls a.delete').button
        icons: {primary: 'ui-icon-trash'}
        text: no
      .click (e) -> e.preventDefault()
      
      output_entries = block.find 'ul.output-processes'
      output_entries.children().each bindOutputEntry
    
    
    processes = ds.find('dd.output-processes').children 'ul'
    do (processes) ->
      (ul = processes)._toggler = $ '<a class="show-output-processes">Show processes</a>'
      ul._empty = (processes.children().length == 0)
      ul._show = (fn) ->
        return if processes._empty
        ul.slideDown 100, fn
        ul._toggler.fadeOut 100, -> $(@).remove()
      
      
      unless ul._empty
        ul._toggler.appendTo(ul.hide().parent())
        .button(icons: primary: 'ui-icon-triangle-1-s').click (e) ->
          e.preventDefault()
          ul._show()
        
    
    
    ds.find('dd.output-processes > ul.output-processes > li').each bindOutputTemplate
    ds.find('dd.output-processes a.create').button({icons: primary: "ui-icon-plus"}).click (e) ->
      e.preventDefault()
      (create_template = $(@)).loading()
      url = "#{ds_url}/output/new/"
      $.get url, {},
        (data) ->
          create_template.unblock()
          template_form = $(data).appendTo 'body'
          form_body = template_form.find '.output-form-body'
          template_form.formDialog(title: "Create an output process")
            .bind('dialogclose', -> template_form.remove())
            .find('[name=output_type]').change ->
                $.get url, {'output': $(@).val()}, (data) ->
                  form_body.empty().append data
                  form_body.find(':input').uniform().end()
                  template_form.find('.submit').removeAttr('disabled')
                  $.uniform.update()
            .end().find(":input").uniform()
            .filter('.submit').click (e) ->
              e.preventDefault()
              template_form.loading()
              $.post url, template_form.formSerialize(),
                (data) ->
                  template_form.unblock()
                  if data.success is yes
                    bindOutputTemplate.call $(data.html).appendTo processes
                    template_form.dialog 'close'
                  else
                    $$.showErrors template_form, data
            
            .end().filter('.cancel').click (e) ->
              e.preventDefault()
              template_form.dialog 'close'
        
    
    ds.find('ul.groups > li.group').each ->
      group = $ @
      group.children('span.group-name').click (e) -> 
        e.preventDefault()
        group.toggleClass('expanded')
      
      group.find('ul.blocks li.block').each ->
        block = $ @
        block_id = block.attr 'data-oid'
        block_url = "#{ds_url}/blocks/#{block_id}"
        
        bindComponent = ->
          cmp = $ @
          cmp_id = cmp.attr 'data-oid'
          graph_element = cmp.find('.component-image').hide()
          show_preview = cmp.find('a.preview').button
            icons: primary: 'ui-icon-search'
          
          if (type = graph_element.attr 'data-type')?
            show_preview.click (e) ->
              e.preventDefault()
              show_preview.remove()
              graph_element.show()
              grapher = new $G[type] graph_element
              grapher.prepare()
          else
            show_preview.add(graph_element).remove()
          
          cmp.find('div.breadcrumbs .go-block').click (e) ->
            e.preventDefault()
            $(@).loading()
            $.get "#{block_url}/", {},
              (data) ->
                block_view = $ data.details
                ds.find('li.cmp.selected').removeClass 'selected'
                viewer.children(":not(.empty)").remove().end()
                  .find('.empty').hide().end()
                  .append block_view

                bindBlock.call block_view
          
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
            cmp_id = cmp.attr 'data-oid'
            cmp.find('span.cmp-name').click (e) ->
              e.preventDefault()
              cmp_title = $ @
              return if cmp.hasClass 'selected'
              block.loading()
              $.get "#{block_url}/components/#{cmp_id}/", {},
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
          url = "#{block_url}/delete/"
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
            if (cmps = block_title.siblings('ul.components')).length > 0
              ds.find('li.block').removeClass 'expanded'
              cmps.remove()
          
          block.loading()
          $.get "#{block_url}/", {},
            (data) ->
              block.unblock()
              cmps = $ data.components
              cmps.insertAfter block_title
              ds.find('li.block').removeClass 'expanded'
              block.addClass 'expanded'
              bindComponents.call cmps
              
              block_view = $ data.details
              viewer.children(":not(.empty)").remove().end()
                .find('.empty').hide().end()
                .append block_view
              
              bindBlock.call block_view
        
      
    
  
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
