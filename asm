#!/usr/bin/env bash
# Usage : ./asm fichier.asm
# 1) nasm -> build/fichier.o   2) chargement + liaison en mémoire   3) exécution
set -eu
cd "$(dirname "$0")"
SRC="${1:-bits64.asm}"

command -v nasm >/dev/null || { echo "nasm introuvable : brew install nasm" >&2; exit 1; }
[ -f "$SRC" ] || { echo "Fichier introuvable : $SRC" >&2; exit 1; }

if [ ! -x .venv/bin/python ]; then
    echo "[setup] création de .venv et installation de unicorn (une seule fois)"
    python3 -m venv .venv
    .venv/bin/pip install -q unicorn 2>/dev/null
fi

OBJ="build/${SRC%.asm}.o"
mkdir -p "$(dirname "$OBJ")"
echo "[1/2] nasm -f elf64 $SRC -> $OBJ"
nasm -f elf64 "$SRC" -o "$OBJ"
echo "[2/2] exécution (x86-64 Linux émulé)"
exec .venv/bin/python tools/run_elf64.py "$OBJ"
