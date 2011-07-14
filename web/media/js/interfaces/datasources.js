(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  jQuery(function($) {
    var bindDatasource, bindDatasourceList, bindFile, bindFileTree, bindFiles, ds_list;
    bindFileTree = function() {
      var files, ftree, viewer;
      ftree = $(this);
      if (ftree.hasClass('deferred')) {
        return $.get("/datasources/" + (ftree.closest('li.datasource').attr('data-oid')) + "/files/", {}, function(data) {
          var new_filetree;
          new_filetree = $(data);
          ftree.replaceWith(new_filetree);
          return bindFileTree.call(new_filetree);
        }, 'html');
      } else {
        viewer = ftree.find('.file-details');
        files = ftree.find('.level-0');
        return files.find('li:not(.file) > span').each(function() {
          return ($(this)).siblings('ul').addClass('collapsed');
        }).click(function(e) {
          var level, ul;
          e.preventDefault();
          level = ($(this)).toggleClass('expanded');
          ul = level.siblings('ul').toggleClass('collapsed');
          if (ul.hasClass('files')) {
            return bindFiles.call(ul);
          }
        }).children('ul').removeClass('collapsed');
      }
    };
    bindFiles = function() {
      var datasource, viewer;
      if (this.data('bound') != null) {
        return;
      }
      datasource = this.closest('li.datasource');
      viewer = datasource.find('.file-details');
      this.data('bound', true);
      return this.find('li.file').click(function() {
        var fid, item;
        item = $(this);
        item.closest('ul.level-0').find('li.selected').removeClass('selected');
        item.addClass('selected');
        fid = item.attr('data-oid');
        return $.get("/datasources/" + (datasource.attr('data-oid')) + "/files/" + fid + "/", {}, __bind(function(data) {
          var file;
          file = $(data);
          file.data('list-item', item);
          viewer.find('.empty').hide().end().find("[rel=" + fid + "]").remove();
          viewer.find('.file').remove();
          viewer.append(file);
          return bindFile.call(file);
        }, this));
      });
    };
    bindFile = function() {
      var bindFileStructure, def, dsid, fid, file, fileList, listItem;
      file = this;
      fid = this.attr('data-oid');
      dsid = this.closest('li.datasource').attr('data-oid');
      listItem = this.data('list-item');
      fileList = listItem.closest('ul.files');
      bindFileStructure = function() {
        var structure;
        structure = this;
        this.find('li.cmp').each(function() {
          var cmp;
          cmp = $(this);
          return cmp.find('span.cmp-name').click(function(e) {
            e.preventDefault();
            return cmp.toggleClass('expanded');
          });
        });
        return this.find('.file-controls').buttonset().find('a.load').button({
          icons: {
            primary: 'ui-icon-arrowthick-1-s'
          }
        }).click(function(e) {
          e.preventDefault();
          file.loading();
          return $.get("/datasources/" + dsid + "/files/" + fid + "/load/", {}, function(data) {
            var load_form;
            file.unblock();
            load_form = $(data).appendTo('body');
            return load_form.formDialog({
              title: "Choose dataset"
            }).bind('dialogclose', function() {
              return load_form.remove();
            }).find(':input').uniform().end().find('ul.compatible-datasets').selectable().end().find('.cancel').click(function(e) {
              e.preventDefault();
              return load_form.dialog('close');
            }).end().find('.submit').click(function(e) {
              var datasets;
              e.preventDefault();
              load_form.loading();
              datasets = _.map(load_form.find('ul.compatible-datasets li.ui-selected'), function(item) {
                return $(item).attr('data-oid');
              });
              return $.post("/datasources/" + dsid + "/files/" + fid + "/load/", $.param({
                datasets: datasets
              }), function(data) {
                var new_structure;
                load_form.unblock();
                load_form.dialog('close');
                new_structure = $(data.html);
                structure.replaceWith(new_structure);
                return bindFileStructure.call(new_structure);
              });
            });
          });
        }).end().find('a.new-dataset').button({
          icons: {
            primary: 'ui-icon-plus'
          }
        }).click(function(e) {
          e.preventDefault();
          file.loading();
          return $.get('/db/new/', {
            file: fid
          }, function(data) {
            var component_list, dataset_form;
            file.unblock();
            dataset_form = $(data).appendTo('body');
            component_list = dataset_form.find('ul.components');
            dataset_form.formDialog({
              title: 'Create new Dataset'
            }).bind('dialogclose', function() {
              return dataset_form.remove();
            });
            return dataset_form.find(':input').uniform().filter('.cancel').click(function(e) {
              dataset_form.dialog('close');
              return e.preventDefault();
            }).end().filter('.submit').click(function(e) {
              e.preventDefault();
              dataset_form.loading();
              return $.post('/db/new/', dataset_form.formSerialize(), function(data) {
                dataset_form.unblock();
                if (data.success === true) {
                  return dataset_form.dialog('close');
                } else {
                  return $$.showErrors(dataset_form, data);
                }
              });
            });
          });
        });
      };
      def = this.find('div.file.deferred');
      return $.ajax({
        url: "/datasources/" + dsid + "/files/" + fid + "/structure/",
        data: {},
        success: function(data) {
          var structure;
          def.replaceWith((structure = $(data)));
          return bindFileStructure.call(structure);
        },
        statusCode: {
          404: function() {
            return def.replaceWith("<div class=\"not_found\">The source file do not seem to be available</div>");
          }
        }
      });
    };
    bindDatasource = function() {
      var buttons, ds, ds_id;
      ds = $(this);
      ds_id = ds.attr('data-oid');
      buttons = {
        "delete": ds.find('a.delete').button({
          icons: {
            primary: 'ui-icon-minus'
          },
          text: false
        }).click(function(e) {
          e.preventDefault();
          if (!confirm('Are you sure you wish to delete this datasource?')) {
            return;
          }
          $(this).loading();
          return $.get("/datasources/" + ds_id + "/delete/", {}, function(data) {
            ds.remove();
            return ds_list.reload();
          });
        }),
        refresh: ds.find('a.refresh').button({
          icons: {
            primary: 'ui-icon-refresh'
          },
          text: false
        }).click(function(e) {
          var btn;
          e.preventDefault();
          btn = $(this).loading();
          return $.get("/datasources/" + ds_id + "/files/refresh/", {}, function(data) {
            btn.unblock();
            ds.find('div.files').replaceWith(data);
            return bindFileTree.call(ds.find('div.files'));
          }, 'html');
        }),
        modify: ds.find('a.modify').button({
          icons: {
            primary: 'ui-icon-pencil'
          },
          text: false
        }).click(function(e) {
          var btn;
          e.preventDefault();
          btn = $(this).loading();
          return $.get("/datasources/" + ds_id + "/edit/", {}, function(data) {
            var datasource_form, datasource_name;
            btn.unblock();
            datasource_form = $(data).appendTo('body');
            datasource_name = datasource_form.find('input[name=name]').val();
            return datasource_form.formDialog({
              title: "Edit Datasource " + datasource_name
            }).bind('dialogclose', function() {
              return datasource_form.remove();
            }).find(':input').uniform().filter('.submit').click(function(e) {
              e.preventDefault();
              datasource_form.loading();
              return $.post("/datasources/" + ds_id + "/update/", datasource_form.formSerialize(), function(data) {
                var new_ds;
                datasource_form.unblock();
                if (data.success === true) {
                  new_ds = $(data.html).insertAfter(ds);
                  ds.remove();
                  bindDatasource.call(new_ds);
                  datasource_form.dialog('close');
                  return ds_list.reload();
                } else {
                  return $$.showErrors(datasource_form, data);
                }
              });
            }).end().filter('.cancel').click(function(e) {
              e.preventDefault();
              return datasource_form.dialog('close');
            });
          }, 'html');
        })
      };
      ds.find('.controls').buttonset();
      return bindFileTree.call(ds.find('div.files'));
    };
    bindDatasourceList = function() {
      this.is_empty = function() {
        return this.find('li.datasource').length === 0;
      };
      this.list = this.find('ul.datasource-entries');
      this.links = this.find('ul.links');
      this.reload = function() {
        if (this.tabs_on != null) {
          this.tabs('destroy');
        }
        this.links.empty();
        if (!this.is_empty()) {
          this.tabs_on = true;
          _.each(this.list.children('li.datasource'), __bind(function(el) {
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
      return this.find('li.datasource').each(bindDatasource);
    };
    bindDatasourceList.call(ds_list = $('#datasource-list'));
    return $('#content a.create').button({
      icons: {
        primary: 'ui-icon-plus'
      }
    }).click(function() {
      var btn;
      btn = $(this).loading();
      return $.get('/datasources/new/', {}, function(data) {
        var datasource_form;
        btn.unblock();
        datasource_form = $(data).appendTo('body');
        return datasource_form.formDialog({
          title: 'Create new Datasource'
        }).bind('dialogclose', function() {
          return datasource_form.remove();
        }).find(':input').uniform().filter('.submit').click(function(e) {
          datasource_form.loading();
          e.preventDefault();
          return $.post('/datasources/create/', datasource_form.formSerialize(), function(data) {
            var new_ds;
            datasource_form.unblock();
            if (data.success === true) {
              datasource_form.dialog('close');
              new_ds = $(data.html).appendTo(ds_list.list);
              bindDatasource.call(new_ds);
              return ds_list.reload();
            } else {
              return $$.showErrors(datasource_form, data);
            }
          });
        }).end().filter('.cancel').click(function(e) {
          e.preventDefault();
          return datasource_form.dialog('close');
        });
      }, 'html');
    });
  });
}).call(this);
