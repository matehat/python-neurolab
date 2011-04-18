(function() {
  this.$$ = {};
  _.extend(this.$$, {
    showErrors: function(form, errors) {
      this.clearErrors(form);
      return _.each(errors, function(errorlist, fieldname) {
        var errorUL, field_label;
        field_label = form.find("div.field." + fieldname + " label").addClass('contains_error');
        errorUL = $('<ul class="error">').insertAfter(field_label);
        return _.each(errorlist, function(error) {
          return errorUL.append("<li>" + error + "</li>");
        });
      });
    },
    clearErrors: function(form) {
      return form.find('div.field').find('ul.error').remove().end().find('label').removeClass('contains_error');
    },
    defaults: {
      formDialog: {
        resizable: false,
        width: 600,
        modal: true,
        position: 'top',
        show: 'fade'
      },
      loading: {
        fadeIn: 100,
        fadeOut: 100,
        message: null,
        overlayCSS: {
          backgroundColor: '#fff'
        }
      },
      blockedForm: {
        fadeIn: 100,
        fadeOut: 100,
        message: null,
        overlayCSS: {
          backgroundColor: '#000'
        }
      }
    }
  });
  $.fn.loading = function(opts) {
    var btn, el, options;
    _.extend(options = {}, $$.defaults.loading, opts != null ? opts : {});
    if ((btn = (el = $(this)).closest('.ui-button')).length > 0) {
      el = btn;
    }
    el.block(options);
    return el;
  };
  $.fn.formDialog = function(opts) {
    var options;
    _.extend(options = {}, $$.defaults.formDialog, opts != null ? opts : {});
    return $(this).dialog(options);
  };
  jQuery(function($) {
    return $(':input').uniform();
  });
}).call(this);
