from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.conf.urls.defaults import *

from neurolab.db.models import *
from web.auth import secured_url as secured

def index(request):
    return render_to_response('interfaces/datasources.html',
        {'datasources': Datasource.objects},
        context_instance=RequestContext(request)
    )

def new(request):
    from neurolab.db.forms import DatasourceForm
    return render_to_response('partials/datasources/form.html', {
        'form': DatasourceForm()
    })

def create(request):
    import json
    from neurolab.db.forms import DatasourceForm
    from neurolab.db.models import Datasource
    
    form = DatasourceForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        for k in ('pathlevels', 'treelevels'):
            data[k] = filter(None, data[k].split('\n'))
        
        dset = Datasource(**data)
        dset.permit_user(request.user, 'admin')
        dset.save()
        
        return HttpResponse(json.dumps({
            'success': True,
            'html': render_to_string(
                "partials/datasources/item.html",
                {'datasource': dset}
            )
        }), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(form.errors.copy()), mimetype="application/json")

def edit(request, ds_id):
    from neurolab.db.forms import DatasourceForm
    from neurolab.db.models import Datasource
    
    try:
        ds = Datasource.objects.with_id(ds_id)
    except Datasource.DoesNotExist:
        raise Http404
    
    return render_to_response('partials/datasources/form.html', {
        'form': DatasourceForm({
            'name': ds.name,
            'root': ds.root,
            'pathlevels': "\n".join(ds.pathlevels),
            'treelevels': "\n".join(ds.treelevels),
            'fileformat': ds.fileformat
        }),
        'datasource': ds,
    })

def update(request, ds_id):
    import json
    from neurolab.db.forms import DatasourceForm
    from neurolab.db.models import Datasource
    
    try:
        ds = Datasource.objects.with_id(ds_id)
    except Datasource.DoesNotExist:
        raise Http404
    
    form = DatasourceForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        for k in ('pathlevels', 'treelevels'):
            data[k] = filter(None, data[k].split('\n'))
        
        for k in data:
            setattr(ds, k, data[k])
        ds.save()
        return HttpResponse(json.dumps({
            'success': True,
            'html': render_to_string(
                "partials/datasources/item.html",
                {'datasource': ds}
            )
        }), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(form.errors.copy()), mimetype="application/json")

def delete(request, ds_id):
    import json
    from neurolab.db.models import Datasource
    
    try:
        ds = Datasource.objects.with_id(ds_id)
    except Datasource.DoesNotExist:
        raise Http404
    
    ds.delete()
    return HttpResponse(json.dumps({'success': True}), mimetype="application/json")


def sourcefile(request, ds_id, file_id):
    from neurolab.db.models import SourceFile, Dataset, Datasource
    
    try:
        file = SourceFile.objects.get(id=file_id, datasource=ds_id)
    except SourceFile.DoesNotExist, KeyError:
        raise Http404
    
    return render_to_response('partials/datasources/sourcefile/item.html', {'file': file})

def sourcefile_structure(request, ds_id, file_id):
    from neurolab.db.models import SourceFile
    import json
    
    try:
        file = SourceFile.objects.get(id=file_id, datasource=ds_id)
    except SourceFile.DoesNotExist, KeyError:
        raise Http404
    
    resp = HttpResponse(json.dumps({'success': False}), mimetype="application/json")
    resp.status_code = 404
    return resp
    
    try:
        file_infos = file.infos
    except IOError:
        resp = HttpResponse(json.dumps({'success': False}), mimetype="application/json")
        resp.status_code = 404
        return resp
    
    return render_to_response('partials/datasources/sourcefile/structure.html', {
        'file': file, 
        'infos': file_infos,
        'datasets': file.datasets()
    })

def sourcefile_load(request, ds_id, file_id):
    import json
    from neurolab.db.models import SourceFile
    
    try:
        file = SourceFile.objects.get(id=file_id, datasource=ds_id)
        datasets = file.datasets()
    except SourceFile.DoesNotExist, KeyError:
        raise Http404
    
    if request.method == 'GET':
        return render_to_response('partials/datasources/sourcefile/loadform.html', {
            'file': file, 'datasets': datasets})
    elif request.method == 'POST':
        dataset_dict = {str(ds.id): ds for ds in datasets}
        for dataset_id in request.POST.getlist('datasets[]'):
            if dataset_id in dataset_dict:
                dataset = dataset_dict[dataset_id]
                dataset.load_file(file)
        
        file = SourceFile.objects.get(id=file_id, datasource=ds_id)
        return HttpResponse(json.dumps({
            'success': True, 
            'html': render_to_string('partials/datasources/sourcefile/structure.html', {
                'file': file, 
                'infos': file.infos, 
                'datasets': file.datasets()
            })
        }), mimetype="application/json")


def sourcefiles(request, ds_id, refresh=True):
    from neurolab.db.models import Datasource
    
    try:
        ds = Datasource.objects.with_id(ds_id)
    except Datasource.DoesNotExist:
        raise Http404
    
    if refresh:
        ds.parsetree()
    
    return render_to_response('partials/datasources/sourcefile/list.html',
        {'datasource': ds}
    )


urlpatterns = patterns('',
    secured(r'^new/$', new),
    secured(r'^create/$', create),
    
    secured(r'^(?P<ds_id>[0-9a-f]+)/edit/$', edit),
    secured(r'^(?P<ds_id>[0-9a-f]+)/update/$', update),
    secured(r'^(?P<ds_id>[0-9a-f]+)/delete/$', delete),
    secured(r'^(?P<ds_id>[0-9a-f]+)/files/$', sourcefiles),
    secured(r'^(?P<ds_id>[0-9a-f]+)/files/refresh/$', sourcefiles, {'refresh': True}),
    secured(r'^(?P<ds_id>[0-9a-f]+)/files/(?P<file_id>[0-9a-f]+)/$', sourcefile),
    secured(r'^(?P<ds_id>[0-9a-f]+)/files/(?P<file_id>[0-9a-f]+)/structure/$', sourcefile_structure),
    secured(r'^(?P<ds_id>[0-9a-f]+)/files/(?P<file_id>[0-9a-f]+)/load/$', sourcefile_load),
    
    secured(r'^$', index),
)
