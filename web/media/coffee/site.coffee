@$$ = {}
_.extend @$$, 
  showErrors: (form, errors) ->
    @clearErrors form
    _.each errors, (errorlist, fieldname) ->
      field_label = form.find("div.field.#{fieldname} label").addClass 'contains_error'
      errorUL = $('<ul class="error">').insertAfter field_label
      _.each errorlist, (error) -> errorUL.append "<li>#{error}</li>"
  
  clearErrors: (form) ->
    form.find('div.field').find('ul.error').remove()
      .end().find('label').removeClass 'contains_error'
  
  defaults:
    formDialog:
      resizable: false
      width: 600
      modal: true
      position: 'top'
      show: 'fade'
    loading:
      fadeIn: 100
      fadeOut: 100
      message: null
      overlayCSS:
        backgroundColor: '#fff'
    blockedForm:
      fadeIn: 100
      fadeOut: 100
      message: null
      overlayCSS:
        backgroundColor: '#000'

$.fn.loading = (opts) ->
  _.extend options = {}, $$.defaults.loading, (opts ? {})
  if (btn = (el = $(@)).closest('.ui-button')).length > 0
    el = btn
  el.block options
  return el

$.fn.formDialog = (opts) ->
  _.extend options = {}, $$.defaults.formDialog, (opts ? {})
  $(@).dialog options

jQuery ($) ->
  $(':input').uniform()