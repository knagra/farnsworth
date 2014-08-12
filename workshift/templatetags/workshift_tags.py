'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def wurl(url_name, *args, **kwargs):
    args = [i for i in args if i]
    kwargs = dict((i, j) for i, j in kwargs.items() if j)
    return reverse(url_name, args=args, kwargs=kwargs)

@register.filter
def currency(dollars):
    dollars = round(float(dollars), 2)
    minus = "-" if dollar < 0 else ""
    return "{0}${1}{2}".format(
        minus,
        intcomma(int(dollars)),
        "{:0.2f}".format(dollars)[-3:],
    )
