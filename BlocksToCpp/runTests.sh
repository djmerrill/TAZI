#!/bin/bash

VARFILES=tests/varTests/*

echo "TEST OUTPUTS: " > parserOutput

#looping over a set of files
for f in $VARFILES
do
	if [ -f $f ]; then
		echo "Processing $f: "
		echo "Testing file: $f" >> parserOutput
		python blocklyTranslator.py -x $f >> parserOutput
		python blocklyTranslator.py -x $f > cCode.c
		if gcc -fsyntax-only cCode.c; then
			echo "PASS"
		else
			echo "FAIL"
		fi 
	else if [ -d $f ]; then
		echo "dafuq, this is a directory. y u do dis."
		fi
	fi
done
