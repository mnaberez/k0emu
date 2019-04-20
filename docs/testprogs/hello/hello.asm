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
    mov a,#'h
    call uart_put
    mov a,#'e
    call uart_put
    mov a,#'l
    call uart_put
    mov a,#'l
    call uart_put
    mov a,#'o
    call uart_put
    mov a,#0x0d
    call uart_put
    mov a,#0x0a
    call uart_put

    br loop

uart_put:
;Write a byte to the UART
;Blocks until it has been sent
    mov rxb0_txs0,a
uart_put_wait:
    bf if0h.3, uart_put_wait   ;Wait until IF0H.3=1 (transmit complete)
    clr1 if0h.3                ;Clear transmit complete interrupt flag
    ret
