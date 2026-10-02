# asm-mac-arm

Lancer de l'assembleur x86-64 Linux (NASM) sur un Mac ARM (M1, M2, M3…), sans Docker, sans VM, sans toucher au code.

## Pourquoi

Les cours d'assembleur sont faits pour Linux x86-64 (`_start`, syscalls Linux comme `rax = 1` pour écrire et `rax = 60` pour quitter). Sur un Mac ARM, ça ne se lie pas et ça ne s'exécute pas, d'où les erreurs. Rosetta ne règle pas le problème, car les syscalls macOS n'ont pas les mêmes numéros.

Ici, le code est assemblé avec NASM, puis exécuté dans un émulateur x86-64 (Unicorn, en Python) qui traduit les syscalls Linux. Ton fichier `.asm` reste tel quel.

## Installation

Il faut Homebrew. Ensuite :

```
brew install nasm
git clone https://github.com/Ailcope/asm-mac-arm.git
cd asm-mac-arm
make run
```

Au premier lancement, `make` crée tout seul un dossier `.venv` et y installe `unicorn`. Python 3 est déjà présent sur macOS (sinon `brew install python`).

Si ça marche, tu vois : `Tout est bon jusqu'à cette ligne ;)`

## Utilisation

```
make run                  # lance bits64.asm
make run SRC=autre.asm    # lance un autre fichier
make clean                # supprime build/ et .venv
```

Pour utiliser ton propre code, remplace `bits64.asm` ou passe ton fichier avec `SRC=`. Il doit déclarer `global _start`.

## Limites

- Seuls les syscalls `read`, `write`, `exit` et `exit_group` sont émulés. Les autres affichent `[syscall N non émulé]` et renvoient une erreur.
- Pas de débogueur pas à pas.
- Ça émule du code utilisateur uniquement (pas de libc, pas de linkage avec des bibliothèques).

## Comment ça marche (rapidement)

1. `nasm -f elf64` produit un objet ELF64 Linux dans `build/`.
2. `tools/run_elf64.py` charge cet objet en mémoire, applique les relocations (pour que `mov rsi, phrase` pointe au bon endroit), puis lance l'émulation à `_start`.
3. À chaque instruction `syscall`, le script fait l'équivalent côté Mac (écrire sur la sortie, lire l'entrée, quitter avec le bon code).

## Licence

CC-BY-NC-4.0, usage non commercial. Voir `LICENSE`.
