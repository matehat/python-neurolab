(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  jQuery(function($) {
    var bindDataset, bindDatasetList, ds_list;
    bindDataset = function() {
      var bindBlock, bindOutputTemplate, buttons, controls, ds, ds_id, ds_url, processes, viewer;
      ds = $(this);
      ds_id = ds.attr('data-oid');
      ds_url = "/db/" + ds_id;
      viewer = ds.find('div.right-pane');
      controls = ds.children('.controls').buttonset();
      buttons = {
        "delete": controls.children('a.delete').button({
          icons: {
            primary: 'ui-icon-trash'
          }
        }).click(function(e) {
          e.preventDefault();
          if (!confirm('Are you sure you wish to delete this dataset?')) {
            return;
          }
          return $.get("" + ds_url + "/delete/", {}, function(data) {
            ds.remove();
            return ds_list.reload();
          });
        }),
        modify: controls.children('a.modify').button({
          icons: {
            primary: 'ui-icon-pencil'
          }
        }).click(function(e) {
          e.preventDefault();
          return $.get("" + ds_url + "/edit/", {}, function(data) {
            var dataset_form, dataset_name;
            dataset_form = $(data).appendTo('body');
            dataset_name = dataset_form.find('input[name=name]').val();
            return dataset_form.formDialog({
              title: "Edit Dataset " + dataset_name
            }).bind('dialogclose', function() {
              return dataset_form.remove();
            }).find(':input').uniform().filter('.submit').click(function(e) {
              e.preventDefault();
              return $.post("" + ds_url + "/edit/", dataset_form.formSerialize(), function(data) {
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
      bindOutputTemplate = function() {
        var templ_id, templ_url, template;
        template = $(this);
        templ_id = template.attr('data-oid');
        templ_url = "" + ds_url + "/output/" + templ_id;
        return template.children('.controls').buttonset().children('.modify').button({
          icons: {
            primary: 'ui-icon-pencil'
          },
          text: false
        }).click(function(e) {
          e.preventDefault();
          template.loading();
          return $.get("" + templ_url + "/edit/", {}, function(data) {
            var template_form;
            template.unblock();
            template_form = $(data).appendTo('body');
            template_form.formDialog({
              title: "Edit template of output process"
            });
            template_form.bind('dialogclose', function() {
              return template_form.remove();
            });
            return template_form.find(":input").uniform().filter('.submit').click(function(e) {
              e.preventDefault();
              template_form.loading();
              return $.post("" + templ_url + "/edit/", template_form.formSerialize(), function(data) {
                var new_template;
                template_form.unblock();
                if (data.success === true) {
                  new_template = $(data.html).insertAfter(template);
                  template.remove();
                  bindOutputTemplate.call(new_template);
                  return template_form.dialog('close');
                } else {
                  return $$.showErrors(template_form, data);
                }
              });
            }).end().filter('.cancel').click(function(e) {
              e.preventDefault();
              return template_form.dialog('close');
            });
          });
        }).end().children('.delete').button({
          icons: {
            primary: 'ui-icon-trash'
          },
          text: false
        }).click(function(e) {
          e.preventDefault();
          if (!confirm("Are you sure you wish to delete this output process?")) {
            return;
          }
          template.loading();
          return $.get("" + templ_url + "/delete/", {}, function(data) {
            return template.slideUp(100, function() {
              return template.remove();
            });
          });
        });
      };
      bindBlock = function() {
        var bindOutputEntry, block, block_id, block_url, output_entries;
        block = $(this);
        block_id = block.attr('data-oid');
        block_url = "" + ds_url + "/blocks/" + block_id;
        bindOutputEntry = function() {
          var entry, entry_url, templ_id;
          entry = $(this);
          templ_id = entry.attr('data-template-oid');
          entry_url = "" + block_url + "/output/" + templ_id;
          return entry.find('a.make').button({
            icons: {
              primary: 'ui-icon-play'
            },
            text: false
          }).click(function(e) {
            e.preventDefault();
            entry.loading();
            return $.get("" + entry_url + "/make/", {}, function(data) {
              var entry_form;
              entry.unblock();
              entry_form = $(data).appendTo('body');
              entry_form.formDialog({
                title: "Initiate an processed output"
              });
              entry_form.bind('dialogclose', function() {
                return entry_form.remove();
              });
              return entry_form.find(":input").uniform().filter('.submit').click(function(e) {
                e.preventDefault();
                entry_form.loading();
                return $.post("" + entry_url + "/make/", entry_form.formSerialize(), function(data) {
                  entry_form.unblock();
                  console.log(data.success, data.success === true);
                  if (data.success === true) {
                    entry.addClass('initiated');
                    return entry_form.dialog('close');
                  } else {
                    return $$.showErrors(entry_form, data);
                  }
                }, 'json');
              }).end().filter('.cancel').click(function(e) {
                e.preventDefault();
                return entry_form.dialog('close');
              });
            });
          }).end().find('a.discard').button({
            icons: {
              primary: 'ui-icon-trash'
            },
            text: false
          }).click(function(e) {
            e.preventDefault();
            if (!confirm("Are you sure you wish to discard that processed output?")) {
              return;
            }
            entry.loading();
            return $.get("" + entry_url + "/discard/", {}, function(data) {
              entry.unblock();
              return entry.removeClass('initiated');
            });
          }).end().find('a.show-files').button({
            icons: {
              primary: 'ui-icon-folder-open'
            },
            text: false
          }).click(function(e) {
            e.preventDefault();
            entry.find('ul.output-entry-files').show();
            return $(this).hide();
          }).end().find('ul.output-entry-files').hide();
        };
        block.find('div.block-controls a.delete').button({
          icons: {
            primary: 'ui-icon-trash'
          },
          text: false
        }).click(function(e) {
          return e.preventDefault();
        });
        output_entries = block.find('ul.output-processes');
        return output_entries.children().each(bindOutputEntry);
      };
      processes = ds.find('dd.output-processes').children('ul');
      (function(processes) {
        var ul;
        (ul = processes)._toggler = $('<a class="show-output-processes">Show processes</a>');
        ul._empty = processes.children().length === 0;
        ul._show = function(fn) {
          if (processes._empty) {
            return;
          }
          ul.slideDown(100, fn);
          return ul._toggler.fadeOut(100, function() {
            return $(this).remove();
          });
        };
        if (!ul._empty) {
          return ul._toggler.appendTo(ul.hide().parent()).button({
            icons: {
              primary: 'ui-icon-triangle-1-s'
            }
          }).click(function(e) {
            e.preventDefault();
            return ul._show();
          });
        }
      })(processes);
      ds.find('dd.output-processes > ul.output-processes > li').each(bindOutputTemplate);
      ds.find('dd.output-processes a.create').button({
        icons: {
          primary: "ui-icon-plus"
        }
      }).click(function(e) {
        var create_template, url;
        e.preventDefault();
        (create_template = $(this)).loading();
        url = "" + ds_url + "/output/new/";
        return $.get(url, {}, function(data) {
          var form_body, template_form;
          create_template.unblock();
          template_form = $(data).appendTo('body');
          form_body = template_form.find('.output-form-body');
          return template_form.formDialog({
            title: "Create an output process"
          }).bind('dialogclose', function() {
            return template_form.remove();
          }).find('[name=output_type]').change(function() {
            return $.get(url, {
              'output': $(this).val()
            }, function(data) {
              form_body.empty().append(data);
              form_body.find(':input').uniform().end();
              template_form.find('.submit').removeAttr('disabled');
              return $.uniform.update();
            });
          }).end().find(":input").uniform().filter('.submit').click(function(e) {
            e.preventDefault();
            template_form.loading();
            return $.post(url, template_form.formSerialize(), function(data) {
              template_form.unblock();
              if (data.success === true) {
                bindOutputTemplate.call($(data.html).appendTo(processes));
                return template_form.dialog('close');
              } else {
                return $$.showErrors(template_form, data);
              }
            });
          }).end().filter('.cancel').click(function(e) {
            e.preventDefault();
            return template_form.dialog('close');
          });
        });
      });
      return ds.find('ul.groups > li.group').each(function() {
        var group;
        group = $(this);
        group.children('span.group-name').click(function(e) {
          e.preventDefault();
          return group.toggleClass('expanded');
        });
        return group.find('ul.blocks li.block').each(function() {
          var bindComponent, bindComponents, block, block_id, block_url;
          block = $(this);
          block_id = block.attr('data-oid');
          block_url = "" + ds_url + "/blocks/" + block_id;
          bindComponent = function() {
            var cmp, cmp_id, graph_element, show_preview, type;
            cmp = $(this);
            cmp_id = cmp.attr('data-oid');
            graph_element = cmp.find('.component-image').hide();
            show_preview = cmp.find('a.preview').button({
              icons: {
                primary: 'ui-icon-search'
              }
            });
            if ((type = graph_element.attr('data-type')) != null) {
              show_preview.click(function(e) {
                var grapher;
                e.preventDefault();
                show_preview.remove();
                graph_element.show();
                grapher = new $G[type](graph_element);
                return grapher.prepare();
              });
            } else {
              show_preview.add(graph_element).remove();
            }
            cmp.find('div.breadcrumbs .go-block').click(function(e) {
              e.preventDefault();
              $(this).loading();
              return $.get("" + block_url + "/", {}, function(data) {
                var block_view;
                block_view = $(data.details);
                ds.find('li.cmp.selected').removeClass('selected');
                viewer.children(":not(.empty)").remove().end().find('.empty').hide().end().append(block_view);
                return bindBlock.call(block_view);
              });
            });
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
              var cmp, cmp_id;
              cmp = $(this);
              cmp_id = cmp.attr('data-oid');
              return cmp.find('span.cmp-name').click(function(e) {
                var cmp_title;
                e.preventDefault();
                cmp_title = $(this);
                if (cmp.hasClass('selected')) {
                  return;
                }
                block.loading();
                return $.get("" + block_url + "/components/" + cmp_id + "/", {}, function(data) {
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
            url = "" + block_url + "/delete/";
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
            var block_title, cmps;
            e.preventDefault();
            block_title = $(this);
            if (block.hasClass('expanded')) {
              return block.removeClass('expanded');
            } else {
              if ((cmps = block_title.siblings('ul.components')).length > 0) {
                ds.find('li.block').removeClass('expanded');
                cmps.remove();
              }
            }
            block.loading();
            return $.get("" + block_url + "/", {}, function(data) {
              var block_view;
              block.unblock();
              cmps = $(data.components);
              cmps.insertAfter(block_title);
              ds.find('li.block').removeClass('expanded');
              block.addClass('expanded');
              bindComponents.call(cmps);
              block_view = $(data.details);
              viewer.children(":not(.empty)").remove().end().find('.empty').hide().end().append(block_view);
              return bindBlock.call(block_view);
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
