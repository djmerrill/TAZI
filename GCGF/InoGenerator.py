__author__ = "Michael Gonzalez"
__email__ = "mmg005@eng.ucsd.edu"

import xml.etree.ElementTree as ETree
import functools
from InoCommenter import *
class Arg:
    def __init__(self, value, name):
        self.value = value
	self.name = name
class CObj:
    countMap = {}
    def __init__(self, objType):
        self.objType = objType
        if objType not in CObj.countMap: CObj.countMap[objType] = 1
        else: CObj.countMap[objType] += 1
	self.name = str.lower(objType) + str(CObj.countMap[objType])
    def setArgs(self, args):
        self.args = args
class ClassGenerator:
    objects = []
    libraries = []
    objInstances = []
    loopBody = []
    name = "" 
    def __init__( self, api):
        self.parseApiGspec(api)
    def getSetupFunction(self):
        def concatLines(acc, line): return acc + "   " + line + ".setup();\n"
	return functools.reduce( concatLines, self.objInstances, "void setup() {\n" ) + "}"
    def getLoopFunction(self):
        def concatLines(acc, line): return acc + "   " + line + "\n"
	return functools.reduce( concatLines, self.loopBody, "void loop() {\n" ) + "}"
    def getLibraries(self):
        def concatLib( acc, elem): return acc + '#include <' + elem + '>\n'
	return functools.reduce( concatLib, set(self.libraries), "" )
    def getConstants(self):
        retStrings = []
	for obj in self.objects:
	    for arg in obj.args:
	        currStr = "#define " + str.upper(obj.name) + "_" + arg.name + " " + str(arg.value)
	        retStrings.append(currStr)
	return retStrings
    def getObjectDeclarations(self):
        retStrings = []
	for obj in self.objects:
	    argC = 0
	    instanceName = str.lower(obj.name)
	    self.objInstances.append(instanceName)
	    currStr = obj.objType + " " + instanceName + "("
	    for arg in obj.args :
		if argC is not 0:
		    currStr = currStr + ", "
	        currStr = currStr + str.upper(obj.name) + "_" + str( arg.name )
		argC = argC + 1
	    currStr = currStr + ");"
	    retStrings.append(currStr)
        return retStrings
    def parseApiGspec(self, root):
        for component in root:
	    if component.tag == "name": self.name = component.text
	    if component.tag != "component":
	        continue
	    for node in component:
	        if node.tag != "api":
		    continue
                currentObj = CObj( node.attrib["class"] )
		if "polls" in node.attrib.keys():
		    self.loopBody.append( currentObj.name + ".poll();" )
	        args = []
		# Handle all the arguments for the object
	        for arg in node.findall("arg"):
	            currentArg = Arg( arg.attrib["digitalliteral"], arg.attrib["arg"] )
		    if currentArg.value == "None": 
		        currentArg.value = arg.attrib["analogliteral"] 
		    args.append( currentArg )
		# Handle all the extra required libraries
		for lib in node.find("required_files").findall("file"):
		    self.libraries.append( lib.attrib["name"] )
	        currentObj.setArgs( args )
	        self.objects.append( currentObj )
	        self.libraries.append( node.attrib["include"])
    def getClass(self):
        rv = createRobotHeader( self.name )
        rv += nl * 2
        rv += a(createSectionHeader("Libraries"))
        rv += a(self.getLibraries())
        rv += a(createSectionHeader("Pin Constants"))
        for string in self.getConstants():
            rv += a(string)
        rv += a(createSectionHeader("Object Declarations"))
        for string in self.getObjectDeclarations():
            rv += a(string)
        rv += a(createSectionHeader("Setup Function", description="The setup() function runs --ONCE-- when the Arduino boots up. As the name implies, it's useful to add code that 'sets up' your Gadget to run correctly."))
        rv += a(self.getSetupFunction())
        rv += a(createSectionHeader("Loop Function", description="The loop() function runs continuously after the setup() function finishes and while the Arduino is running. In other words, this function is called repeatly over and over again when it reaches the end of the function. This function is where the majority of your program's logic should go."  ))
        rv += a(self.getLoopFunction())
	return rv

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser("stuff")
    argparser.add_argument("-g", "--gspec", required=True)
    args = argparser.parse_args()
    api = ETree.parse(args.gspec).getroot()
    generator = ClassGenerator(api)
    print generator.getClass()

    