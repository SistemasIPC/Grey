from django import template

register = template.Library()

@register.filter
def get_item(diccionario, key):
    return diccionario.get(key)