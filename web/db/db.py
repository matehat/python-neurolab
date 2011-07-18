from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf.urls.defaults import *
from django.template.loader import render_to_string

import json
from neurolab.db.models import *
from web.auth import secured_url as secured

def index(request):
    return render_to_response('interfaces/db.html',
        {'datasets': Dataset.objects},
        context_instance=RequestContext(request)
    )

def new(request):
    from neurolab.db.forms import DatasetForm
    from neurolab.db.models import *
    
    try:
        file = SourceFile.objects.get(id=request.REQUEST['file'])
    except SourceFile.DoesNotExist, KeyError:
        raise Http404
    
    if request.method == "POST":
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
    else:
        return render_to_response('partials/db/form.html', {
            'form': DatasetForm(),
            'components': file.components,
            'file': file,
        })

def edit(request, ds_id):
    from neurolab.db.forms import DatasetForm
    from neurolab.db.models import *
    
    try:
        dset = Dataset.objects.with_id(ds_id)
    except Dataset.DoesNotExist:
        raise Http404
    
    if request.method == 'POST':
        import json
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
    else:
        return render_to_response('partials/db/form.html', {
            'form': DatasetForm({
                'name': dset.name,
                'root': dset.root,
                'blockname': dset.blockname,
                'groupname': dset.groupname,
            }),
            'dataset': dset,
        })

def delete(request, ds_id):
    from neurolab.db.models import *
    
    try:
        dset = Dataset.objects.with_id(ds_id)
    except Dataset.DoesNotExist:
        raise Http404
    
    dset.delete()
    return HttpResponse(json.dumps({'success': True}), mimetype="application/json")


def output_new(request, ds_id):
    import json
    from neurolab.db.models import Dataset
    from neurolab.output.models import OutputTemplate
    
    try:
        ds = Dataset.objects.with_id(ds_id)
    except Dataset.DoesNotExist:
        raise Http404
    
    if request.method == 'GET':
        if 'output' in request.GET:
            try:
                template = OutputTemplate.templates[request.GET['output']]
            except KeyError:
                raise Http404
            
            return render_to_response("partials/db/output_form.html", {
                'template': template,
                'form': template.CriteriaForm(),
            })
        else:
            return render_to_response("partials/db/output_new.html", {
                'output_processes': OutputTemplate.templates,
            })
    else:
        output = OutputTemplate.templates[request.POST['output_type']]
        form = output.CriteriaForm
        
        errors = {}
        if request.POST.get('name', '').strip() == '':
            errors['name'] = ['This field is required']
        elif output.objects(dataset=ds, name=request.POST['name']).count():
            errors['name'] = ['This name is already used on this dataset']
        
        if not errors:
            criteria = {k: request.POST[k] for k in form.base_fields if k in request.POST}
            output = output.objects.create(dataset=ds, criteria=criteria, name=request.POST['name'])
            
            return HttpResponse(json.dumps({
                'success': True,
                'html': render_to_string("partials/db/output_item.html", {'template': output})
            }), mimetype="application/json")
        else:
            return HttpResponse(json.dumps(errors), mimetype="application/json")

def output_edit(request, ds_id, op_id):
    import json
    from neurolab.db.models import Dataset
    from neurolab.output.models import OutputTemplate
    
    try:
        ds = Dataset.objects.with_id(ds_id)
        op = OutputTemplate.objects.get(dataset=ds, id=op_id)
    except (Dataset.DoesNotExist, OutputTemplate.DoesNotExist):
        raise Http404
    
    if request.method == 'GET':
        return render_to_response("partials/db/output_edit.html", {
            'form': op.CriteriaForm(initial=op.criteria),
            'output': op,
        })
    else:
        form = op.CriteriaForm
        errors = {}
        if request.POST.get('name', '').strip() == '':
            errors['name'] = ['This field is required']
        elif type(op).objects(dataset=ds, name=request.POST['name'], id__ne=op.id).count():
            errors['name'] = ['This name is already used on this dataset']
        
        if not errors:
            criteria = {k: request.POST[k] for k in form.base_fields if k in request.POST}
            op.criteria.update(criteria)
            op.name = request.POST['name']
            op.save()
        
            return HttpResponse(json.dumps({
                'success': True,
                'html': render_to_string("partials/db/output_item.html", {'template': op})
            }), mimetype="application/json")
        else:
            return HttpResponse(json.dumps(errors), mimetype="application/json")
        

def output_delete(request, ds_id, op_id):
    from neurolab.db.models import Dataset
    from neurolab.output.models import OutputTemplate
    
    try:
        ds = Dataset.objects.with_id(ds_id)
        op = OutputTemplate.objects.get(dataset=ds, id=op_id)
    except (Dataset.DoesNotExist):
        raise Http404
    
    op.delete()
    return HttpResponse("")


def block_view(request, ds_id, block_id):
    import json
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
    except Block.DoesNotExist:
        raise Http404
    
    return HttpResponse(json.dumps({
        'components': render_to_string("partials/db/component/list.html", {'blk': block}),
        'details': render_to_string("partials/db/block/item.html", {'blk': block}),
    }), mimetype="application/json")

def block_delete(request, ds_id, block_id):
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
    except Block.DoesNotExist:
        raise Http404
    block.delete()
    return HttpResponse("")


def block_output_make(request, ds_id, block_id, op_id):
    import json
    from neurolab.db.models import Dataset, Block
    from neurolab.output.models import OutputTemplate, OutputEntry
    
    try:
        ds = Dataset.objects.with_id(ds_id)
        blk = Block.objects.get(dataset=ds, id=block_id)
        template = OutputTemplate.objects.get(dataset=ds, id=op_id)
    except (Dataset.DoesNotExist, Block.DoesNotExist, OutputTemplate.DoesNotExist):
        raise Http404
    
    if request.method == 'GET':
        return render_to_response("partials/db/block/output.html", {
            'form': template.CriteriaForm(initial=template.criteria),
            'output': template,
        })
    else:
        form = template.CriteriaForm(request.POST)
        if form.is_valid():
            template.entry(blk, form.cleaned_data)
            return HttpResponse(json.dumps({'success': True}))
        else:
            return HttpResponse(json.dumps(form.errors), mimetype="application/json")
    

def block_output_discard(request, ds_id, block_id, op_id):
    import json
    from neurolab.db.models import Dataset, Block
    from neurolab.output.models import OutputTemplate, OutputEntry
    
    try:
        ds = Dataset.objects.with_id(ds_id)
        blk = Block.objects.get(dataset=ds, id=block_id)
        template = OutputTemplate.objects.get(dataset=ds, id=op_id)
        entry = OutputEntry.objects.get(block=blk, template=template)
    except (Dataset.DoesNotExist, Block.DoesNotExist, OutputTemplate.DoesNotExist):
        raise Http404
    
    entry.delete(discard=True)
    return HttpResponse("")


def component_view(request, ds_id, block_id, cmp_id):
    from neurolab.db.models import *
    
    try:
        block = Block.objects.get(id=block_id, dataset=ds_id)
        component = block.components().get(id=cmp_id)
    except (Block.DoesNotExist, Component.DoesNotExist):
        raise Http404
    
    return render_to_response("partials/db/component/item.html", {
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
        return render_to_response("partials/db/component/delete.html", {
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
                if Component.objects(parent=component, name=request.POST['name']).count() > 0:
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
            
            return render_to_response("partials/db/component/process_form.html", {
                'task': task,
                'form': task.CriteriaForm(),
                'cmp': component
            })
        else:
            return render_to_response("partials/db/component/process.html", {
                'cmp': component,
            })


urlpatterns = patterns('',
    secured(r'^$',   index),
    secured(r'^new/$', new),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/edit/$', edit),
    secured(r'^(?P<ds_id>[0-9a-f]+)/delete/$', delete),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/output/new/$', output_new),
    secured(r'^(?P<ds_id>[0-9a-f]+)/output/(?P<op_id>[0-9a-f]+)/edit/$', output_edit),
    secured(r'^(?P<ds_id>[0-9a-f]+)/output/(?P<op_id>[0-9a-f]+)/delete/$', output_delete),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/$', block_view),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/delete/$', block_delete),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/output/(?P<op_id>[0-9a-f]+)/make/$', block_output_make),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/output/(?P<op_id>[0-9a-f]+)/discard/$', block_output_discard),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/components/(?P<cmp_id>[0-9a-f]+)/$', component_view),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/components/(?P<cmp_id>[0-9a-f]+)/delete/$', component_delete),
    secured(r'^(?P<ds_id>[0-9a-f]+)/blocks/(?P<block_id>[0-9a-f]+)/components/(?P<cmp_id>[0-9a-f]+)/process/$', component_process),
)