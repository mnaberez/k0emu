;Print "Hello, World!" out the UART every 100ms

    .area CODE1 (ABS)
    .org 0

pm2 = 0xff22            ;Port mode register 2
rxb0_txs0 = 0xff18      ;Receive buffer register 0 / Transmit shift register 0
asim0 = 0xffa0          ;Asynchronous serial interface mode register 0
brgc0 = 0xffa2          ;Baud rate generator control register 0
if0h = 0xffe1           ;Interrupt request flag register 0H
ims = 0xfff0            ;Memory size switching register
ixs = 0xfff4            ;Internal expansion RAM size switching register
wdtm = 0xfff9           ;Watchdog timer mode register
pcc = 0xfffb            ;Processor clock control register

    nop                 ;These two nops are also the reset vector
    nop

    di                  ;Disable interrupts
    mov pcc,#0          ;Processor clock = full speed
    mov wdtm,#0         ;Watchdog disabled
    mov ixs,#8          ;Expansion RAM size = 2K
    mov ims,#0xcf       ;High speed RAM size = 1K, ROM size = 60K
    movw sp,#0xfe1f     ;Initialize stack pointer
    mov pm2,#0b11011111 ;PM25=output (TxD0), all others input
    mov asim0,#0        ;Disable UART
    mov brgc0,#0x1b     ;Set baud rate to 38400 bps
    mov asim0,#0x8a     ;Enable UART for transmit only and 8-N-1

loop:
    push ax
    pop ax

    movw ax,sp
    movw 0xfe00,ax

    movw ax,0xff1c
    movw 0xfe02,ax


    call greet
    call delay_100ms
    br loop

greet:
;Write "Hello, World" greeting to the UART
    movw hl,#greet_text
greet_nextchar:
    mov a,[hl]
    or a,#0
    bz greet_done
    call uart_put
    incw hl
    br greet_nextchar
greet_done:
    ret
greet_text:
    .ascii "Hello, World!\r\n\0"

uart_put:
;Write a byte to the UART
;Blocks until it has been sent
    mov rxb0_txs0,a
uart_put_wait:
    bf if0h.3, uart_put_wait   ;Wait until IF0H.3=1 (transmit complete)
    clr1 if0h.3                ;Clear transmit complete interrupt flag
    ret

delay_100ms:
;Delay ~100ms
  push ax
  movw ax,#0x6700
delay_loop:
  decw ax
  cmpw ax,#0
  bnz delay_loop
  pop ax
  ret
