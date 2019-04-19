for a in range(0, 0x100):
  for x in range(0, 0x100):
    print("    ;A=%02X, X=%02X" % (a, x))
    print("    mov a,#0x%02x" % x)
    print("    mov x,a")
    print("    mov a,#0x%02x" % a)
    print("    cmp a,x")
    print("    call print")
    print("    ")
