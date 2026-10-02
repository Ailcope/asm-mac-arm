# Assembleur x86-64 Linux sur Mac ARM : nasm (ELF64) + émulation Unicorn.
# Usage : make run            (bits64.asm)
#         make run SRC=autre.asm
SRC ?= bits64.asm
OBJ := build/$(SRC:.asm=.o)
VENV := .venv
PY := $(VENV)/bin/python

.PHONY: run build clean

run: build $(PY)
	@$(PY) tools/run_elf64.py $(OBJ)

build: $(OBJ)

build/%.o: %.asm
	@mkdir -p $(dir $@)
	nasm -f elf64 $< -o $@

$(PY):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q unicorn

clean:
	rm -rf build $(VENV)
