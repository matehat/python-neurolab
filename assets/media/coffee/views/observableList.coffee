observableForm = AppKit.template
  remote: '/t/forms/observable-type-form.html'
  cache: yes

AppKit

  observableList: AppKit.View
    target: '#observable-list'
    awake: yes
    events:
      addObservable: ->
        @entries.insert
          id: 'new'
          name: 'Fill this'
      
    extensions:
      'ui.accordeon': {}
      subviews:
        create:
          awake: yes
          target: 'a.create'
          events:
            click: 'addObservable'
          extensions:
            'ui.button':
              text: no
              icons:
                primary: 'ui-icon-plus'
          
          template:
            content: ""
          
          
      listview:
        selector: 'ul.observable-entries'
        entry:
          template:
            content:  """
                      <li class='observable-type' rel='{{ id }}'>
                        <h2>{{ name }}</h2>
                        <a class="delete">Delete</a>
                        <a class="modify">Modify</a>
                      </li>
                      """
          
          selector:   "li.observable-type"
          events:
            delete: -> @$.remove()
            modify: -> @showModifyForm()
            viewWillWake: ->
              console.log 'New Entry!'
            
            saveModifyWindow: ->
              alert "Saved!"
          
          methods:
            showModifyForm: ->
              @getView('modifyForm').wakeFromTemplate @getMany('name', 'id')
          
          properties:
            name: 'h2'
            id:   '/rel'
        
          extensions:
            subviews:
              delete:
                target: 'a.delete'
                events:
                  click:  'delete'
                extensions:
                  'ui.button':
                    text: no
                    icons:
                      primary: 'ui-icon-minus'
              
              modify:
                target: 'a.modify'
                events:
                  click: 'modify'
                
                extensions:
                  'ui.button':
                    text: no
                    icons:
                      primary: 'ui-icon-pencil'
              
              modifyForm:
                awake: no
                inject: 'append'
                target: 'form.observable-type-form'
                template: observableForm
                
                properties:
                  id:   'input[name=id]'
                  name: 'input[name=name]'
                  description: ':input[name=description]'
                  formatter: 'input[name=formatter]'
                
                events:
                  dialogclose: -> @destroy()
                  dialogopen: ->
                    @dialog.option 'title', "Modify Observable: #{@get 'name'}"
                  
                  save:  'saveModifyWindow'
                
                extensions:
                  'ui.dialog': 
                    show: 'fade'
                    title: 'Modify observable'
                    resizable: no
                    buttons:
                      Save: ->
                        form = $(@).data 'view'
                        form.destroy()
                    
                    width: 450
                  
                  subviews:
                    save:
                      target: 'a.save'
                      events:
                        click: 'save'
                      
                      extensions:
                        'ui.button':
                          text: no
                          icons:
                            primary: 'ui-icon-disk'