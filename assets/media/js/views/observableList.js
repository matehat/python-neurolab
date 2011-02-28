(function() {
  var observableForm;
  observableForm = AppKit.template({
    remote: '/t/forms/observable-type-form.html',
    cache: true
  });
  AppKit({
    observableList: AppKit.View({
      target: '#observable-list',
      awake: true,
      events: {
        addObservable: function() {
          return this.entries.insert({
            id: 'new',
            name: 'Fill this'
          });
        }
      },
      extensions: {
        'ui.accordeon': {},
        subviews: {
          create: {
            awake: true,
            target: 'a.create',
            events: {
              click: 'addObservable'
            },
            extensions: {
              'ui.button': {
                text: false,
                icons: {
                  primary: 'ui-icon-plus'
                }
              }
            },
            template: {
              content: ""
            }
          }
        },
        listview: {
          selector: 'ul.observable-entries',
          entry: {
            template: {
              content: "<li class='observable-type' rel='{{ id }}'>\n  <h2>{{ name }}</h2>\n  <a class=\"delete\">Delete</a>\n  <a class=\"modify\">Modify</a>\n</li>"
            },
            selector: "li.observable-type",
            events: {
              "delete": function() {
                return this.$.remove();
              },
              modify: function() {
                return this.showModifyForm();
              },
              viewWillWake: function() {
                return console.log('New Entry!');
              },
              saveModifyWindow: function() {
                return alert("Saved!");
              }
            },
            methods: {
              showModifyForm: function() {
                return this.getView('modifyForm').wakeFromTemplate(this.getMany('name', 'id'));
              }
            },
            properties: {
              name: 'h2',
              id: '/rel'
            },
            extensions: {
              subviews: {
                "delete": {
                  target: 'a.delete',
                  events: {
                    click: 'delete'
                  },
                  extensions: {
                    'ui.button': {
                      text: false,
                      icons: {
                        primary: 'ui-icon-minus'
                      }
                    }
                  }
                },
                modify: {
                  target: 'a.modify',
                  events: {
                    click: 'modify'
                  },
                  extensions: {
                    'ui.button': {
                      text: false,
                      icons: {
                        primary: 'ui-icon-pencil'
                      }
                    }
                  }
                },
                modifyForm: {
                  awake: false,
                  inject: 'append',
                  target: 'form.observable-type-form',
                  template: observableForm,
                  properties: {
                    id: 'input[name=id]',
                    name: 'input[name=name]',
                    description: ':input[name=description]',
                    formatter: 'input[name=formatter]'
                  },
                  events: {
                    dialogclose: function() {
                      return this.destroy();
                    },
                    dialogopen: function() {
                      return this.dialog.option('title', "Modify Observable: " + (this.get('name')));
                    },
                    save: 'saveModifyWindow'
                  },
                  extensions: {
                    'ui.dialog': {
                      show: 'fade',
                      title: 'Modify observable',
                      resizable: false,
                      buttons: {
                        Save: function() {
                          var form;
                          form = $(this).data('view');
                          return form.destroy();
                        }
                      },
                      width: 450
                    },
                    subviews: {
                      save: {
                        target: 'a.save',
                        events: {
                          click: 'save'
                        },
                        extensions: {
                          'ui.button': {
                            text: false,
                            icons: {
                              primary: 'ui-icon-disk'
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    })
  });
}).call(this);
