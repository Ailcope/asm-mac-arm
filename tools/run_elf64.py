#!/usr/bin/env python3
"""Exécute un objet NASM ELF64 (Linux x86-64) sur Mac ARM, sans VM ni linker.

Charge le .o en mémoire, applique les relocations, puis émule le code avec
Unicorn en traduisant les syscalls Linux (write, exit, exit_group, read...).
Usage : run_elf64.py fichier.o
"""
import struct
import sys

from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_INSN, UcError
from unicorn.x86_const import *

BASE = 0x400000
STACK_TOP = 0x7FFF0000
STACK_SIZE = 0x100000
PAGE = 0x1000

SHF_ALLOC = 2
SHT_NOBITS = 8


def cstr(blob, off):
    return blob[off:blob.index(b"\0", off)].decode()


def load(path):
    d = open(path, "rb").read()
    if d[:4] != b"\x7fELF" or d[4] != 2:
        sys.exit("Pas un objet ELF64 : assemble avec  nasm -f elf64")
    shoff, = struct.unpack_from("<Q", d, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", d, 0x3A)
    secs = []
    for i in range(shnum):
        n, t, f, a, o, s, link, info, al, es = struct.unpack_from(
            "<IIQQQQIIQQ", d, shoff + i * shentsize)
        secs.append(dict(name=n, type=t, flags=f, off=o, size=s,
                         link=link, info=info, align=al or 1, entsize=es))
    shstr = secs[shstrndx]
    for s in secs:
        s["name"] = cstr(d, shstr["off"] + s["name"])

    # placement des sections ALLOC
    cur = BASE
    for s in secs:
        if s["flags"] & SHF_ALLOC:
            cur = (cur + s["align"] - 1) // s["align"] * s["align"]
            s["addr"] = cur
            cur += s["size"]
    end = (cur + PAGE - 1) // PAGE * PAGE
    mem = bytearray(end - BASE)
    for s in secs:
        if s.get("addr") is not None and s["type"] != SHT_NOBITS:
            mem[s["addr"] - BASE:s["addr"] - BASE + s["size"]] = \
                d[s["off"]:s["off"] + s["size"]]

    # table des symboles
    symtab = next(s for s in secs if s["type"] == 2)
    strtab = secs[symtab["link"]]
    syms = []
    for i in range(symtab["size"] // 24):
        n, info, other, shndx, val, size = struct.unpack_from(
            "<IBBHQQ", d, symtab["off"] + i * 24)
        name = cstr(d, strtab["off"] + n)
        if shndx == 0 or shndx >= 0xFF00:
            addr = val
        else:
            addr = secs[shndx]["addr"] + val
        syms.append((name, addr))

    # relocations
    for s in secs:
        if s["type"] != 4:  # SHT_RELA
            continue
        target = secs[s["info"]]
        if target.get("addr") is None:
            continue
        for i in range(s["size"] // 24):
            off, info, add = struct.unpack_from("<QQq", d, s["off"] + i * 24)
            sym, typ = info >> 32, info & 0xFFFFFFFF
            S = syms[sym][1]
            P = target["addr"] + off
            pos = P - BASE
            if typ == 1:      # R_X86_64_64
                mem[pos:pos + 8] = struct.pack("<Q", (S + add) & (2**64 - 1))
            elif typ in (2, 4):  # PC32 / PLT32
                mem[pos:pos + 4] = struct.pack("<i", S + add - P)
            elif typ == 10:   # 32
                mem[pos:pos + 4] = struct.pack("<I", (S + add) & 0xFFFFFFFF)
            elif typ == 11:   # 32S
                mem[pos:pos + 4] = struct.pack("<i", S + add)
            else:
                sys.exit(f"Relocation ELF type {typ} non gérée")

    entry = dict(syms).get("_start")
    if entry is None:
        sys.exit("Symbole _start introuvable (global _start ?)")
    return bytes(mem), entry


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    mem, entry = load(sys.argv[1])
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    uc.mem_map(BASE, len(mem))
    uc.mem_write(BASE, mem)
    uc.mem_map(STACK_TOP - STACK_SIZE, STACK_SIZE)
    uc.reg_write(UC_X86_REG_RSP, STACK_TOP - 8)

    out = sys.stdout.buffer
    state = {"code": None}

    def on_syscall(uc, _):
        nr = uc.reg_read(UC_X86_REG_RAX)
        a1 = uc.reg_read(UC_X86_REG_RDI)
        a2 = uc.reg_read(UC_X86_REG_RSI)
        a3 = uc.reg_read(UC_X86_REG_RDX)
        ret = -38  # ENOSYS
        if nr == 1:  # write
            data = bytes(uc.mem_read(a2, a3))
            if a1 == 2:
                sys.stderr.buffer.write(data)
                sys.stderr.buffer.flush()
            else:
                out.write(data)
                out.flush()
            ret = a3
        elif nr == 0:  # read
            data = (sys.stdin.buffer.read1(a3) if a1 == 0 else b"")
            uc.mem_write(a2, data)
            ret = len(data)
        elif nr in (60, 231):  # exit, exit_group
            state["code"] = a1 & 0xFF
            uc.emu_stop()
            return
        else:
            print(f"[syscall {nr} non émulé]", file=sys.stderr)
        uc.reg_write(UC_X86_REG_RAX, ret & (2**64 - 1))

    uc.hook_add(UC_HOOK_INSN, on_syscall, None, 1, 0, UC_X86_INS_SYSCALL)
    try:
        uc.emu_start(entry, 0)
    except UcError as e:
        sys.exit(f"Crash émulation : {e} (RIP=0x{uc.reg_read(UC_X86_REG_RIP):x})")
    if state["code"] is None:
        sys.exit("Programme terminé sans syscall exit (il tombe hors du code ?)")
    sys.exit(state["code"])


if __name__ == "__main__":
    main()
