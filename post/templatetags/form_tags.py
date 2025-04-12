from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes = css_classes.split(' ')
    else:
        css_classes = []
    
    args = arg.split(' ')
    for a in args:
        if a not in css_classes:
            css_classes.append(a)
    
    return value.as_widget(attrs={'class': ' '.join(css_classes)})