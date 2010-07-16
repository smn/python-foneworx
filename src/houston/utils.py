from xml.etree.ElementTree import Element, fromstring, tostring

class Dispatcher(object):
    
    def __init__(self, prefix="do_"):
        self.prefix = prefix
    
    def dispatch(self, command, *args, **kwargs):
        command_name = '%s%s' % (self.prefix, command.lower())
        if hasattr(self, command_name):
            fn = getattr(self, command_name)
            return fn(*args, **kwargs)
        raise Exception, 'No dispatcher available for %s' % command


def dict_to_xml(dictionary, root=Element("root")):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            root.append(dict_to_xml(value, Element(key)))
        else:
            element = Element(key)
            element.text = value
            root.append(element)
    return root

def xml_to_dict(xml, dictionary=None):
    # if I don't do this, dictionary for some reason will be the 
    # value of the last test run with nosetests. Nightmare
    dictionary = dictionary or {}
    if xml.getchildren():
        for child in xml.getchildren():
            if child.getchildren():
                _, dictionary[child.tag] = xml_to_dict(child, {})
            else:
                dictionary[child.tag] = child.text
    else:
        dictionary[xml.tag] = xml.text
    return xml.tag, dictionary