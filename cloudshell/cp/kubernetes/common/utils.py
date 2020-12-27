import os
import uuid
from datetime import datetime

import yaml


def convert_to_int_list(list_str, separator=','):
    """
    :param str list_str:
    :param str separator:
    :rtype: List[int]
    """
    if not list_str:
        return []
    separated_list = list_str.split(separator)
    trimmed_list = list(map(lambda x: x.strip(), separated_list))
    return list(map(int, trimmed_list))


def convert_app_name_to_valid_kubernetes_name(app_name):
    """
    :param str app_name:
    :rtype: str
    """
    return app_name.lower().replace(' ', '-').replace('_', '-')


def generate_short_unique_string():
    """
    generate a short unique string.
    method generate a guid and return the first 8 characteres of the new guid
    :rtype: str
    """
    unique_id = str(uuid.uuid4())[:8]
    return unique_id


def get_custom_params_value(custom_params_list, key):
    """
    :param List custom_params_list:
    :param str key:
    :rtype: str
    """
    param = next(iter(
        filter(lambda x: x['name'] == key,
               custom_params_list)), None)
    if param:
        return param['value']
    else:
        return None


def dump_context(operation, context, path, obj=True):
    if os.path.exists(path):
        with open(os.path.join(path, "{}-{}.yaml".format(operation, datetime.now().strftime("%Y%m%d-%H%M%S"))),
                  "w+") as ff:
            if obj:
                ff.write(yaml.dump(context, default_flow_style=False))
            else:
                ff.write(context)


def set_value(target, name, value, raise_exeception=False):
    if isinstance(target, (list)):
        target.append(value)
    elif (not try_set_attr(target, name, value) and raise_exeception):
        raise ValueError(target.__class__.__name__ + ' has no property named ' + name)


def convert_to_bool(v):
    if type(v) is bool:
        return v

    return v != None and v.lower() == "true"


def try_set_attr(target, name, value):
    try:
        if (hasattr(target, name)):
            value = convert_to_bool(value) if type(getattr(target, name)) is bool else value
            setattr(target, name, value)
            return True

    except Exception as e:
        pass

    return False


def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def first_letter_to_upper(str):
    return str[:1].upper() + str[1:]


def to_snake_case(str):
    return str.lower().replace(' ', '_')


def first_or_default(predicate, lst, default=None):
    return (list(filter(predicate, lst))+[default])[0]

def single(lst, predicate):
    return list(filter(predicate, lst))[0]


def index_of(lst, predicate):
    gen = (index for index, item in enumerate(lst) if predicate(item))

    try:
        first = next(gen)
    except StopIteration:
        return None

    return first


def convert_attributes_list_to_dict(attributes):
    attributes_map = {}

    # so we shall convert it to attributes map{key : attribute name,value : attribute value }
    for item in attributes:
        attributes_map[item.get('attributeName')] = item.get('attributeValue')

    return attributes_map
