#!/usr/bin/env bash
# Usage : asm fichier.asm   (ou macasm fichier.asm une fois installé, depuis n'importe où)
# 1) nasm -> .o (dossier temporaire)   2) chargement + liaison en mémoire   3) exécution
set -eu

# Retrouve le vrai dossier du dépôt, même via un lien symbolique (macasm)
SELF="$0"
while [ -L "$SELF" ]; do
    DIR="$(cd "$(dirname "$SELF")" && pwd)"
    SELF="$(readlink "$SELF")"
    case "$SELF" in /*) ;; *) SELF="$DIR/$SELF" ;; esac
done
ROOT="$(cd "$(dirname "$SELF")" && pwd)"

OPT=""
if [ "${1:-}" = "-r" ]; then OPT="--regs"; shift; fi
SRC="${1:-}"
[ -n "$SRC" ] || { echo "Usage : macasm [-r] fichier.asm   (-r : affiche les registres à la fin)" >&2; exit 1; }
command -v nasm >/dev/null || { echo "nasm introuvable : brew install nasm" >&2; exit 1; }
[ -f "$SRC" ] || { echo "Fichier introuvable : $SRC" >&2; exit 1; }

if [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo "[setup] création de .venv et installation de unicorn (une seule fois)" >&2
    python3 -m venv "$ROOT/.venv"
    "$ROOT/.venv/bin/pip" install -q unicorn 2>/dev/null
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
OBJ="$TMP/$(basename "${SRC%.asm}").o"
echo "[1/2] nasm -f elf64 $SRC -> .o" >&2
nasm -f elf64 "$SRC" -o "$OBJ"
echo "[2/2] exécution (x86-64 Linux émulé)" >&2
"$ROOT/.venv/bin/python" "$ROOT/tools/run_elf64.py" $OPT "$OBJ"
