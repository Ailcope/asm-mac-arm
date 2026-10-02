# asm-mac-arm

Lancer de l'assembleur x86-64 Linux (NASM) sur un Mac ARM (M1, M2, M3…), sans Docker, sans VM, sans toucher au code.

## Le problème (ce que ça règle)

Tu as ce fichier, écrit pour Linux x86-64 :

```nasm
bits 64
section .data
    phrase DB "Tout est bon jusqu'à cette ligne ;)",10

section .text
    global _start

_start:
    mov rax, 1          ; write (Linux)
    mov rdi, 1
    mov rsi, phrase
    mov rdx, 37
    syscall

    mov rax, 60         ; exit (Linux)
    xor rdi, rdi
    syscall
```

Sur un Mac ARM, tu fais `nasm -f elf64 bits64.asm -o bits64.o` puis `ld bits64.o -o bits64`, et c'est la galère :

```
ld: Missing -arch option
ld: -arch arm64      ->  ld: Missing -platform_version option
gcc bits64.o -o bits64
  ld: unknown file type in 'bits64.o'
```

Tu passes en `-f macho64`, et ça empire :

```
ld: warning: ignoring file 'bits64.o': found architecture 'x86_64', required architecture 'arm64'
Undefined symbols for architecture arm64: "_main"

gcc -arch x86_64 bits64.o -o bits64 -Wl,-e,_start -nostdlib
  ld: dynamic executables or dylibs must link with libSystem.dylib
  Illegal text-relocations: text-relocation in '_start'+0x1E to 'phrase'
```

Et même une fois lié, il faudrait réécrire le code : les syscalls Linux (`1`, `60`) ne sont pas ceux de macOS (`0x2000004`, `0x2000001`), et il faut des `rel phrase`. Rosetta ne change rien à ça.

Ici, on ne touche à rien : le `.asm` reste celui du cours.

## Comment ça marche

Le code est assemblé avec NASM en ELF64 (le vrai format Linux), puis chargé en mémoire et exécuté dans un émulateur x86-64 (Unicorn, en Python). Les syscalls Linux sont traduits à la volée. Il n'y a donc plus d'étape `ld` ni `gcc`, celle qui posait problème.

## Installation

Il faut Homebrew. Ensuite :

```
brew install nasm
git clone https://github.com/Ailcope/asm-mac-arm.git
cd asm-mac-arm
make install
```

`make install` crée la commande `macasm` (un lien dans `/opt/homebrew/bin`), utilisable depuis n'importe quel dossier. Au premier lancement, un dossier `.venv` est créé dans le dépôt et `unicorn` y est installé (Python 3 est déjà présent sur macOS, sinon `brew install python`).

## Utilisation

Où que tu sois dans le Mac, tu passes ton `.asm` en argument :

```
cd ~/mes-cours/tp3
macasm exercice2.asm
```

Ça fait le `.o` (dans un dossier temporaire, rien ne traîne chez toi) puis l'exécution. Le fichier doit déclarer `global _start`. Les sous-dossiers et les espaces dans les noms marchent.

Si ça marche, tu vois :

```
[1/2] nasm -f elf64 exercice2.asm -> .o
[2/2] exécution (x86-64 Linux émulé)
Tout est bon jusqu'à cette ligne ;)
```

Autres commandes, depuis le dossier du dépôt :

```
make run                     # lance bits64.asm
make run SRC=tp/exercice2.asm
make uninstall               # retire macasm
make clean                   # supprime .venv
```

Si `/opt/homebrew/bin` n'existe pas ou n'est pas accessible : `make install BIN=~/.local/bin` (et ajoute ce dossier à ton `PATH`).

## Limites

- Seuls les syscalls `read`, `write`, `exit` et `exit_group` sont émulés. Les autres affichent `[syscall N non émulé]` et renvoient une erreur.
- Pas de débogueur pas à pas.
- Code utilisateur uniquement (pas de libc, pas de linkage avec des bibliothèques).

## Licence

CC-BY-NC-4.0, usage non commercial. Voir `LICENSE`.
