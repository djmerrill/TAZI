import xml.etree.ElementTree as ET

tree = ET.parse("testBlocks.xml")
root = tree.getroot()


# Recursively print the tree, with proper indentation
def recursePrint(node, spaces):
	tag = node.tag.split("}")
	if (len(tag) > 1):
		tag = tag[1]
	else:
		tag = node.tag


	if tag == "block":
		whatToPrint = node.attrib["type"]
	elif tag == "field":
		whatToPrint = node.attrib["name"] + " " +  node.text
	elif tag == "value":
		whatToPrint = node.attrib["name"]
	elif tag == "shadow":
		whatToPrint = node.attrib["type"]
	elif tag == "statement":
		whatToPrint = node.attrib["name"]
	elif tag == "next":
		whatToPrint = "I assume this means just execute next instruction"
	else:
		whatToPrint = ""

	print(spaces + tag + " -- " + whatToPrint)
	if list(node) == []:
		return
	for child in node:
		recursePrint(child, spaces + "  ")
		

# Begin main		
# recursePrint(root, "")


# There should be some degree of error checking
class BlocklyError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self, value):
		return repr(self.value)



# Recurse through the xml to translate
def recurseParse(node):
	tag = node.tag.split("}")
	if (len(tag) > 1):
		tag = tag[1]
	else:
		tag = node.tag

	if tag == "xml":
		overallResult = ""
		for child in node:
			if (child.attrib["type"] == "main_loop" 
				or child.attrib["type"] == "variable_declarations"):
				overallResult += "\n" + recurseParse(child)
		return overallResult

	elif tag == "block":
		return getBlock(node)
	elif tag == "next":
		return "\n" + recurseParse(list(node)[0])
	elif tag == "statement":
		return recurseParseCheck(list(node))
	elif tag == "shadow":
		return getField(list(node)[0])
	else:
		return ""


# Safety net for checking if there is a next block
def recurseParseCheck(nodeList):
	if (len(nodeList) != 1):
		return ""
	else:
		return recurseParse(nodeList[0])


# Sub functions

def getBlock(node):
	blockType = node.attrib["type"]

	if (blockType == "main_loop"):
		# Should be a "next" block
		return "loop()\n{" + recurseParseCheck(list(node)) + "\n}"

	if (blockType == "variable_declarations"):
		return recurseParseCheck(list(node))

	if (blockType == "variables_set"):
		# First child is the field, contains name of the variable
		varName = getField(list(node)[0])
		if (len(list(node)) < 2):
			raise BlocklyError("Field " + varName + " does not have a value!")
			return ""
		varType = getType(list(list(node)[1])[0])
		varValue = getField(list(list(list(node)[1])[0])[0])
		nextBlock = ""
		# Now deal with possible "next" block
		if (len(list(node)) == 3):
			nextBlock = recurseParse(list(node)[2])
		return varType + " " + varName + " = " + varValue + ";" + nextBlock

	if (blockType == "controls_if"):
		# First child is the boolean part
		booleanPart = recurseParse(list(list(node)[0])[0])
		# Second child is the statement part
		statementPart = recurseParse(list(node)[1])
		return "if (" + booleanPart + ")\n{\n" + statementPart + "\n}"

	if (blockType == "logic_compare"):
		# 3 children: operator, value A, value B
		operator = getOp(list(node)[0])
		if (len(list(node)) != 3):
			raise BlocklyError("Logic compare with operator '" + operator + "' requires 2 values to compare!")
			return ""
		valueA = recurseParse(list(list(node)[1])[0])
		valueB = recurseParse(list(list(node)[2])[0])
		return valueA + " " + operator + " " + valueB

	if (blockType == "math_arithmetic"):
		# 3 children: operator, value A, value B
		operator = getOp(list(node)[0])
		if (len(list(node)) != 3):
			raise BlocklyError("Math block with operator '" + operator + "' requires 2 values to compute!")
			return ""
		valueA = recurseParse(list(list(node)[1])[-1])
		valueB = recurseParse(list(list(node)[2])[-1])
		if (operator == "pow"):
			return "pow(" + valueA + ", " + valueB + ")"
		return valueA + " " + operator + " " + valueB

	if (blockType == "math_number"):
		return getField(list(node)[0])

	if (blockType == "variables_get"):
		return getField(list(node)[0])


	# Remainder block types that aren't built in, so it must be custom
	if (len(blockType.split("_")) < 3):
		raise BlocklyError("Block " + blockType + " is malformatted!")
		return ""

	instance = blockType.split("_")[1]
	method = blockType.split("_")[2]

	if (len(list(node)) == 0):
		return instance + "." + method + "();"

	# Iterate through the rest of the children; the last one may be a "next"
	hasNext = 0
	if (list(node)[-1].tag == "next"):
		hasNext = 1

	arguments = ""
	for i in range(len(list(node)) - hasNext):
		arguments += " " + recurseParse(list(node)[i])
	arguments = arguments.strip().replace(" ", ", ")
	if (hasNext == 0):
		return instance + "." + method + "(" + arguments + ");"
	else:
		return instance + "." + method + "(" + arguments + ");" + recurseParse(list(node)[-1])


# Typing dictionary
typeDict = {
	"math_number": "double",
	"text": "string"
}
def getType(node):
	return typeDict[node.attrib["type"]]


def getField(node):
	return node.text

# Operator dictionary
opDict = {
	"EQ": "==",
	"NEQ": "!=",
	"LT": "<",
	"LTE": "<=",
	"GT": ">",
	"GTE": ">=",
	"AND": "&&",
	"OR": "||",
	"PLUS": "+",
	"MINUS": "-",
	"MULTIPLY": "*",
	"DIVIDE": "/",
	"POWER": "pow"
}
def getOp(node):
	return opDict[node.text]


# main
try:
	print(recurseParse(root))
except BlocklyError as e:
	print("Error: " + e.value)
