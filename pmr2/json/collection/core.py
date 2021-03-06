import json

from pmr2.json.utils import extractRequestObj
from pmr2.json.utils import objToRequest


def generate_hal(links, data=None):
    """
    Generates a HAL representation of the input and return as a dict.

    data must be a dict or None.
    """

    # validation for links could be useful?
    result = {
        '_links': links,
    }

    if data:
        if '_links' in data:
            raise ValueError('data cannot contain _links key')
        result.update(data)
    return result

def template_to_dict(template):
    data = template.get('data', [])
    result = {}
    for d in data:
        if d.get('name') is None:
            continue
        result[d['name']] = d.get('value')
    return result

def generate_collection(version='1.0', href=None, links=None, items=None,
        queries=None, template=None, error=None):
    keys = (
        'version', 'href', 'links', 'items', 'queries', 'template', 'error',)
    kw = locals()
    return {
        'collection': {key: kw[key] for key in keys if kw.get(key) is not None}
    }

def keyvalue_to_itemdata(item_dict):
    """
    Convert a simple item_dict in the key:value format to the collection
    item format.
    """

    return {'data':
        [{
            'name': k,
            'value': v,
        } for k, v in item_dict.iteritems()]
    }

def keyvalue_to_links(item_dict, rel='bookmark'):
    """
    Convert a simple item_dict in the key:links format to the collection
    links format.
    """

    return [{
        'prompt': k,
        'href': v,
        'rel': rel,
    } for k, v in item_dict.iteritems()]

def json_collection_view_init(view):
    view._jc_links = None
    view._jc_items = None
    view._jc_queries = None
    view._jc_template = None
    view._jc_error = None

def json_collection_view_render(view):
    try:
        href = view.context.absolute_url() + '/' + view.__name__
    except TypeError:
        href = view.__name__

    return view.dumps(generate_collection(
        href=href,
        links=view._jc_links,
        items=view._jc_items,
        queries=view._jc_queries,
        template=view._jc_template,
        error=view._jc_error,
    ))

def request_template_to_dict(request):
    obj = extractRequestObj(request)

    if not isinstance(obj, dict):
        # Should probably also check whether the object is a valid
        # collection.
        return {}

    template = obj.get('template', {})
    return template_to_dict(template)

def update_json_collection_form(form):
    form.request.form.update(request_template_to_dict(form.request))

def _append_form_widgets(data, form):
    if not form.widgets:
        return

    for id_, w in form.widgets.items():
        # this is gross.
        if hasattr(form.widgets[id_], 'items'):
            items = form.widgets[id_].items
            if callable(items):
                items = items()

            options = [{
                'text': i['content'],
                'value': i['value'],
            } for i in items]
        else:
            options = None

        data.append({
            'name': form.prefix + form.widgets.prefix + id_,
            'prompt': w.field.title,
            'description': w.field.description,
            'type': type(w.field).__name__,
            'required': w.required,
            'value': w.value,
            'options': options,
        })

def _append_form_actions(data, form):
    if not form.actions:
        return

    for id_, a in form.actions.items():
        data.append({
            # ideal is this, but values are wrong because where this
            # function is used (before form.buttons have been updated).
            # 'name': form.prefix + form.buttons.prefix + id_,
            'name': form.prefix + 'buttons.' + id_,
            'prompt': a.title,
            'description': None,
            'type': type(a.field).__name__,
            'required': a.required,
            'value': None,  # what if button is selected?
        })

def formfields_to_collection_template(form):
    """
    Turn the form fields into a collection template.
    """

    data = []

    _append_form_widgets(data, form)
    _append_form_actions(data, form)

    results = {
        'data': data
    }
    return results

def view_url(context, brain):
    """
    Helper method for views to turn a brain into a proper target URL for
    client consumption.
    """

    siteprop = context.portal_properties.site_properties
    use_view_action = getattr(siteprop,
        'typesUseViewActionInListings', ())
    if brain.portal_type in use_view_action:
        return brain.getURL() + '/view'
    return brain.getURL()
