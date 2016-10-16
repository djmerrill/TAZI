import xml.etree.ElementTree as ET
sequence_node = "sequence_node"
selector_node = "selector_node"
action_node = "action_node"
condition_node = "condition_node"
root_node = "root_node"
star_nodes  = [ sequence_node, selector_node ]
value_nodes = [ action_node, condition_node ]
class BehaviorParser:
    def __init__(self):
        self.count_action = 0
        self.count_sequence = 0
        self.count_selector = 0
        self.count_condition = 0

    def assign_node_name( self, node, node_type):
        name = node_type  
        if node_type == sequence_node: 
            self.count_sequence += 1
            name += str(self.count_sequence)
        if node_type == selector_node: 
            self.count_selector += 1
            name += str(self.count_selector)
        if node_type == action_node: 
            self.count_action += 1
            name += str(self.count_action)
        if node_type == condition_node: 
            self.count_condition += 1
            name += str(self.count_condition)
        return name

    def parse_node( self, node):
        node_type = node.attrib["type"]
        # Determine a unique name for the node
        name = assign_node_name( node, node_type )
        print name
        # If the node is one of these types, then it will have children.
        # Find them and parse them
        if  node_type in [  root_node ] + star_nodes : 
            children = [ c[0] for c in node if len(c) > 0 ] # Indexing at zero takes the block out of its wrapping statement
            print children
            for child in children:
                self.parse_node(child)
