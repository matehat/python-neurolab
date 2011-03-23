from django import template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from neurolab.db.models import SourceFile

register = template.Library()
file_template = get_template('partials/datasources/sourcefile/item.html')

@register.filter
def filetree(dataset):
    num_levels = len(dataset.treelevels)
    def recurse(level, n=0):
        if isinstance(level, dict):
            last_level = n == num_levels - 1
            items = ""
            for k in sorted(level.iterkeys()):
                val = level[k]
                items = "%s%s" % (items, (
                    "<li class=\"%s\" data-oid=\"%s\"><span>%s<span class=\"icon\"></span></span>\n%s</li>"
                    % (
                        'file'  if last_level else '', 
                        val.id  if last_level else '',
                        k, recurse(val, n+1)
                    )))
            return "<ul class=\"filetree %s\">%s</ul>" % (
                'files' if last_level else 'level-' + str(n), items)
        return ''
    
    return mark_safe(recurse(dataset.filetree()))
