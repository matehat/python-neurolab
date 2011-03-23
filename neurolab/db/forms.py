from django import forms
from neurolab.formats import Format

class DatasourceForm(forms.Form):
    name = forms.CharField(label='Name')
    root = forms.CharField(label='Root Directory')
    
    pathlevels = forms.CharField(required=False, label='File path levels',
        widget=forms.Textarea)
    treelevels = forms.CharField(label='File tree levels',
        widget=forms.Textarea)
        
    fileformat = forms.ChoiceField(label='File format', choices=[
        (format.slug, format.name)
        for format in Format.choices()
    ])

class DatasetForm(forms.Form):
    name = forms.CharField(label='Name')
    root = forms.CharField(label='Root Directory')
    
    blockname = forms.CharField(label='Block Name',
        help_text=  "The block name is used for identifying blocks. " + \
                    "This name, together with the group name, should be unique for each block.")
    groupname = forms.CharField(label='Group Name', 
        help_text="The group name is used to group blocks together under a common name")
