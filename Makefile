BLOCKLY_PATH = ./Server/*

build:
	make -C GCGF
	make -C InoComposer copy 
	make -C Server copy

default:
	git pull
	sudo cp -R $(BLOCKLY_PATH) /var/www/html

test:
	make -C BlocksToCpp

clean:
	make -C GCGF clean
	make -C Server clean
	make -C InoComposer clean
run:
	make -C Server run
