(($) ->
  AppKit.options {
    viewURL: '/media/js/views/'
  }
  AppKit ->
    AppKit.loadView 'observableList'
  
)(jQuery)