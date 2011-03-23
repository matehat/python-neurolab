from django import template
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from neurolab.db.models import SourceFile

register = template.Library()