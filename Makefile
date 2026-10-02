# Assembleur x86-64 Linux sur Mac ARM : nasm (ELF64) + émulation Unicorn.
# Usage : make run            (bits64.asm)
#         make run SRC=tp/autre.asm
# Équivalent : ./asm tp/autre.asm
SRC ?= bits64.asm

.PHONY: run clean

run:
	@./asm "$(SRC)"

clean:
	rm -rf build .venv
