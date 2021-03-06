#!/usr/bin/env python

from translation_dictionaries import *
from behavior_parser import BehaviorParser

import xml.etree.ElementTree as ET
import argparse

DEBUG = 0
#Can run with arguments for filename input OR requests filename input


spaces = "  "
delimitter = ";"
use_c_lib = True
c_lib = "#include <iostream>\n#include <cmath>"
c_lib += "\n#include <stdlib.h>\nusing namespace std;\n"
   
# Typing dictionary
typeDict = {
    "math_number": "int",
    "text": "string",
    "logic_boolean": "bool"
}

# There should be some degree of error checking
class BlocklyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self, value):
        return repr(self.value)

class BlocklyTranslator:
    def __init__(self):
        self.declaredlVars = []
        self.main_loop = []
        self.definedFuncs = []
        self.declaredObjs = set()
        self.declaredFuncs = []
        self.main_setup = []
        self.main_funcs = ""
        self.behavior_parser = None
        self.switch1 = "";
        self.switch2 = "";
        # User Defined Function Names
        self.madeFuncNames = {}
        self.checkFuncDefs = {}
        self.program_name = "Prog"
        self.isCpp = False
        self.setup_func_dict()
        self.stateCount = 0
        self.index_name_mangling = 0
        self.number_of_delay_objects = 0
        self.declaredVars = []
    def setup_func_dict(self): 
        self.get_func = {
            "variables_set": self.set_variable,
            "controls_if": self.if_block,
            "logic_compare": self.logical_compare,
            "logic_operation": self.logical_compare,
            "math_number_property": self.math_property,
            "math_arithmetic": self.arithmetic_statement,
            "math_single": self.math_single,
            "math_modulo": self.math_modulo,
            "math_random_int": self.random_int,
            "math_random_float": self.random_float,
            "controls_whileUntil": self.while_until,
            "controls_repeat_ext": self.repeat_control,
            "controls_for": self.for_loop,
            "delay": self.delay,
            "delaySeconds": self.delaySeconds,
            "millis": self.millis,
            "logic_negate": self.negate,
            "controls_flow_statements": self.flowcontrols,
            "procedures_defreturn": self.create_function,
            "procedures_defnoreturn": self.create_function,
            "procedures_ifreturn": self.if_return,
            "procedures_callreturn": self.call_method,
            "procedures_callnoreturn": self.call_method
        }
    def refactor_statement_to_block( self, s ):
        s.tag = "block"
        s.attrib["type"] = s.attrib["name"]
        return s
    
    def is_node_of_type( self,node, type_name ):
        atb = (node.attrib).get("type")
        return atb != None and atb == type_name
    
    def parse_state_block(self, child):
        name = child[0].text
        upperName = name.upper()
        isStart = child[1].text
        # Dealing with it if it's a start state
        if (isStart=="TRUE"):
            self.definedFuncs = [("short currState = " + upperName + ";\n")] + self.definedFuncs;
        # Adding the state to the definitions at top
        self.declaredFuncs = ["#define " + upperName + " " + str(self.stateCount) + "\n"] + self.declaredFuncs
        self.stateCount+=1;
        # Adding the method corresponding to the state
        bodyNode = child[2][0]
        bodyStr = self.get_block(bodyNode,1)
        self.declaredFuncs.append("void " + name + "();\n")
        self.definedFuncs.append("void " + name + "() {\n" + bodyStr + ";\n}\n")
        #Adding to the first switch statement (which does the appropriate action for state)
        if(self.switch1==""):
            self.switch1 += (spaces + "switch (currState) {\n")
        self.switch1 += (spaces + "case " + upperName + ": \n" + spaces*2 + name + "();\n" + spaces*2 + "break;\n")

        #Adding to the second switch statement (which handles the transitions)
        if(self.switch2==""):
            self.switch2 += ( spaces + "switch (currState) {\n")	
        self.switch2 += (spaces + "case " + upperName + ": \n")
        tempStr = self.parse_next_block(child,2,"");
        self.switch2 += (tempStr[6:] + "\n" + spaces*2 + "break;\n")
    # Recurse through the xml to translate
    def parse_blocks_recursively(self,node, depth):
        tag = node.tag.split("}")
        tag = tag[1] if (len(tag) > 1) else node.tag
    
        if DEBUG:
            print "Current tag: " + tag, "Attributes: " + str(node.attrib)
    
        isStateCode = False;
        if tag == "xml":
            overallResult = ""
            mainBod = ""
            for child in node.iter('block'):
                if self.is_node_of_type(child, "procedures_defnoreturn") or self.is_node_of_type(child, "procedures_defreturn"):
                    self.find_define(child)
    
            for child in node:
                if self.is_node_of_type(child, "procedures_defnoreturn") or self.is_node_of_type(child, "procedures_defreturn"):
                    self.main_funcs += ";\n" + self.parse_blocks_recursively(child, depth)
    
            for child in node:
                if self.is_node_of_type(child, "main") or self.is_node_of_type(child, "root_node"):
                    overallResult += self.parse_blocks_recursively(child, depth)
                if self.is_node_of_type(child,"state"):
                    isStateCode = True
                    self.parse_state_block(child);
                    self.declaredFuncs.append("void update_state();\n") 
                    self.definedFuncs.append("void update_state(){\n" + self.switch1 + spaces + "}\n\n" + self.switch2 + spaces + "}\n" + "}\n"); 
                    overallResult = "update_state();"		   
        if (isStateCode == True):
            return overallResult
        # Handle the case for Blockly CPP
        c_main = [ ns for ns in node.findall("block") if ns.attrib["type"] == "c_main" ]
        if( len( c_main ) == 1): 
            main = self.refactor_statement_to_block(c_main[0].find("statement"))
            overallResult += self.parse_blocks_recursively(main, 0)
    
            return self.main_funcs + overallResult
    
        elif tag == "block":
            return self.get_block(node,depth)
        elif tag == "next":
            return ";\n" + self.parse_blocks_recursively(list(node)[0], depth)
        elif tag == "statement":
            return self.parse_blocks_recursively(list(node)[0], depth)
        elif tag == "shadow":
            return self.parse_blocks_recursively(list(node)[0], depth)
        elif tag == "value":
            return self.parse_blocks_recursively(list(node)[0], depth)
        elif tag == "field":
            return self.get_field(node)
        else:
            return ""
    
    # Safety net for checking if there is a next block
    #shouldn't the if statement check if it's equal to 0?
    def recurse_parse_check(self,nodeList, depth, remove_white_space=False):
        if (len(nodeList) != 1):
            return ""
        else:
            return self.parse_blocks_recursively(nodeList[0], depth)
    
    # Sub functions
    
    def get_block(self,node,depth):
        blockType = node.attrib["type"]
        if (blockType == "main_loop"):
            # Should be a "next" block
            loopStr = self.recurse_parse_check(list(node), depth+1)+";"
            self.main_loop = loopStr.split("\n")
            return "void loop () {\n" + loopStr + "\n}"
    
        if (blockType == "main_body"):
            mainStr = "int main() {\n " 
            mainStr += self.recurse_parse_check(list(node), depth+1) + ";\n"
            mainStr += spaces + " return 0;\n}"
            self.isCpp = True
            return mainStr
    
        #TODO PQ will move this to its own separate function later lol
        if (blockType == "text_print"):
            nextNode = (node.find("value").find("block"))
            function = depth*spaces + "cout << ("
            #function += recurseParse([nextNode], depth+1, remove_white_space=True)
            function += self.parse_blocks_recursively(nextNode, depth + 1)
            return self.parse_next_block(node, depth, function + ") << endl")
    
        if (blockType == "variable_declarations"):
            setupStr = self.recurse_parse_check(list(node), depth + 1) + ";"
            self.main_setup = setupStr.split("\n")
            return "void setup () {\n" + self.recurse_parse_check(list(node), depth + 1) + ";\n}\n"
    
        if blockType in self.get_func.keys():
            return self.func_check_get(blockType, node, depth) #self.get_func[blockType](node,depth)
    
        if (blockType == "math_number" or blockType == "variables_get"):
            return self.get_field(list(node)[0])
    
        if (blockType == "text"):
            return "\"" + self.get_field(list(node)[0]) + "\""
    
        if (blockType == "math_constant"):
            return self.get_constant(list(node)[0])
    
        if (blockType == "logic_null"):
            return "0"
    
        if (blockType == "logic_boolean"):
            if list(node)[0].text == "TRUE":
                return "true"
            else:
                return "false"
        if (blockType == "main"): 
            lines = ""
            for b in map( self.refactor_statement_to_block, node.findall("statement" )):
                lines += self.parse_blocks_recursively( b, depth ) + delimitter+ '\n'
            return lines
        if blockType == "root_node": 
            parser = ContextAwareParser(self) 
            self.behavior_parser = BehaviorParser(self.program_name, parser) 
            self.behavior_parser.parse_node( node )
            return ""
        if blockType == "transition":
            tempStr = (spaces*depth) + "if("
            tempStr += self.get_block(node[0][0],depth)
            tempStr += ") {\n"
            tempStr += (spaces*(depth+1) + "currState = " + node[1][0][0].text.upper() + ";\n")
            tempStr += (spaces*depth) + "}"
            if self.hasNext(node):
                tempStr += self.parse_blocks_recursively(list(node)[-1], depth);
            return tempStr
        return self.genericBlockGet(node,depth)
       
    def genericBlockGet(self,node,depth):
        blockType = node.attrib["type"]
        # Remainder block types that aren't built in, so it must be custom
        if (len(blockType.split("$")) < 3):
            print blockType
            raise BlocklyError("Block " + blockType + " is malformatted! At depth" + str(depth))
            return ""
    
        object_instance = blockType.split("$")[1]
        self.declaredObjs.add(object_instance)
        method_name = blockType.split("$")[2]
    
        if (len(list(node)) == 0):
            return self.parse_next_block(node, depth, object_instance + "." + method_name + "()")
    
        arguments = self.get_args(node)
    
        block_code_value = object_instance + "." + method_name + "(" + arguments + ")"
        return self.parse_next_block(node, depth, block_code_value)
    
    def parse_next_block(self,node, depth, nodeStr):
        if not self.hasNext(node): return (spaces * depth) + nodeStr
        else: return (spaces * depth) + nodeStr + self.parse_blocks_recursively(list(node)[-1], depth)
    
    #iterate through the children; may have a "next"
    def hasNext(self,node):
        if len(list(node)) == 0:
            return False
        if (list(node)[-1].tag == "next"):
            return True
        return False
    
    def get_args(self,node ):
        arguments = ""
        argList = filter(lambda n: n.tag == "block" or n.tag == "value", (list(node)))
        if len( argList ) == 0:
            argList = filter(lambda n: n.tag == "shadow", (list(node)))
        for i in range(len(argList)):
            curr = argList[i]
            if(arguments != ""):
                arguments += ", "
            if curr.tag == "value": arguments += self.get_value( curr )
            else: arguments += self.parse_blocks_recursively(argList[i], 0)
    
        return arguments
    
    def get_type(self,node):
        if ((node.attrib).get("type") != None and typeDict.get(node.attrib["type"]) != None):
            return typeDict[node.attrib["type"]]
        #else if (node.tag == "block"):
            #
        else:
            #default int
            return "int"
    
    
    def get_field(self,node):
        if (node.attrib.get("name") != None and node.attrib["name"] == "BOOL"):
            if (node.text == "TRUE"):
                return "true"
            if (node.text == "FALSE"):
                return "false"
        return node.text
    
    def get_value(self, val ):
        node = val.find("block")
        if node is None: node = val.find("shadow")
        return self.parse_blocks_recursively( node, 0 )
    
        return opDict[node.text]
    
    
    def get_constant(self,node):
        for k in mathDict.keys():
            if k in self.get_field(node): return mathDict[k] + "(" + self.get_field(node[4:]) + ")"
        return constDict[self.get_field(node)]
    
    # Function Get dictionary
    
    #set variable
    def set_variable(self,node, depth):
        # First child is the field, contains name of the variable
        varName = self.get_field(list(node)[0])
        if (len(list(node)) < 2):
            raise BlocklyError("Field " + varName + " does not have a value!")
            return ""
    
        #if((list(node)[1]).tag.split("}"))
        if varName in self.declaredVars: pass
            # Already declared, we don't need to redo it
        else:
            # Not declared yet, put it in thing
            varType = self.get_type(list(list(node)[1])[0]) + " "
            self.declaredVars.append(varType + varName + ";")
    
        if((list(list(node)[1])[0]).tag == "block"):
            varValue = self.parse_blocks_recursively(list(list(node)[1])[0], 0)
        else:
            varValue = self.get_field(list(list(list(node)[1])[0])[0])
    
        totString = varName + " = " + varValue# + ";"
        return self.parse_next_block(node, depth, totString)
    
    #if statement
    def if_block(self,node, depth):
        numElsIfs = 0
        numElses = 0
        booleanPart = ""
        statementPart = ""
        ifBChild = 0
    
        for child in node:
            if(child.tag == "statement" or child.tag == "value"):
                ifBChild += 1
    
        # First child is either boolean or contains extra piece info
        fchildNode = list(node)[0]
        if (fchildNode.tag == "mutation"):
            if (fchildNode.attrib.get("elseif") != None):
                numElsIfs = int(fchildNode.attrib["elseif"])
            if (fchildNode.attrib.get("else") != None):
                numElses = 1
    
            if (ifBChild < (2*(1 + numElsIfs) + numElses)):
                raise BlocklyError("If-Statement requires a condition and statements!")
    
            booleanPart = self.get_args(list(node)[1])
            statementPart = self.parse_blocks_recursively(list(node)[2], depth+1)
        else:
            if (ifBChild < 2):
                raise BlocklyError("If-Statement requires a condition and statements!")
    
            booleanPart = self.get_args(list(node)[0])
            statementPart = self.parse_blocks_recursively(list(node)[1], depth+1)
    
        # Second child is the statement part
        returnStr = "if(" + booleanPart + ") {\n"
    
        totString = returnStr + statementPart + ";\n" + (spaces*depth) + "}"
    
        if (numElsIfs >= 1):
            totString += self.else_if_block(node, numElsIfs, depth)
    
        if (numElses == 1):
            stmtList = [ s for s in list(node) if s.tag == "statement" ]
            stmt = self.parse_blocks_recursively( stmtList[-1], depth + 1) 
            totString += "\n" + (spaces*depth) + "else {\n" + stmt + ";\n" + (spaces*depth) + "}"
    
        return self.parse_next_block(node, depth, totString)
    
    #else if statements
    def else_if_block(self,node, numTimes, depth):
        elseifOpenString = "\n" + (spaces*depth) + "else if("
        elseString = ""
    
        for i in range(3, 3 + (numTimes * 2)):
            if (((list(node)[i]).attrib["name"])[:2] == "IF"):
                elseString += elseifOpenString
                booleanPart = self.get_args(list(node)[i])
                elseString += booleanPart + ") {\n" + self.parse_blocks_recursively((list(node)[i + 1]), depth + 1) + ";\n" + (spaces*depth) + "}"
    
        return elseString
    
    #else statement
    def elseBlock(self,node, depth):
        elseString = "else {\n" + (spaces*depth) + "}"
    
    #logic compare
    def logical_compare(self,node,depth):
        # 3 children: operator, value A, value B
        operator = getOp(list(node)[0])
        if (len(list(node)) != 3):
            raise BlocklyError("Logic compare with operator '" + operator + "' requires 2 values to compare!")
            return ""
        valueA = self.parse_blocks_recursively(list(list(node)[1])[0],depth)
        valueB = self.parse_blocks_recursively(list(list(node)[2])[0],depth)
    
        return self.parse_next_block(node, depth, (valueA + " " + operator + " " + valueB))
    
    #math property
    def math_property(self,node, depth):
        test = list(node)[1].text
    
        numToCheck = self.parse_blocks_recursively(list(node)[2], 0)
        if (test == "EVEN"): modNum = 0
        else: modNum = 1
        #even, odd, prime, whole, positive, negative, divisible by
    
        total = numToCheck + "%2 == " + str(modNum)
    
        return self.parse_next_block(node, depth, total)
    
    #math arithmetic
    def arithmetic_statement(self,node,depth):
        # 3 children: operator, value A, value B
        operator = getOp(list(node)[0])
        if (len(list(node)) != 3):
            raise BlocklyError("Math block with operator '" + operator + "' requires 2 values to compute!")
            return ""
        #valueA = recurseParse(list(list(node)[1])[-1],depth)
        #valueB = recurseParse(list(list(node)[2])[-1],depth)
    
        valueA = self.parse_blocks_recursively(list(list(node)[1])[-1],depth)
        valueB = self.parse_blocks_recursively(list(list(node)[2])[-1],depth)
    
        if (operator == "pow"):
            return self.parse_next_block(node, depth, ("pow(" + valueA + ", " + valueB + ")"))
        else:
            expr = valueA + " " + operator + " " + valueB
        return self.parse_next_block(node, depth, (valueA + " " + operator + " " + valueB))
    
    #math single
    def math_single(self,node, depth):
        operator = getOp(list(node)[0])
    
        valueOn = self.get_value( node.find("value" ) )
        if operator in ["sqrt", "abs", "-1*", "pow", "log", "log10", "exp"]:
            return self.parse_next_block(node, depth, (operator + "(" + valueOn + ")"))
        if operator == "pow10": 
            return self.parse_next_block(node, depth, ("pow(10," + valueOn + ")"))
    
        return self.parse_next_block(node, depth, (operator + valueOn))
    
    #math modulo
    def math_modulo(self,node, depth):
        values = [ n for n in node if n.tag == "value" ]
        dividend = self.get_value( values[0] )
        divisor = self.get_value( values[1] )
    
        return self.parse_next_block(node, depth, "(int)" + dividend + " % (int)" + divisor)
    
    #math random
    def random_int(self,node, depth):
        minNum = self.parse_blocks_recursively(list(list(node)[0])[0], depth)
        maxNum = self.parse_blocks_recursively(list(list(node)[1])[0], depth)
    
        return "rand() % (" + maxNum + " - " + minNum + ") + " + minNum
    
    #math random float
    def random_float(self,node, depth):
        return "(float) rand() / RAND_MAX"
    
    #while loop
    def while_until(self,node, depth):
        retString = "while("
    
        if (len(list(node)) < 3):
            raise BlocklyError("While-loop requires a condition and statements!")
    
        if (list(node)[0]).text == "UNTIL":
            retString += "!("
    
        if ((list(node)[1]).attrib.get("name") != None and (list(node)[1]).attrib["name"] == "BOOL"):
            condit = self.get_args(list(node)[1])
            retString += condit
    
        if (list(node)[0]).text == "UNTIL":
            retString += ")"
    
        retString += ") {\n"
    
        if (list(node)[2]).attrib.get("name") != None and (list(node)[2]).attrib["name"] == "DO":
            statement = self.parse_blocks_recursively(list(node)[2], depth + 1)
        else:
            statement = "\n";
    
        retString += statement + ";\n" + (spaces*depth) + "}"
    
        return self.parse_next_block(node, depth, retString)
    
    #negate
    def negate(self,node, depth):
        retString = "!("
    
        inner = self.parse_blocks_recursively(list(list(node)[0])[0], 0)
        return self.parse_next_block(node, depth, (retString + inner + ")"))
    
    #repeat for specified num of times
    def repeat_control(self,node, depth):
        idx = "__index_" + str(self.index_name_mangling)
        self.index_name_mangling += 1
        retString = ";\n" + (spaces*depth) + "int __i;\n"
        retString += (spaces*depth) + "for(__i = 0; __i < "
        count = self.parse_blocks_recursively(list(node)[0], 0)
        retString += count + "; __i++) {\n"
    
        statement = self.parse_blocks_recursively(list(node)[1], depth+1)
    
        retString += statement + ";\n" + (spaces*depth) + "}\n"
    
        return self.parse_next_block(node, depth, retString)
    
    #for loop
    def for_loop(self,node, depth):
        #from
        val = self.get_field(list(node)[0])
        values = node.findall("value")
        fromVal = self.get_value( values[0] )
    
        # Moving this here so that val can be declared outside
        retString = (spaces*(depth-1)) + "for(int "
    
        retString += val + " = " + fromVal
    
        #to
        toVal = self.get_value( values[1] )
    
        #increment
        incr = self.get_value( values[2] )
    
        try: cond = "<=" if float(fromVal) <= float(toVal) else ">="
        except: cond = "<="
    
        retString += "; " + val + cond + "("+toVal+"); " + val + "+=(" + incr + ")) {\n"
    
        statement = self.parse_blocks_recursively(list(node)[4], depth+1)
    
        retString += statement + ";\n " + (spaces*depth) + "}"
    
        return self.parse_next_block(node, depth, retString)
    #delay
    def delay(self,node,depth):
        return self._delay(node, depth, "1")
    #delaySeconds
    def delaySeconds(self,node,depth):
        return self._delay(node, depth, "1000")
    def _delay( self, node, depth, k ):
        wait_amt = self.get_delay_amt(node,k)
        retString = "delay(" + wait_amt + ")"
        return self.parse_next_block(node, depth, retString)
    def get_delay_amt( self, node, k ):
        wait_amt = "(int)( " + k + "* ("
        wait_amt += self.get_args(list(node)[0])
        wait_amt += "))"
        return wait_amt
    #millis
    def millis(self,node, depth):
        return self.parse_next_block(node, depth, "millis()")
    
    #controls_flow_statements
    def flowcontrols(self,node, depth):
        flow = getOp(list(node)[0])
        return self.parse_next_block(node, depth, flow)
    
    #Function creation
    def create_function(self,node, depth):
        params = ""
        comment = "/* "
        funcName = ""
        funcBody = ""
        retType = "void"
        funcRet = ""
    
        for child in node:
            if (child.tag == "mutation"):
                for arg in child:
                    if(params != ""):
                        params += ", "
                    params += self.get_type(arg) + " " + (arg.attrib["name"])
            if (child.tag == "comment"):
                comment += child.text + "\n" + (spaces*depth) + "*/\n"
            if (child.tag == "field"):
                funcName = str.replace(child.text, " ", "")
            if (child.tag == "statement"):
                funcBody = self.parse_blocks_recursively(list(child)[0], depth + 1) + ";\n"
            if (child.tag == "value"):
                retType = self.get_type(list(child)[0])
                funcRet = (spaces*(depth + 1)) + "return " + self.parse_blocks_recursively(list(child)[0], 0) + ";;\n"
    
        total = comment + retType + " " + funcName + "(" + params + ") {\n" + funcBody + funcRet + (spaces*depth) + "}\n"
    
        if (self.checkFuncDefs.get(funcName) == None):
            self.definedFuncs += total.split("\n")
            self.declaredFuncs.append(retType + " " + funcName + "(" + params + ");")
            self.checkFuncDefs[funcName] = True
    
        return self.parse_next_block(node, depth, total)
    
    def find_define(self,node):
        paramNum = 0;
        funcName = ""
        for child in node:
            if(child.tag == "mutation"):
                for arg in child:
                    paramNum += 1
            if(child.tag == "field"):
                funcName = str.replace(child.text, " ", "")
    
        self.madeFuncNames[funcName] = paramNum
    
    #call the method with correct arguments as stored by function dictionary
    def call_method(self,node, depth):
        methodName = str.replace((list(node)[0]).attrib["name"], " ", "")
        arguments = ""
        argNums = 0
    
        #check dictionary for params to pull
        call = methodName + "("
    
        #PQ TODO FIX THIS
        if ((self.madeFuncNames[methodName]) > 0):
            for arg in list(node)[0]:
                argNums += 1
    
            for child in node:
                if (child.tag == "value"):
                    if(arguments != ""):
                        arguments += ", "
                    arguments += self.parse_blocks_recursively(child, 0)
            
            call += arguments
    
        return self.parse_next_block(node, depth, call + ")")
    
    #make an if-return for function creation
    def if_return(self,node, depth):
        mainStr = ";\n" + (spaces*depth) + "if("
    
        boolPart = self.get_args(list(node)[1])
        funcRet = (spaces*(depth + 1)) + "return " + self.parse_blocks_recursively(list(list(node)[2])[0], 0) + ";"
    
        mainStr += boolPart + ") {\n" + funcRet + ";\n" + (spaces*depth) + "}\n"
    
        return self.parse_next_block(node, depth, mainStr)
    
    def func_check_get(self,blockType, node, depth):
        if (len(list(node)) > 0 and (list(node)[0]).tag == "next"):
            return self.parse_next_block(node, depth, "")
        
        return self.get_func[blockType](node, depth)
    
    
    def findFuncDefs(self,node):
        for child in node:
            if(child.tag == "field"):
                funcName = str.replace(child.text, " ", "")
    
        if(self.madeFuncNames[funcName] != None):
            return True
        return False

    def run( self,xml ):
        tree = ET.parse(xml)
        root = tree.getroot()
        self.madeFuncNames.clear()
        self.checkFuncDefs.clear()
        try:
            if DEBUG: print("--- RUNNING IN DEBUG MODE ---")
            mainStr = (self.parse_blocks_recursively(root,0)) 
            mainStr = "\n".join( [ a for a in self.get_variables() ] ) + "\n" + mainStr 
            # Jinja would be better
            if use_c_lib: 
                mainStr = c_lib + mainStr 
            return mainStr
        except BlocklyError as e:
            print("Error: " + e.value)
            raise
    
    def get_loop(self): return self.main_loop
    def get_variables(self): return set(self.declaredVars)
    def get_func_defs(self): return self.definedFuncs
    def get_func_decs(self): return self.declaredFuncs
    def get_setup(self): return self.main_setup
    
    def get_split_definitions( self, xml ):
        self.delimitter = "57"
        xml_str = self.run(xml)
        return string.split(xml_str, self.delimitter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--xml", required=False, help="Specify xml file through command line")
    parser.add_argument("-d", action="store_true", help="Debug mode")
    args = parser.parse_args()
    inp = None
    translator = BlocklyTranslator()
    if args.xml is not None:
        inp = args.xml
    else:
        inp = raw_input("Filename: ")
    if args.d: DEBUG = 1
    print translator.run( inp )

class ContextAwareParser(BlocklyTranslator):
    def __init__(self, parent):
        self.parent = parent
        self.declaredVars = parent.declaredVars 
        self.main_loop = parent.main_loop  
        self.definedFuncs = parent.definedFuncs  
        self.declaredObjs = parent.declaredObjs  
        self.declaredFuncs = parent.declaredFuncs 
        self.main_setup = parent.main_setup  
        self.main_funcs = parent.main_funcs  
        # User Defined Function Names
        self.madeFuncNames = parent.madeFuncNames  
        self.checkFuncDefs = parent.checkFuncDefs  
        self.program_name =  parent.program_name 
        self.index_name_mangling = parent.index_name_mangling 
        self.number_of_delay_objects = parent.number_of_delay_objects 
        self.setup_func_dict()
        self.reset_state()
    def reset_state(self):
        self.state = 1
    def _delay(self, node, depth, k):
        #return super(ContextAwareParser, self)._delay(node, depth, k)
        wait_amt = self.get_delay_amt(node,k)
        delay_obj = "delay_" + str(self.number_of_delay_objects)
        self.number_of_delay_objects += 1
        case = str(self.state)
        self.declaredVars.append("DelayTimer " + delay_obj + "(" + wait_amt + ");")
        retString = "case " + case + ":\n" 
        retString += (depth+3)*"\t" + "if ( !" + delay_obj + ".delay() ) return " + case
        self.state += 1
        return self.parse_next_block(node, depth, retString)