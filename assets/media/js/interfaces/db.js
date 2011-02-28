(function() {
  (function($) {
    AppKit.options({
      viewURL: '/media/js/views/'
    });
    return AppKit(function() {
      return AppKit.loadView('observableList');
    });
  })(jQuery);
}).call(this);
