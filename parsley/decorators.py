import re

from django import forms


FIELD_TYPES = [
    (forms.URLField, "url"),
    (forms.EmailField, "email"),
    (forms.IntegerField, "digits"),
    (forms.DecimalField, "number"),
    (forms.FloatField, "number"),
]


FIELD_ATTRS = [
    ("min_length", "minlength"),
    ("max_length", "maxlength"),
    ("min_value", "min"),
    ("max_value", "max"),
]


def update_widget_attrs(field):
    attrs = field.widget.attrs
    if field.required:
        attrs["data-required"] = "true"
    if isinstance(field, forms.RegexField):
        attrs.update({"data-regexp": field.regex.pattern})
        if field.regex.flags & re.IGNORECASE:
            attrs.update({"data-regexp-flag": "i"})
    if isinstance(field, forms.MultiValueField):
        for subfield in field.fields:
            update_widget_attrs(subfield)
    # Set data-* attributes for parsley based on Django field attributes
    for attr, data_attr, in FIELD_ATTRS:
        if getattr(field, attr, None):
            attrs["data-{0}".format(data_attr)] = getattr(field, attr)
    # Set data-type attribute based on Django field instance type
    for klass, field_type in FIELD_TYPES:
        if isinstance(field, klass):
            attrs["data-type"] = field_type


def parsleyfy(klass):
    "A decorator to add data-* attributes to your form.fields"
    old_init = klass.__init__

    def new_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        for _, field in self.fields.items():
            update_widget_attrs(field)
        extras = getattr(getattr(self, 'Meta', None), 'parsley_extras', {})
        for field_name, data in extras.items():
            for key, value in data.items():
                if field_name not in self.fields:
                    continue
                attrs = self.fields[field_name].widget.attrs
                if key == 'equalto':
                    # Use HTML id for data-equalto
                    attrs['data-equalto'] = '#' + self[value].id_for_label
                else:
                    attrs['data-%s' % key] = value
    klass.__init__ = new_init

    try:
        klass.Media.js += ("parsley/js/parsley-standalone.min.js",)
    except AttributeError:
        class Media:
            js = (
                "parsley/js/parsley-standalone.min.js",
            )
        klass.Media = Media

    return klass
