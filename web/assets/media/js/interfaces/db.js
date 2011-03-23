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
            var cmp, graph_element, grapher, type;
            cmp = $(this);
            graph_element = cmp.find('.component-image');
            if ((type = graph_element.attr('data-type')) != null) {
              grapher = new $G[type](graph_element);
              return grapher.prepare();
            }
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
                  viewer.empty().append(cmp_viewer);
                  return bindComponent.call(cmp_viewer);
                });
              });
            });
          };
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
