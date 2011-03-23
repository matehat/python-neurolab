from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf.urls.defaults import *
from django.template.loader import render_to_string

from neurolab.db.models import *
from web.auth import secured_url as secured

def index(request):
    return render_to_response('interfaces/db.html',
        {'datasets': Dataset.objects},
        context_instance=RequestContext(request)
    )

def new(request):
    from neurolab.db.forms import DatasetForm
    from neurolab.db.models import Component, SourceFile
    
    try:
        file = SourceFile.objects.get(id=request.GET['file'])
    except SourceFile.DoesNotExist, KeyError:
        raise Http404
    
    return render_to_response('partials/db/form.html', {
        'form': DatasetForm(),
        'components': file.components,
        'file': file,
    })

def create(request):
    import json
    from neurolab.db.forms import DatasetForm
    from neurolab.db.models import *
    
    try:
        file = SourceFile.objects.get(id=request.POST['file'])
    except SourceFile.DoesNotExist, KeyError:
        raise Http404
    
    form = DatasetForm(request.POST)
    errors = {}
    if len(request.POST.getlist('components')) == 0:
        errors['components'] = ['You must select at least 1 component']
    
    if form.is_valid() and not errors:
        dset = Dataset(**form.cleaned_data)
        dset.permit_user(request.user, 'admin')
        dset.components = []
        
        for name in request.POST.getlist('components'):
            if name not in file.components:
                return HttpResponseBadRequest()
            
            base = file.components[name]
            componentform = Component.registry[base['type']].CriteriaForm(base)
            if not componentform.is_valid():
                return HttpResponseBadRequest()
            
            template = ComponentTemplate.objects.create(
                name=base['name'], 
                component_slug=base['type'],
                criteria=componentform.cleaned_data,
            )
            dset.components.append(template)
        
        dset.save()
        return HttpResponse(json.dumps({'success': True}), 
            mimetype="application/json")
    else:
        errors.update(form.errors or {})
        return HttpResponse(json.dumps(errors), mimetype="application/json")
    

def edit(request, ds_id):
    from neurolab.db.forms import DatasetForm
    from neurolab.db.models import *
    
    try:
        dset = Dataset.objects.with_id(ds_id)
    except Dataset.DoesNotExist:
        raise Http404
    
    return render_to_response('partials/db/form.html', {
        'form': DatasetForm({
            'name': dset.name,
            'root': dset.root,
            'blockname': dset.blockname,
            'groupname': dset.groupname,
        }),
        'dataset': dset,
    })

def update(request, ds_id):
    import json
    from neurolab.db.forms import DatasetForm
    from neurolab.db.models import *
    
    try:
        dset = Dataset.objects.with_id(ds_id)
    except Dataset.DoesNotExist:
        raise Http404
    
    form = DatasetForm(request.POST)
    if form.is_valid():
        for k in form.cleaned_data:
            setattr(dset, k, form.cleaned_data[k])
        dset.save()
        
        return HttpResponse(json.dumps({
            'success': True,
            'html': render_to_string(
                "partials/db/item.html",
                {'dataset': dset}
            )
        }), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(form.errors.copy()), mimetype="application/json")
    

def delete(request, ds_id):
    from neurolab.db.models import *
    
    try:
        dset = Dataset.objects.with_id(ds_id)
    except Dataset.DoesNotExist:
        raise Http404
    
    dset.delete()
    return HttpResponse(json.dumps({'success': True}), mimetype="application/json")


def block_delete(request, ds_id, block_id):
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
    except Block.DoesNotExist:
        raise Http404
    block.delete()
    return HttpResponse("")

def block_components(request, ds_id, block_id):
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
    except Block.DoesNotExist:
        raise Http404
    
    return render_to_response("partials/db/block/components.html", {'blk': block})

def block_view(request, ds_id, block_id):
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
        component = block.components().get(name=request.GET.get('component', ''))
    except (Block.DoesNotExist, Component.DoesNotExist):
        raise Http404
    
    return render_to_response("partials/db/block/component.html", {
        'cmp': component,
    })


def component_delete(request, ds_id, block_id, cmp_id):
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
        component = block.components().with_id(cmp_id)
    except (Block.DoesNotExist, Component.DoesNotExist):
        raise Http404
    
    if request.method == 'POST':
        discard = 'discard' in request.POST
        delete_template = 'delete_template' in request.POST
        
        if delete_template:
            template = component.template
            for child in template.offspring():
                child.template = None
                child.save()
            for instance in template.instances():
                pass
                instance.delete(discard)
            template.delete()
        else:
            component.delete(discard)
        
        return HttpResponse("")
    else:
        return render_to_response("partials/db/block/component_delete.html", {
            'cmp': component,
        })

def component_process(request, ds_id, block_id, cmp_id):
    import json
    from neurolab.db.models import *
    from neurolab.tasks.models import ProcessingTask
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
        component = block.components().with_id(cmp_id)
    except (Block.DoesNotExist, Component.DoesNotExist):
        raise Http404
    
    if request.method == 'POST':
        template = 'template' in request.POST
        task = ProcessingTask.tasks[request.POST['process_type']]
        form = task.CriteriaForm(request.POST)
        errors = {}
        if 'name' not in request.POST:
            errors['name'] = ['This field is required']
        
        if not errors and form.is_valid():
            criteria = form.cleaned_data
            if template:
                if ComponentTemplate.objects(parent=component.template, name=request.POST['name']).count() > 0:
                    raise Http404
                
                ComponentTemplate.objects.create(parent=component.template, name=request.POST['name'],
                    task_slug=task.slug, criteria=criteria)
                component.template.update()
            else:
                if task.objects(argument.component, name=request.POST['name']).count() > 0:
                    raise Http404
                
                task.create(name=request.POST['name'], argument=component, criteria=criteria)
            
            return HttpResponse(json.dumps({'success': True}), mimetype="application/json")
        else:
            errors.update(form.errors)
            return HttpResponse(json.dumps(errors), mimetype="application/json")
    else:
        if 'task' in request.GET:
            try:
                task = ProcessingTask.tasks[request.GET['task']]
            except KeyError:
                raise Http404
            
            return render_to_response("partials/db/block/component_processform.html", {
                'task': task,
                'form': task.CriteriaForm(),
                'cmp': component
            })
        else:
            return render_to_response("partials/db/block/component_process.html", {
                'cmp': component,
            })


urlpatterns = patterns('',
    secured(r'^$',   index),
    secured(r'^new$', new),
    secured(r'^create$', create),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/edit$', edit),
    secured(r'^(?P<ds_id>[0-9a-f]+)/update$', update),
    secured(r'^(?P<ds_id>[0-9a-f]+)/delete$', delete),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/delete/$', block_delete),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/components/$', block_components),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/components/(?P<cmp_id>[0-9a-f]+)/delete/$', component_delete),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/components/(?P<cmp_id>[0-9a-f]+)/process/$', component_process),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/view/', block_view),
)