from bs4 import BeautifulSoup
from vdom import VNode

def parse_vdom(soup_node):
    if hasattr(soup_node, 'string') and soup_node.string is not None and not getattr(soup_node, 'name', None):
        return VNode("text", {"content": soup_node.string.strip()}, [])
    if hasattr(soup_node, 'name') and soup_node.name is not None:
        attrs = dict(soup_node.attrs)
        children = []
        for child in soup_node.children:
            child_vdom = parse_vdom(child)
            if child_vdom:
                children.append(child_vdom)
        return VNode(soup_node.name, attrs, children)
    return None