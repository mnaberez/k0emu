PROJECT=debugger
ROMSIZE=0xf000

all: clean $(PROJECT).bin

$(PROJECT).hex:
	as78k0 -l -o $(PROJECT).asm
	aslink -i $(PROJECT)
	srec_cat $(PROJECT).ihx -intel -fill 0xff 0x0000 $(ROMSIZE) -o $(PROJECT).hex -intel -address-length=2 -line-length=76 -crlf
	rm $(PROJECT).hlr $(PROJECT).ihx $(PROJECT).rel

$(PROJECT).bin: $(PROJECT).hex
	srec_cat $(PROJECT).hex -intel -o $(PROJECT).bin -binary

clean:
	rm -f *.bin *.hex *.hlr *.ihx *.lst *.rel
