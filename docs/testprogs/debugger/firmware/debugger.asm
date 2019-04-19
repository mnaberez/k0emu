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
    mov a,#'>           ;send ">" prompt
    call uart_put

    call uart_get       ;get command byte

    cmp a,#'R           ;handle command
    bz cmd_read
    cmp a,#'W
    bz cmd_write
    cmp a,#'B
    bz cmd_branch

    br loop             ;do it again

;Commands ===================================================================

cmd_read:
;Read a byte from memory
;Reads from UART: 2 bytes for address
;Writes to UART: "r" followed by the byte read
  call uart_get_hl      ;get address to read into HL

  mov a,#'r             ;send "r" = response to read
  call uart_put

  mov a,[hl]            ;read byte from memory
  call uart_put         ;send it
  ret

cmd_write:
;Write a byte to memory
;Reads from UART: 2 bytes for address, 1 byte for value to write
;Writes to UART: "w" only
  call uart_get_hl      ;get address to write into HL

  call uart_get         ;get byte to write to memory
  mov [hl],a            ;write it to memory

  mov a,#'w             ;send "w" = response to write
  call uart_put
  ret

cmd_branch:
;Branch to a routine in memory
;Reads from UART: 2 bytes for address
;Writes to UART: "b" only
  call uart_get_hl      ;get address to branch to into HL

  mov a,#'b             ;send "b" = response to branch
  call uart_put

  movw ax,hl            ;move address to AX
  br ax                 ;branch to it (it must do the RET)

;UART routines ==============================================================

uart_put:
;Write a byte to the UART
;Blocks until it has been sent
    mov rxb0_txs0,a
uart_put_wait:
    bf if0h.3, uart_put_wait   ;Wait until IF0H.3=1 (transmit complete)
    clr1 if0h.3                ;Clear transmit complete interrupt flag
    ret

uart_get:
;Read a byte from the UART, return it in A
;Blocks until one has been received
    ret

uart_get_hl:
;Read two bytes from the UART, return them in HL
;Blocks until they have been received
    call uart_get    ;get address low
    mov l,a
    call uart_get    ;get address high
    mov h,a
    call uart_get    ;get value to write
    ret
