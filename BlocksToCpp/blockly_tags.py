t_block = "block"
t_shadow = "shadow"
t_statement = "statement"
t_value = "value"
t_mutation = "mutation"
t_comment = "comment"
t_field = "field"
t_next = "next"

a_name = "name"
n_else = "ELSE"

tazi_delimitter = '$'
c_delimitter = ";\n"
empty_statement = "{}"

def block_is_type( block, type_name ):
    if( type(type_name) == list):
        return block.tag in type_name
    return block.tag == type_name