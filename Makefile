# Assembleur x86-64 Linux sur Mac ARM : nasm (ELF64) + émulation Unicorn.
# Usage : make run            (bits64.asm)
#         make run SRC=tp/autre.asm
#         make install        (commande macasm utilisable partout)
SRC ?= bits64.asm
BIN ?= $(firstword $(wildcard /opt/homebrew/bin /usr/local/bin))

.PHONY: run install uninstall clean

run:
	@./asm "$(SRC)"

install:
	@test -n "$(BIN)" -a -w "$(BIN)" || { echo "Pas de dossier accessible : lance  make install BIN=~/.local/bin  (et ajoute-le au PATH)"; exit 1; }
	ln -sf "$(CURDIR)/asm" "$(BIN)/macasm"
	@echo "OK : macasm fichier.asm  fonctionne maintenant depuis n'importe où"

uninstall:
	rm -f "$(BIN)/macasm"

clean:
	rm -rf build .venv
