class VNode:
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = children or []
        self.key = self.attrs.get("id")
    
    def __repr__(self):
        return f"<VNode {self.tag}>"