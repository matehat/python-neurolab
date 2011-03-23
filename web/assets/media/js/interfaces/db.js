(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  jQuery(function($) {
    var bindDataset, bindDatasetList, ds_list;
    bindDataset = function() {
      var buttons, ds, ds_id, viewer;
      ds = $(this);
      ds_id = ds.attr('data-oid');
      viewer = ds.find('div.block-view');
      buttons = {
        "delete": ds.find('a.delete').button({
          icons: {
            primary: 'ui-icon-minus'
          },
          text: false
        }).click(function(e) {
          e.preventDefault();
          if (!confirm('Are you sure you wish to delete this dataset?')) {
            return;
          }
          return $.get("/db/" + ds_id + "/delete", {}, function(data) {
            ds.remove();
            return ds_list.reload();
          });
        }),
        modify: ds.find('a.modify').button({
          icons: {
            primary: 'ui-icon-pencil'
          },
          text: false
        }).click(function(e) {
          e.preventDefault();
          return $.get("/db/" + ds_id + "/edit", {}, function(data) {
            var dataset_form, dataset_name;
            dataset_form = $(data).appendTo('body');
            dataset_name = dataset_form.find('input[name=name]').val();
            return dataset_form.formDialog({
              title: "Edit Dataset " + dataset_name
            }).bind('dialogclose', function() {
              return dataset_form.remove();
            }).find(':input').uniform().filter('.submit').click(function(e) {
              e.preventDefault();
              return $.post("/db/" + ds_id + "/update", dataset_form.formSerialize(), function(data) {
                var new_ds;
                if (data.success === true) {
                  new_ds = $(data.html).insertAfter(ds);
                  ds.remove();
                  bindDataset.call(new_ds);
                  dataset_form.dialog('close');
                  return ds_list.reload();
                } else {
                  return $$.showErrors(dataset_form, data);
                }
              });
            }).end().filter('.cancel').click(function(e) {
              e.preventDefault();
              return dataset_form.dialog('close');
            });
          }, 'html');
        })
      };
      ds.find('.controls').buttonset();
      return ds.find('ul.groups > li.group').each(function() {
        var group;
        group = $(this);
        group.children('span.group-name').click(function(e) {
          e.preventDefault();
          return group.toggleClass('expanded');
        });
        return group.find('ul.blocks li.block').each(function() {
          var bindComponent, bindComponents, block, block_id;
          block = $(this);
          block_id = block.attr('data-oid');
          bindComponent = function() {
            var cmp, cmp_id, graph_element, grapher, type;
            cmp = $(this);
            cmp_id = cmp.attr('data-oid');
            graph_element = cmp.find('.component-image');
            if ((type = graph_element.attr('data-type')) != null) {
              grapher = new $G[type](graph_element);
              grapher.prepare();
            }
            cmp.find('a.delete').button({
              icons: {
                primary: 'ui-icon-trash'
              },
              text: false
            }).click(function(e) {
              var url;
              e.preventDefault();
              cmp.loading();
              url = "/db/" + ds_id + "/blocks/" + block_id + "/components/" + cmp_id + "/delete/";
              return $.get(url, {}, function(data) {
                var delete_form;
                cmp.unblock();
                delete_form = $(data).appendTo('body');
                return delete_form.formDialog({
                  title: 'Delete a component?'
                }).bind('dialogclose', function() {
                  return delete_form.remove();
                }).find(':input').uniform().end().find('.cancel').click(function(e) {
                  e.preventDefault();
                  return delete_form.dialog('close');
                }).end().find('.submit').click(function(e) {
                  e.preventDefault();
                  return $.post(url, delete_form.formSerialize(), function() {
                    viewer.children(":not(.empty)").remove().end().find('.empty').show();
                    $("li.block ul.components li").filter(function() {
                      return $(this).attr('data-oid') === cmp_id;
                    }).remove();
                    return delete_form.dialog('close');
                  });
                });
              });
            });
            cmp.find('a.process').button({
              icons: {
                primary: 'ui-icon-arrowthick-1-e'
              },
              text: false
            }).click(function(e) {
              var url;
              e.preventDefault();
              cmp.loading();
              url = "/db/" + ds_id + "/blocks/" + block_id + "/components/" + cmp_id + "/process/";
              return $.get(url, {}, function(data) {
                var form_body, proc_form;
                cmp.unblock();
                proc_form = $(data).appendTo('body');
                form_body = proc_form.find('.process-form-body');
                console.log(form_body);
                return proc_form.formDialog({
                  title: 'Process this component?'
                }).bind('dialogclose', function() {
                  return proc_form.remove();
                }).find(':input').uniform().end().find('.cancel').click(function(e) {
                  e.preventDefault();
                  return proc_form.dialog('close');
                }).end().find('[name=process_type]').change(function() {
                  return $.get(url, {
                    'task': $(this).val()
                  }, function(data) {
                    form_body.empty().append(data);
                    form_body.find(':input').uniform().end();
                    proc_form.find('.submit').removeAttr('disabled');
                    return $.uniform.update();
                  });
                }).end().find('.submit').click(function(e) {
                  e.preventDefault();
                  return $.post(url, form_body.closest('form').formSerialize(), function(data) {
                    if (data.success) {
                      return proc_form.dialog('close');
                    } else {
                      return $$.showErrors(proc_form, data);
                    }
                  }, 'json');
                });
              });
            });
            return cmp.find('div.component-controls').buttonset();
          };
          bindComponents = function() {
            var cmps;
            cmps = this;
            return cmps.find('li.cmp').each(function() {
              var cmp;
              cmp = $(this);
              return cmp.find('span.cmp-name').click(function(e) {
                var cmp_title;
                e.preventDefault();
                cmp_title = $(this);
                if (cmp.hasClass('selected')) {
                  return;
                }
                block.loading();
                return $.get("/db/" + ds_id + "/blocks/" + block_id + "/view/", {
                  component: _.strip(cmp_title.text())
                }, function(data) {
                  var cmp_viewer;
                  block.unblock();
                  ds.find('li.cmp.selected').removeClass('selected');
                  cmp.addClass('selected');
                  cmp_viewer = $(data);
                  viewer.children(":not(.empty)").remove().end().find('.empty').hide().end().append(cmp_viewer);
                  return bindComponent.call(cmp_viewer);
                });
              });
            });
          };
          block.find('span.block-name > span.icon.delete').click(function(e) {
            var url;
            e.preventDefault();
            url = "/db/" + ds_id + "/blocks/" + block_id + "/delete/";
            if (!confirm("Are you sure you wish to delete this block?\nData on disk will be kept intact.")) {
              return;
            }
            block.loading();
            return $.get(url, {}, function() {
              block.remove();
              return viewer.children(':not(.empty)').remove().end().find('.empty').show();
            });
          });
          return block.children('span.block-name').click(function(e) {
            var block_title;
            e.preventDefault();
            block_title = $(this);
            if (block.hasClass('expanded')) {
              return block.removeClass('expanded');
            } else {
              if (block_title.siblings('ul.components').length > 0) {
                ds.find('li.block').removeClass('expanded');
                return block.addClass('expanded');
              }
            }
            block.loading();
            return $.get("/db/" + ds_id + "/blocks/" + block_id + "/components/", {}, function(data) {
              var cmps;
              block.unblock();
              cmps = $(data);
              cmps.insertAfter(block_title);
              ds.find('li.block').removeClass('expanded');
              block.addClass('expanded');
              return bindComponents.call(cmps);
            });
          });
        });
      });
    };
    bindDatasetList = function() {
      this.is_empty = function() {
        return this.find('li.dataset').length === 0;
      };
      this.list = this.find('ul.dataset-entries');
      this.links = this.find('ul.links');
      this.reload = function() {
        if (this.tabs_on != null) {
          this.tabs('destroy');
        }
        this.links.empty();
        if (!this.is_empty()) {
          this.tabs_on = true;
          _.each(this.list.children('li.dataset'), __bind(function(el) {
            var ds;
            return this.links.append("<li><a href=\"\#" + ((ds = $(el)).attr('id')) + "\">" + (ds.find('h2').text()) + "</a></li>");
          }, this));
          this.tabs({});
          return this.find('li.empty').hide();
        } else {
          if (this.tabs_on != null) {
            delete this.tabs_on;
          }
          return this.find('li.empty').show();
        }
      };
      this.reload();
      return this.find('li.dataset').each(bindDataset);
    };
    return bindDatasetList.call(ds_list = $('#dataset-list'));
  });
}).call(this);
