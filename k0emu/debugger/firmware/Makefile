PROJECT=debugger
ROMSIZE=0xf000

all: clean $(PROJECT).bin

$(PROJECT).hex:
	as78k0 -l -o $(PROJECT).asm
	aslink -i $(PROJECT)
	srec_cat $(PROJECT).hex -intel -fill 0xff 0x0000 $(ROMSIZE) -o $(PROJECT).hex.srec_cat -intel -address-length=2 -line-length=76 -crlf
	mv $(PROJECT).hex.srec_cat $(PROJECT).hex
	rm $(PROJECT).hlr $(PROJECT).rel

$(PROJECT).bin: $(PROJECT).hex
	srec_cat $(PROJECT).hex -intel -o $(PROJECT).bin -binary

clean:
	rm -f *.bin *.hex *.hlr *.ihx *.lst *.rel
