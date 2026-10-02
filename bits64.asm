bits 64
section .data
    phrase DB "Tout est bon jusqu'à cette ligne ;)",10

section .text
    global _start

_start:
    mov rax, 100
    mov rbx, 42
    add rax, rbx

point:
    mov rcx, 0xABCD

    mov rax, 1
    mov rdi, 1
    mov rsi, phrase
    mov rdx, 37
    syscall

sortie:
    mov rax, 60
    xor rdi, rdi
    syscall