import itertools

class Processor(object):
    RESET_VECTOR_ADDRESS = 0x0000
    BRK_VECTOR_ADDRESS = 0x003F
    REGISTERS_BASE_ADDRESS = 0xFEF8
    SP_ADDRESS = 0xFF1C
    PSW_ADDRESS = 0xFF1E
    RESERVED_ADDRESSES = set(range(0xF800, 0xFB00))

    def __init__(self):
        self.memory = Memory(0x10000)
        self._init_opcode_map_unprefixed()
        self._init_opcode_map_prefix_0x31()
        self._init_opcode_map_prefix_0x61()
        self._init_opcode_map_prefix_0x71()
        self.reset()
        self.messages = []
        self.inst_count = 0

    def reset(self):
        self.write_sp(0)
        self.pc = self.read_memory_word(self.RESET_VECTOR_ADDRESS)

    def step(self):
        opcode = self._consume_byte()
        handler = self._opcode_map_unprefixed.get(opcode, self._opcode_not_implemented)
        handler(opcode)
        self.inst_count += 1

    def interrupt(self, isr_address):
        self._push(self.read_psw())
        self.write_psw(self.read_psw() & ~Flags.IE)
        self._push_word(self.pc)
        self.pc = isr_address

    def __str__(self):
        return RegisterTrace.generate(self)

    def _init_opcode_map_unprefixed(self):
        D = {
            0x00: self._opcode_0x00, # nop
            0x01: self._opcode_0x01, # not1 cy
            0x02: self._opcode_0x02, # movw ax,!0abceh             ;02 ce ab       addr16p
            0x03: self._opcode_0x03, # movw !0abceh,ax             ;03 ce ab       addr16p
            0x04: self._opcode_0x04, # dbnz 0fe20h,$label0         ;04 20 fd       saddr
            0x05: self._opcode_0x05, # xch a,[de]                  ;05
            0x07: self._opcode_0x07, # xch a,[hl]                  ;07
            0x08: self._opcode_0x08, # add a,!0abcdh               ;08 cd ab
            0x09: self._opcode_0x09, # add a,[hl+0abh]             ;09 ab
            0x0d: self._opcode_0x0d, # add a,#0abh                 ;0d ab
            0x0e: self._opcode_0x0e, # add a,0fe20h                ;0e 20          saddr
            0x0f: self._opcode_0x0f, # add a,[hl]                  ;0f
            0x11: self._opcode_0x11, # mov 0fe20h,#0abh            ;11 20 ab       saddr
            0x13: self._opcode_0x13, # mov 0fffeh, #0abh           ;13 fe ab       sfr
            0x18: self._opcode_0x18, # sub a,!0abcdh               ;18 cd ab
            0x19: self._opcode_0x19, # sub a,[hl+0abh]             ;19 ab
            0x1d: self._opcode_0x1d, # sub a,#0abh                 ;1d ab
            0x1e: self._opcode_0x1e, # sub a,0fe20h                ;1e 20          saddr
            0x1f: self._opcode_0x1f, # sub a,[hl]                  ;1f
            0x20: self._opcode_0x20, # set1 cy
            0x21: self._opcode_0x21, # clr1 cy
            0x22: self._opcode_0x22, # push psw                    ;22
            0x23: self._opcode_0x23, # pop psw                     ;23
            0x24: self._opcode_0x24, # ror a,1                     ;24
            0x25: self._opcode_0x25, # rorc a,1                    ;25
            0x26: self._opcode_0x26, # rol a,1                     ;26
            0x27: self._opcode_0x27, # rolc a,1                    ;27
            0x28: self._opcode_0x28, # addc a,!0abcdh              ;28 cd ab
            0x29: self._opcode_0x29, # addc a,[hl+0abh]            ;29 ab
            0x2d: self._opcode_0x2d, # addc a,#0abh                ;2d ab
            0x2e: self._opcode_0x2e, # addc a,0fe20h               ;2e 20          saddr
            0x2f: self._opcode_0x2f, # addc a,[hl]                 ;2f
            0x31: self._opcode_0x31,
            0x38: self._opcode_0x38, # subc a,!0abcdh              ;38 cd ab
            0x39: self._opcode_0x39, # subc a,[hl+0abh]            ;39 ab
            0x3d: self._opcode_0x3d, # subc a,#0abh                ;3d ab
            0x3e: self._opcode_0x3e, # subc a,0fe20h               ;3e 20          saddr
            0x3f: self._opcode_0x3f, # subc a,[hl]                 ;3f
            0x48: self._opcode_0x48, # cmp a,!0abcdh               ;48 cd ab
            0x49: self._opcode_0x49, # cmp a,[hl+0abh]             ;49 ab
            0x4d: self._opcode_0x4d, # cmp a,#0abh                 ;4d ab
            0x4e: self._opcode_0x4e, # cmp a,0fe20h                ;4e 20          saddr
            0x4f: self._opcode_0x4f, # cmp a,[hl]                  ;4f
            0x58: self._opcode_0x58, # and a,!0abcdh               ;58 cd ab
            0x59: self._opcode_0x59, # and a,[hl+0abh]             ;59 ab
            0x5d: self._opcode_0x5d, # and a,#0abh                 ;5d ab
            0x5e: self._opcode_0x5e, # and a,0fe20h                ;5e 20          saddr
            0x5f: self._opcode_0x5f, # and a,[hl]                  ;5f
            0x61: self._opcode_0x61,
            0x68: self._opcode_0x68, # or a,!0abcdh                ;68 cd ab
            0x69: self._opcode_0x69, # or a,[hl+0abh]              ;69 ab
            0x6d: self._opcode_0x6d, # or a,#0abh                  ;6d ab
            0x6e: self._opcode_0x6e, # or a,0fe20h                 ;6e 20          saddr
            0x6f: self._opcode_0x6f, # or a,[hl]                   ;6f
            0x71: self._opcode_0x71,
            0x78: self._opcode_0x78, # xor a,!0abcdh               ;78 cd ab
            0x79: self._opcode_0x79, # xor a,[hl+0abh]             ;79 ab
            0x7d: self._opcode_0x7d, # xor a,#0abh                 ;7d ab
            0x7e: self._opcode_0x7e, # xor a,0fe20h                ;7e 20          saddr
            0x7f: self._opcode_0x7f, # xor a,[hl]                  ;7f
            0x81: self._opcode_0x81, # inc 0fe20h                  ;81 20          saddr
            0x83: self._opcode_0x83, # xch a,0fe20h                ;83 20          saddr
            0x85: self._opcode_0x85, # mov a,[de]                  ;85
            0x87: self._opcode_0x87, # mov a,[hl]                  ;87
            0x88: self._opcode_0x88, # add 0fe20h,#0abh            ;88 20 ab       saddr
            0x89: self._opcode_0x89, # movw ax,0fe20h              ;89 20          saddrp
            0x8a: self._opcode_0x8a, # dbnz c,$label1              ;8a fe
            0x8b: self._opcode_0x8b, # dbnz c,$label1              ;8a fe
            0x8d: self._opcode_0x8d, # bc $label3                  ;8d fe
            0x8e: self._opcode_0x8e, # mov a,!addr16               ;8e
            0x8f: self._opcode_0x8f, # reti                        ;8f
            0x91: self._opcode_0x91, # dec 0fe20h                  ;91 20          saddr
            0x93: self._opcode_0x93, # xch a,0fffeh                ;93 fe          sfr
            0x95: self._opcode_0x95, # mov [de],a                  ;95
            0x97: self._opcode_0x97, # mov [hl],a                  ;97
            0x98: self._opcode_0x98, # sub 0fe20h,#0abh            ;98 20 ab       saddr
            0x99: self._opcode_0x99, # movw 0fe20h,ax              ;99 20          saddrp
            0x9a: self._opcode_0x9a, # call !0abcdh                ;9a cd ab
            0x9b: self._opcode_0x9b, # br !0abcdh                  ;9b cd ab
            0x9d: self._opcode_0x9d, # bnc $label3                 ;8d fe
            0x9e: self._opcode_0x9e, # mov !addr16,a               ;9e cd ab
            0x9f: self._opcode_0x9f, # retb                        ;9f
            0xa8: self._opcode_0xa8, # addc 0fe20h,#0abh           ;a8 20 ab       saddr
            0xa9: self._opcode_0xa9, # movw ax,0fffeh              ;a9 fe          sfrp
            0xaa: self._opcode_0xaa, # mov a,[hl+c]                ;aa
            0xab: self._opcode_0xab, # mov a,[hl+b]                ;ab
            0xad: self._opcode_0xad, # bz $label5                  ;ad fe
            0xae: self._opcode_0xae, # mov a,[hl+0abh]             ;ae ab
            0xaf: self._opcode_0xaf, # ret                         ;af
            0xb8: self._opcode_0xb8, # subc 0fe20h,#0abh           ;b8 20 ab       saddr
            0xb9: self._opcode_0xb9, # movw 0fffeh,ax              ;b9 fe          sfrp
            0xba: self._opcode_0xba, # mov [hl+c],a                ;ba
            0xbb: self._opcode_0xbb, # mov [hl+b],a                ;bb
            0xbd: self._opcode_0xbd, # bnz $label5                 ;bd fe
            0xbe: self._opcode_0xbe, # mov [hl+0abh],a             ;be ab
            0xbf: self._opcode_0xbf, # brk                         ;bf
            0xc8: self._opcode_0xc8, # cmp 0fe20h,#0abh            ;c8 20 ab       saddr
            0xca: self._opcode_0xca, # addw ax,#0abcdh             ;ca cd ab
            0xce: self._opcode_0xce, # xch a,!abcd                 ;ce cd ab
            0xd8: self._opcode_0xd8, # and 0fe20h,#0abh            ;d8 20 ab       saddr
            0xda: self._opcode_0xda, # subw ax,#0abcdh             ;da cd ab
            0xde: self._opcode_0xde, # xch a,[hl+0abh]             ;de ab
            0xe8: self._opcode_0xe8, # or 0fe20h,#0abh             ;e8 20 ab
            0xea: self._opcode_0xea, # cmpw ax,#0abcdh             ;ea cd ab
            0xee: self._opcode_0xee, # movw sp,#0abcdh             ;ee 1c cd ab
            0xf0: self._opcode_0xf0, # mov a,0fe20h                ;F0 20          saddr
            0xf2: self._opcode_0xf2, # mov 0fe20h,a                ;f2 20          saddr
            0xf4: self._opcode_0xf4, # mov a,0fffeh                ;f4 fe          sfr
            0xf6: self._opcode_0xf6, # mov 0fffeh,a                ;f6 fe          sfr
            0xf8: self._opcode_0xf8, # xor 0fe20h,#0abh            ;f8 20 ab       saddr
            0xfa: self._opcode_0xfa, # br $label7                  ;fa fe
            0xfe: self._opcode_0xfe, # movw 0fffeh,#0abcdh         ;fe fe cd ab    sfrp
        }

        # xch a,REG                    ;32...37 except 31
        for opcode in (0x30, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            D[opcode] = self._opcode_0x30_to_0x37_except_0x31
        # mov a,x ... mov a,h           ;60..67 except 61
        for opcode in (0x60, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67):
            D[opcode] = self._opcode_0x60_to_0x67_except_0x61
        # inc x ;40 .. inc h ;47
        for opcode in (0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47):
            D[opcode] = self._opcode_0x40_to_0x47_inc
        # dec x ;50 .. dec h ;57
        for opcode in (0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57):
            D[opcode] = self._opcode_0x50_to_0x57_dec
        # mov x,a ... mov h,a           ;70..77 except 71
        for opcode in (0x70, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77):
            D[opcode] = self._opcode_0x70_to_0x77_except_0x71
        for opcode in (0x0c, 0x1c, 0x2c, 0x3c, 0x4c, 0x5c, 0x6c, 0x7c):
            D[opcode] = self._opcode_0x0c_to_0x7c_callf
        # bt 0fe20h.bit,$label8         ;8c 20 fd       saddr
        for opcode in (0x8c, 0x9c, 0xac, 0xbc, 0xcc, 0xdc, 0xec, 0xfc):
            D[opcode] = self._opcode_0x8c_to_0xfc_bt
        # movw ax,#0abcdh             ;10 cd ab
        for opcode in (0x10, 0x12, 0x14, 0x16):
            D[opcode] = self._opcode_0x10_to_0x16_movw
        # xchw ax,bc                  ;e2
        for opcode in (0xe2, 0xe4, 0xe6):
            D[opcode] = self._opcode_0xe2_to_0xe6_xchw
        # push ax                     ;b1
        for opcode in (0xb1, 0xb3, 0xb5, 0xb7):
            D[opcode] = self._opcode_0xb1_to_0xb7_push_rp
        # pop ax                      ;b0
        for opcode in (0xb0, 0xb2, 0xb4, 0xb6):
            D[opcode] = self._opcode_0xb0_to_0xb6_pop_rp
        # incw ax                     ;80
        for opcode in (0x80, 0x82, 0x84, 0x86):
            D[opcode] = self._opcode_0x80_to_0x86_incw
        # decw ax                     ;90
        for opcode in (0x90, 0x92, 0x94, 0x96):
            D[opcode] = self._opcode_0x90_to_0x96_decw
        # movw ax,bc..hl                  ;c2..c6
        for opcode in (0xc2, 0xc4, 0xc6):
            D[opcode] = self._opcode_0xc2_to_0xc6_movw
        # movw bc..hl,ax                  ;d2..d6
        for opcode in (0xd2, 0xd4, 0xd6):
            D[opcode] = self._opcode_0xd2_to_0xd6_movw
        # set1 0fe20h.0               ;0a 20          saddr
        for opcode in (0x0a, 0x1a, 0x2a, 0x3a, 0x4a, 0x5a, 0x6a, 0x7a):
            D[opcode] = self._opcode_0x0a_to_0x7a_set1
        # clr1 0fe20h.0               ;0b 20          saddr
        for opcode in (0x0b, 0x1b, 0x2b, 0x3b, 0x4b, 0x5b, 0x6b, 0x7b):
            D[opcode] = self._opcode_0x0b_to_0x7b_clr
        # mov r,#byte                 ;a0..a7 xx
        for opcode in (0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7):
            D[opcode] = self._opcode_0xa0_to_0xa7
        # callt [0040h] ... callt [007eh]
        for opcode in range(0xc1, 0x100, 2):
            D[opcode] = self._opcode_0xc1_to_0xff_callt
        self._opcode_map_unprefixed = D

    def _init_opcode_map_prefix_0x31(self):
        D = {
            0x0a: self._opcode_0x31_0x0a_add,   # add a,[hl+c]                ;31 0a
            0x0b: self._opcode_0x31_0x0b_add,   # add a,[hl+b]                ;31 0b
            0x1a: self._opcode_0x31_0x1a_sub,   # sub a,[hl+c]                ;31 1a
            0x1b: self._opcode_0x31_0x1b_sub,   # sub a,[hl+b]                ;31 1b
            0x2a: self._opcode_0x31_0x2a_addc,  # addc a,[hl+c]               ;31 2a
            0x2b: self._opcode_0x31_0x2b_addc,  # addc a,[hl+b]               ;31 2b
            0x3a: self._opcode_0x31_0x3a_subc,  # subc a,[hl+c]               ;31 3a
            0x3b: self._opcode_0x31_0x3b_subc,  # subc a,[hl+b]               ;31 3b
            0x4a: self._opcode_0x31_0x4a_cmp,   # cmp a,[hl+c]                ;31 4a
            0x4b: self._opcode_0x31_0x4b_cmp,   # cmp a,[hl+b]                ;31 4b
            0x5a: self._opcode_0x31_0x5a_and,   # and a,[hl+c]                ;31 5a
            0x5b: self._opcode_0x31_0x5b_and,   # and a,[hl+b]                ;31 5b
            0x6a: self._opcode_0x31_0x6a_or,    # or a,[hl+c]                 ;31 6a
            0x6b: self._opcode_0x31_0x6b_or,    # or a,[hl+c]                 ;31 6b
            0x7a: self._opcode_0x31_0x7a_xor,   # xor a,[hl+c]                ;31 7a
            0x7b: self._opcode_0x31_0x7b_xor,   # xor a,[hl+b]                ;31 7b
            0x80: self._opcode_0x31_0x80_rol4,  # rol4 [hl]                   ;31 80
            0x82: self._opcode_0x31_0x82_divuw, # divuw c                     ;31 82
            0x88: self._opcode_0x31_0x88_mulu,  # mulu x                      ;31 88
            0x8a: self._opcode_0x31_0x8a_xch,   # xch a,[hl+c]                ;31 8a
            0x8b: self._opcode_0x31_0x8b_xch,   # xch a,[hl+b]                ;31 8b
            0x90: self._opcode_0x31_0x90_ror4,  # ror4 [hl]                   ;31 90
            0x98: self._opcode_0x31_0x98_br,    # br ax                       ;31 98
        }

        # bt a.bit,$label32             ;31 0e fd
        for opcode2 in (0x0e, 0x1e, 0x2e, 0x3e, 0x4e, 0x5e, 0x6e, 0x7e):
            D[opcode2] = self._opcode_0x31_0x0e_to_0x7e_bt
        # bf a.0,$label64             ;31 0f fd
        for opcode2 in (0x0f, 0x1f, 0x2f, 0x3f, 0x4f, 0x5f, 0x6f, 0x7f):
            D[opcode2] = self._opcode_0x31_0x0f_to_0x7f_bf
        # bf [hl].0,$label80          ;31 87 fd
        for opcode2 in (0x87, 0x97, 0xa7, 0xb7, 0xc7, 0xd7, 0xe7, 0xf7):
            D[opcode2] = self._opcode_0x31_0x87_to_0xf7_bf
        # bf 0fffeh.0,$label56        ;31 07 fe fc    sfr
        for opcode2 in (0x07, 0x17, 0x27, 0x37, 0x47, 0x57, 0x67, 0x77):
            D[opcode2] = self._opcode_0x31_0x07_to_0x77_bf
        # bf 0fe20h.0,$label48        ;31 03 20 fc    saddr
        for opcode2 in (0x03, 0x13, 0x23, 0x33, 0x43, 0x53, 0x63, 0x73):
            D[opcode2] = self._opcode_0x31_0x03_to_0x73_bf
        # btclr a.bit,$label104         ;31 0d fd
        for opcode2 in (0x0d, 0x1d, 0x2d, 0x3d, 0x4d, 0x5d, 0x6d, 0x7d):
            D[opcode2] = self._opcode_0x31_0x0d_to_0x7d_btclr
        # bt 0fffeh.bit,$label24        ;31 06 fe fc    sfr
        for opcode2 in (0x06, 0x16, 0x26, 0x36, 0x46, 0x56, 0x66, 0x76):
            D[opcode2] = self._opcode_0x31_0x06_to_0x76_bt
        # btclr 0fffeh.0,$label96     ;31 05 fe fc    sfr
        for opcode2 in (0x05, 0x15, 0x25, 0x35, 0x45, 0x55, 0x65, 0x75):
            D[opcode2] = self._opcode_0x31_0x05_to_0x75_btclr
        # btclr [hl].0,$label120      ;31 85 fd
        for opcode2 in (0x85, 0x95, 0xa5, 0xb5, 0xc5, 0xd5, 0xe5, 0xf5):
            D[opcode2] = self._opcode_0x31_0x85_to_0xf5_btclr
        # btclr 0fe20h.0,$label88     ;31 01 20 fc    saddr
        for opcode2 in (0x01, 0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71):
            D[opcode2] = self._opcode_0x31_0x01_to_0x71_btclr
        # bt [hl].0,$label40          ;31 86 fd
        for opcode2 in (0x86, 0x96, 0xa6, 0xb6, 0xc6, 0xd6, 0xe6, 0xf6):
            D[opcode2] = self._opcode_0x31_0x86_to_0xf6_bt
        self._opcode_map_prefix_0x31 = D

    def _init_opcode_map_prefix_0x61(self):
        D = {
            0x80: self._opcode_0x61_0x80_adjba,     # adjba                       ;61 80
            0x90: self._opcode_0x61_0x90_adjbs,     # adjbs                       ;61 90
        }
        # sel rbn
        for opcode2 in (0xD0, 0xD8, 0xF0, 0xF8):
            D[opcode2] = self._opcode_0x61_0xd0_to_0xf8_sel_rb
        # or a,reg (except: or a,reg=a)
        for opcode2 in (0x68, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f):
            D[opcode2] = self._opcode_0x61_0x68_to_0x6f_or
        # or reg,a
        for opcode2 in (0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67):
            D[opcode2] = self._opcode_0x61_0x61_to_0x67_or
        # cmp reg,a                     ;61 40..47
        for opcode2 in (0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47):
            D[opcode2] = self._opcode_0x61_0x40_to_0x47_cmp
        # cmp a,reg (except cmp a, reg=a)
        for opcode2 in (0x48, 0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x4f):
            D[opcode2] = self._opcode_0x61_48_to_4f_cmp
        # and reg,a
        for opcode2 in (0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57):
            D[opcode2] = self._opcode_0x61_0x50_to_0x57_and
        # and a,reg (except: and a,reg=a)
        for opcode2 in (0x58, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f):
            D[opcode2] = self._opcode_0x61_0x58_to_0x5f_and
        # xor a,reg (except: xor a,reg=a)
        for opcode2 in (0x78, 0x7a, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f):
            D[opcode2] = self._opcode_0x61_0x78_to_0x7f_xor
        # xor reg,a
        for opcode2 in (0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77):
            D[opcode2] = self._opcode_0x61_0x70_to_0x77_xor
        # set1 a.bit
        for opcode2 in (0x8a, 0x9a, 0xaa, 0xba, 0xca, 0xda, 0xea, 0xfa):
            D[opcode2] = self._opcode_0x61_0x8a_to_0xfa_set1
        # clr1 a.bit
        for opcode2 in (0x8b, 0x9b, 0xab, 0xbb, 0xcb, 0xdb, 0xeb, 0xfb):
            D[opcode2] = self._opcode_0x61_0x8b_to_0xfb_clr1
        # mov1 cy,a.bit
        for opcode2 in (0x8c, 0x9c, 0xac, 0xbc, 0xcc, 0xdc, 0xec, 0xfc):
            D[opcode2] = self._opcode_0x61_0x8c_to_0xfc_mov1
        # mov1 a.bit,cy                 ;61 89
        for opcode2 in (0x89, 0x99, 0xa9, 0xb9, 0xc9, 0xd9, 0xe9, 0xf9):
            D[opcode2] = self._opcode_0x61_0x89_to_0xf9_mov1
        # and1 cy,a.0                 ;61 8d
        for opcode2 in (0x8d, 0x9d, 0xad, 0xbd, 0xcd, 0xdd, 0xed, 0xfd):
            D[opcode2] = self._opcode_0x61_0x8d_to_0xfd_and1
        # or1 cy,a.0                  ;61 8e
        for opcode2 in (0x8e, 0x9e, 0xae, 0xbe, 0xce, 0xde, 0xee, 0xfe):
            D[opcode2] = self._opcode_0x61_0x8e_to_0xfe_or1
        # xor1 cy,a.0                 ;61 8f
        for opcode2 in (0x8f, 0x9f, 0xaf, 0xbf, 0xcf, 0xdf, 0xef, 0xff):
            D[opcode2] = self._opcode_0x61_0x8f_to_0xff_xor1
        # add a,x                     ;61 08
        for opcode2 in (0x08, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f):
            D[opcode2] = self._opcode_0x61_0x08_to_0x0f_add
        # addc a,x                    ;61 28
        for opcode2 in (0x28, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f):
            D[opcode2] = self._opcode_0x61_0x28_to_0x2f_addc
        # add x,a                     ;61 00
        for opcode2 in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07):
            D[opcode2] = self._opcode_0x61_0x00_to_0x07_add
        # addc x,a                    ;61 20
        for opcode2 in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27):
            D[opcode2] = self._opcode_0x61_0x20_to_0x27_addc
        # sub a,reg                   ;61 18..1f except 11
        for opcode in (0x18, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f):
            D[opcode] = self._opcode_0x61_0x18_to_0x1f_except_0x11
        # sub reg,a                   ;61 10..17
        for opcode in (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17):
            D[opcode] = self._opcode_0x61_0x10_to_0x17_sub
        # subc a,reg (except: subc a,reg=a) ;61 38..3f
        for opcode in (0x38, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f):
            D[opcode] = self._opcode_0x61_0x38_to_0x3f_subc
        # subc reg,a                  ;61 30..37
        for opcode in (0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            D[opcode] = self._opcode_0x61_0x30_to_0x37_subc
        self._opcode_map_prefix_0x61 = D

    def _init_opcode_map_prefix_0x71(self):
        D = {}

        # set1 sfr.bit
        for opcode2 in (0x0a, 0x1a, 0x2a, 0x3a, 0x4a, 0x5a, 0x6a, 0x7a):
            D[opcode2] = self._opcode_0x71_0x0a_to_0x7a_set1
        # set1 [hl].bit
        for opcode2 in (0x82, 0x92, 0xa2, 0xb2, 0xc2, 0xd2, 0xe2, 0xf2):
            D[opcode2] = self._opcode_0x71_0x82_to_0xf2_set1
        # clr1 sfr.bit
        for opcode2 in (0x0b, 0x1b, 0x2b, 0x3b, 0x4b, 0x5b, 0x6b, 0x7b):
            D[opcode2] = self._opcode_0x71_0x0b_to_0x7b_clr1
        # clr1 [hl].bit
        for opcode2 in (0x83, 0x93, 0xa3, 0xb3, 0xc3, 0xd3, 0xe3, 0xf3):
            D[opcode2] = self._opcode2_0x71_0x83_to_0xf3_clr1
        # mov1 0fe20h.bit,cy            ;71 01 20       saddr
        for opcode2 in (0x01, 0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71):
            D[opcode2] = self._opcode_0x71_0x01_to_0x71_mov1
        # mov1 cy,0fffeh.bit            ;71 0c fe       sfr
        for opcode2 in (0x0c, 0x1c, 0x2c, 0x3c, 0x4c, 0x5c, 0x6c, 0x7c):
            D[opcode2] = self._opcode_0x71_0x0c_to_0x7c_mov1
        # mov1 0fffeh.bit,cy            ;71 09 fe       sfr
        for opcode2 in (0x09, 0x19, 0x29, 0x39, 0x49, 0x59, 0x69, 0x79):
            D[opcode2] = self._opcode_0x71_0x09_to_0x79_mov1
        # mov1 cy,0fe20h.bit            ;71 04 20       saddr
        for opcode2 in (0x04, 0x14, 0x24, 0x34, 0x44, 0x54, 0x64, 0x74):
            D[opcode2] = self._opcode_0x71_0x04_to_0x74_mov1
        # mov1 cy,[hl].bit              ;71 84
        for opcode2 in (0x84, 0x94, 0xa4, 0xb4, 0xc4, 0xd4, 0xe4, 0xf4):
            D[opcode2] = self._opcode_0x71_0x84_to_0xf4_mov1
        # mov1 [hl].bit,cy              ;71 81
        for opcode2 in (0x81, 0x91, 0xa1, 0xb1, 0xc1, 0xd1, 0xe1, 0xf1):
            D[opcode2] = self._opcode_0x71_0x81_to_0xf1_mov1
        # and1 cy,[hl].0              ;71 85
        for opcode2 in (0x85, 0x95, 0xa5, 0xb5, 0xc5, 0xd5, 0xe5, 0xf5):
            D[opcode2] = self._opcode_0x71_0x85_to_0xf5_and1
        # and1 cy,0fffeh.0            ;71 0d fe       sfr
        for opcode2 in (0x0d, 0x1d, 0x2d, 0x3d, 0x4d, 0x5d, 0x6d, 0x7d):
            D[opcode2] = self._opcode_0x71_0x0d_to_0x7d_and1
        # and1 cy,0fe20h.0            ;71 05 20       saddr
        for opcode2 in (0x05, 0x15, 0x25, 0x35, 0x45, 0x55, 0x65, 0x75):
            D[opcode2] = self._opcode_0x71_0x05_to_0x75_and1
        # or1 cy,0fffeh.0             ;71 0e fe       sfr
        for opcode2 in (0x0e, 0x1e, 0x2e, 0x3e, 0x4e, 0x5e, 0x6e, 0x7e):
            D[opcode2] = self._opcode_0x71_0x0e_to_0x7e_or1
        # or1 cy,[hl].0               ;71 86
        for opcode2 in (0x86, 0x96, 0xa6, 0xb6, 0xc6, 0xd6, 0xe6, 0xf6):
            D[opcode2] = self._opcode_0x71_0x86_to_0xf6_or1
        # or1 cy,0fe20h.0             ;71 06 20       saddr
        for opcode2 in (0x06, 0x16, 0x26, 0x36, 0x46, 0x56, 0x66, 0x76):
            D[opcode2] = self._opcode_0x71_0x06_to_0x76_or1
        # xor1 cy,[hl].0              ;71 87
        for opcode2 in (0x87, 0x97, 0xa7, 0xb7, 0xc7, 0xd7, 0xe7, 0xf7):
            D[opcode2] = self._opcode_0x71_0x87_to_0xf7_xor1
        # xor1 cy,0fffeh.0            ;71 0f fe       sfr
        for opcode2 in (0x0f, 0x1f, 0x2f, 0x3f, 0x4f, 0x5f, 0x6f, 0x7f):
            D[opcode2] = self._opcode_0x71_0x0f_to_0x7f
        # xor1 cy,0fe20h.0            ;71 07 20       saddr
        for opcode2 in (0x07, 0x17, 0x27, 0x37, 0x47, 0x57, 0x67, 0x77):
            D[opcode2] = self._opcode_0x71_0x07_to_0x77_xor1
        self._opcode_map_prefix_0x71 = D

    # not implemented
    def _opcode_not_implemented(self, opcode):
        raise NotImplementedError()

    # prefix 0x31
    def _opcode_0x31(self, opcode):
        opcode2 = self._consume_byte()
        handler = self._opcode_map_prefix_0x31.get(opcode2, self._opcode_not_implemented)
        handler(opcode2)

    # prefix 0x61
    def _opcode_0x61(self, opcode):
        opcode2 = self._consume_byte()
        handler = self._opcode_map_prefix_0x61.get(opcode2, self._opcode_not_implemented)
        handler(opcode2)

    # prefix 0x71
    def _opcode_0x71(self, opcode):
        opcode2 = self._consume_byte()
        handler = self._opcode_map_prefix_0x71.get(opcode2, self._opcode_not_implemented)
        handler(opcode2)

    # nop
    def _opcode_0x00(self, opcode):
        return

    # not1 cy
    def _opcode_0x01(self, opcode):
        bitweight = Flags.CY
        carry = self.read_psw() & bitweight
        if carry:
            self.write_psw(self.read_psw() & ~bitweight)
        else:
            self.write_psw(self.read_psw() | bitweight)

    # xch a,[de]                  ;05
    def _opcode_0x05(self, opcode):
        a_value = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.DE)
        other_value = self.read_memory(address)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # xch a,[hl]                  ;07
    def _opcode_0x07(self, opcode):
        a_value = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        other_value = self.read_memory(address)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # add a,!0abcdh               ;08 cd ab
    def _opcode_0x08(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # add a,[hl+0abh]             ;09 ab
    def _opcode_0x09(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # add a,#0abh                 ;0d ab
    def _opcode_0x0d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # add a,0fe20h                ;0e 20          saddr
    def _opcode_0x0e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # add a,[hl]                  ;0f
    def _opcode_0x0f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # movw regpair,#0abcdh             ;10..16 cd ab
    def _opcode_0x10_to_0x16_movw(self, opcode):
        regpair = _regpair(opcode)
        value = self._consume_word()
        self.write_gp_regpair(regpair, value)

    # xchw ax,bc                  ;e2
    # xchw ax,de                  ;e4
    # xchw ax,hl                  ;e6
    def _opcode_0xe2_to_0xe6_xchw(self, opcode):
        ax_value = self.read_gp_regpair(RegisterPairs.AX)
        other_regpair = _regpair(opcode)
        other_value = self.read_gp_regpair(other_regpair)
        self.write_gp_regpair(RegisterPairs.AX, other_value)
        self.write_gp_regpair(other_regpair, ax_value)

    # sub a,!0abcdh               ;18 cd ab
    def _opcode_0x18(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,[hl+0abh]             ;19 ab
    def _opcode_0x19(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,#0abh                 ;1d ab
    def _opcode_0x1d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,0fe20h                ;1e 20          saddr
    def _opcode_0x1e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,[hl]                  ;1f
    def _opcode_0x1f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # set1 cy
    def _opcode_0x20(self, opcode):
        bitweight = Flags.CY
        self.write_psw(self.read_psw() | bitweight)

    # clr1 cy
    def _opcode_0x21(self, opcode):
        bitweight = Flags.CY
        self.write_psw(self.read_psw() & ~bitweight)

    # push psw                    ;22
    def _opcode_0x22(self, opcode):
        self._push(self.read_psw())

    # pop psw                     ;23
    def _opcode_0x23(self, opcode):
        self.write_psw(self._pop())

    # ror a,1                     ;24
    def _opcode_0x24(self, opcode):
        value = self.read_gp_reg(Registers.A)
        original_bit_0 = value & 1
        rotated = value >> 1

        psw = self.read_psw()

        if original_bit_0:
            rotated |= 0x80
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # rorc a,1                    ;25
    def _opcode_0x25(self, opcode):
        value = self.read_gp_reg(Registers.A)
        original_bit_0 = value & 1
        rotated = value >> 1

        psw = self.read_psw()

        if psw & Flags.CY:
            rotated |= 0x80

        if original_bit_0:
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # rol a,1                     ;26
    def _opcode_0x26(self, opcode):
        rotated = self.read_gp_reg(Registers.A) << 1
        psw = self.read_psw()

        if rotated & 0x100:
            rotated |= 1
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # rolc a,1                    ;27
    def _opcode_0x27(self, opcode):
        rotated = self.read_gp_reg(Registers.A) << 1
        psw = self.read_psw()

        if psw & Flags.CY:
             rotated |= 1

        if rotated & 0x100:
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # addc a,!0abcdh              ;28 cd ab
    def _opcode_0x28(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,[hl+0abh]            ;29 ab
    def _opcode_0x29(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,#0abh                ;2d ab
    def _opcode_0x2d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,0fe20h               ;2e 20          saddr
    def _opcode_0x2e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,[hl]                 ;2f
    def _opcode_0x2f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,!0abcdh              ;38 cd ab
    def _opcode_0x38(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,[hl+0abh]            ;39 ab
    def _opcode_0x39(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,#0abh                ;3d ab
    def _opcode_0x3d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,0fe20h               ;3e 20          saddr
    def _opcode_0x3e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,[hl]                 ;3f
    def _opcode_0x3f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # xch a,REG                    ;32...37 except 31
    def _opcode_0x30_to_0x37_except_0x31(self, opcode):
        other_reg = _reg(opcode)
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.read_gp_reg(other_reg)
        self.write_gp_reg(Registers.A, other_value)
        self.write_gp_reg(other_reg, a_value)

    # cmp 0fe20h,#0abh            ;c8 20 ab       saddr
    def _opcode_0xc8(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        self._operation_sub(a, b)

    # addw ax,#0abcdh             ;ca cd ab
    def _opcode_0xca(self, opcode):
        ax_value = self.read_gp_regpair(RegisterPairs.AX)
        other_value = self._consume_word()
        result = self._operation_addw(ax_value, other_value)
        self.write_gp_regpair(RegisterPairs.AX, result)

    # subw ax,#0abcdh             ;da cd ab
    def _opcode_0xda(self, opcode):
        ax_value = self.read_gp_regpair(RegisterPairs.AX)
        other_value = self._consume_word()
        result = self._operation_subw(ax_value, other_value)
        self.write_gp_regpair(RegisterPairs.AX, result)

    # cmpw ax,#0abcdh             ;ea cd ab
    def _opcode_0xea(self, opcode):
        ax_value = self.read_gp_regpair(RegisterPairs.AX)
        other_value = self._consume_word()
        self._operation_subw(ax_value, other_value)

    # xch a,!abcd                 ;ce cd ab
    def _opcode_0xce(self, opcode):
        address = self._consume_addr16()
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.read_memory(address)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # xch a,0fe20h                ;83 20          saddr
    def _opcode_0x83(self, opcode):
        address = self._consume_saddr()
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.read_memory(address)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # xch a,0fffeh                ;93 fe          sfr
    def _opcode_0x93(self, opcode):
        address = self._consume_sfr()
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.read_memory(address)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # incw ax                     ;80
    # ...
    # incw hl                     ;86
    def _opcode_0x80_to_0x86_incw(self, opcode):
        regpair = _regpair(opcode)
        value = self.read_gp_regpair(regpair)
        result = self._operation_incw(value)
        self.write_gp_regpair(regpair, result)

    # decw ax                     ;90
    # ...
    # decw hl                     ;96
    def _opcode_0x90_to_0x96_decw(self, opcode):
        regpair = _regpair(opcode)
        value = self.read_gp_regpair(regpair)
        result = self._operation_decw(value)
        self.write_gp_regpair(regpair, result)

    # movw ax,!0abceh             ;02 ce ab       addr16p
    def _opcode_0x02(self, opcode):
        address = self._consume_addr16p()
        value_low = self.read_memory(address)
        self.write_gp_reg(Registers.X, value_low)
        value_high = self.read_memory(address+1)
        self.write_gp_reg(Registers.A, value_high)

    # movw ax,0fe20h              ;89 20          saddrp
    def _opcode_0x89(self, opcode):
        address = self._consume_saddrp()
        value_low = self.read_memory(address)
        self.write_gp_reg(Registers.X, value_low)
        value_high = self.read_memory(address+1)
        self.write_gp_reg(Registers.A, value_high)

    # sub 0fe20h,#0abh            ;98 20 ab       saddr
    def _opcode_0x98(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_sub(a, b)
        self.write_memory(address, result)

    # movw 0fe20h,ax              ;99 20          saddrp
    def _opcode_0x99(self, opcode):
        address = self._consume_saddrp()
        value_low = self.read_gp_reg(Registers.X)
        self.write_memory(address, value_low)
        value_high = self.read_gp_reg(Registers.A)
        self.write_memory(address+1, value_high)

    # movw !0abceh,ax             ;03 ce ab       addr16p
    def _opcode_0x03(self, opcode):
        address = self._consume_addr16p()
        value_low = self.read_gp_reg(Registers.X)
        self.write_memory(address, value_low)
        value_high = self.read_gp_reg(Registers.A)
        self.write_memory(address+1, value_high)

    # subc 0fe20h,#0abh           ;b8 20 ab       saddr
    def _opcode_0xb8(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_subc(a, b)
        self.write_memory(address, result)

    # movw 0fffeh,ax              ;b9 fe          sfrp
    def _opcode_0xb9(self, opcode):
        address = self._consume_sfrp()
        value_low = self.read_gp_reg(Registers.X)
        self.write_memory(address, value_low)
        value_high = self.read_gp_reg(Registers.A)
        self.write_memory(address+1, value_high)

    # br !0abcdh                  ;9b cd ab
    def _opcode_0x9b(self, opcode):
        address = self._consume_addr16()
        self.pc = address

    # mov r,#byte                 ;a0..a7 xx
    def _opcode_0xa0_to_0xa7(self, opcode):
        reg = _reg(opcode)
        immbyte = self._consume_byte()
        self.write_gp_reg(reg, immbyte)

    # mov a,x ... mov a,h           ;60..67 except 61
    def _opcode_0x60_to_0x67_except_0x61(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(reg)
        self.write_gp_reg(Registers.A, value)

    # mov x,a ... mov h,a           ;70..77 except 71
    def _opcode_0x70_to_0x77_except_0x71(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(Registers.A)
        self.write_gp_reg(reg, value)

    # mov a,!addr16                 ;8e
    def _opcode_0x8e(self, opcode):
        address = self._consume_addr16()
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # mov !addr16,a               ;9e cd ab
    def _opcode_0x9e(self, opcode):
        address = self._consume_addr16()
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # mov a,0fe20h                ;F0 20          saddr
    # mov a,psw                   ;f0 1e          (psw=saddr ff1e)
    def _opcode_0xf0(self, opcode):
        address = self._consume_saddr()
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # mov 0fe20h,a                ;f2 20          saddr
    # mov psw,a                   ;f2 1e          (psw=saddr ff1e)
    def _opcode_0xf2(self, opcode):
        address = self._consume_saddr()
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # mov a,0fffeh                ;f4 fe          sfr
    def _opcode_0xf4(self, opcode):
        address = self._consume_sfr()
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)
        self.write_memory(address, value)

    # mov 0fffeh,a                ;f6 fe          sfr
    def _opcode_0xf6(self, opcode):
        address = self._consume_sfr()
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # mov 0fe20h,#0abh            ;11 20 ab       saddr
    # mov psw,#0abh               ;11 1e ab
    def _opcode_0x11(self, opcode):
        address = self._consume_saddr()
        value = self._consume_byte()
        self.write_memory(address, value)

    # mov 0fffeh, #0abh           ;13 fe ab       sfr
    def _opcode_0x13(self, opcode):
        address = self._consume_sfr()
        value = self._consume_byte()
        self.write_memory(address, value)

    # add a,[hl+b]                ;31 0b
    def _opcode_0x31_0x0b_add(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_b()
        b = self.read_memory(address)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,[hl+c]                ;31 1a
    def _opcode_0x31_0x1a_sub(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_c()
        b = self.read_memory(address)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,[hl+b]                ;31 1b
    def _opcode_0x31_0x1b_sub(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_b()
        b = self.read_memory(address)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,[hl+b]               ;31 2b
    def _opcode_0x31_0x2b_addc(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_b()
        b = self.read_memory(address)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,[hl+c]               ;31 3a
    def _opcode_0x31_0x3a_subc(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_c()
        b = self.read_memory(address)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # subc a,[hl+b]               ;31 3b
    def _opcode_0x31_0x3b_subc(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_b()
        b = self.read_memory(address)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # cmp a,[hl+c]                ;31 4a
    def _opcode_0x31_0x4a_cmp(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_c()
        b = self.read_memory(address)
        self._operation_sub(a, b)

    # cmp a,[hl+b]                ;31 4b
    def _opcode_0x31_0x4b_cmp(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_b()
        b = self.read_memory(address)
        self._operation_sub(a, b)

    # add a,[hl+c]                ;31 0a
    def _opcode_0x31_0x0a_add(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_c()
        b = self.read_memory(address)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,[hl+c]               ;31 2a
    def _opcode_0x31_0x2a_addc(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        address = self._based_hl_c()
        b = self.read_memory(address)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # bt a.bit,$label32             ;31 0e fd
    def _opcode_0x31_0x0e_to_0x7e_bt(self, opcode2):
        bit = _bit(opcode2)
        displacement = self._consume_byte()
        value = self.read_gp_reg(Registers.A)
        self._operation_bt(value, bit, displacement)

    # bf a.0,$label64             ;31 0f fd
    def _opcode_0x31_0x0f_to_0x7f_bf(self, opcode2):
        bit = _bit(opcode2)
        displacement = self._consume_byte()
        value = self.read_gp_reg(Registers.A)
        self._operation_bf(value, bit, displacement)

    # bf [hl].0,$label80          ;31 87 fd
    def _opcode_0x31_0x87_to_0xf7_bf(self, opcode2):
        bit = _bit(opcode2)
        displacement = self._consume_byte()
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.read_memory(address)
        self._operation_bf(value, bit, displacement)

    # bf 0fffeh.0,$label56        ;31 07 fe fc    sfr
    def _opcode_0x31_0x07_to_0x77_bf(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        displacement = self._consume_byte()
        value = self.read_memory(address)
        self._operation_bf(value, bit, displacement)

    # bf psw.0,$label72           ;31 03 1e fc
    def _opcode_0x31_0x03_to_0x73_bf(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        displacement = self._consume_byte()
        value = self.read_memory(address)
        self._operation_bf(value, bit, displacement)

    # btclr a.0,$label104         ;31 0d fd
    def _opcode_0x31_0x0d_to_0x7d_btclr(self, opcode2):
        bit = _bit(opcode2)
        displacement = self._consume_byte()
        value = self.read_gp_reg(Registers.A)
        result = self._operation_btclr(value, bit, displacement)
        self.write_gp_reg(Registers.A, result)

    # bt 0fffeh.0,$label24        ;31 06 fe fc    sfr
    def _opcode_0x31_0x06_to_0x76_bt(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        displacement = self._consume_byte()
        value = self.read_memory(address)
        self._operation_bt(value, bit, displacement)

    # btclr [hl].0,$label120      ;31 85 fd
    def _opcode_0x31_0x05_to_0x75_btclr(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        displacement = self._consume_byte()
        value = self.read_memory(address)
        result = self._operation_btclr(value, bit, displacement)
        self.write_memory(address, result)

    # btclr [hl].0,$label120      ;31 85 fd
    def _opcode_0x31_0x85_to_0xf5_btclr(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        displacement = self._consume_byte()
        value = self.read_memory(address)
        result = self._operation_btclr(value, bit, displacement)
        self.write_memory(address, result)

    # btclr 0fe20h.0,$label88     ;31 01 20 fc    saddr
    def _opcode_0x31_0x01_to_0x71_btclr(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        displacement = self._consume_byte()
        value = self.read_memory(address)
        result = self._operation_btclr(value, bit, displacement)
        self.write_memory(address, result)

    # bt [hl].0,$label40          ;31 86 fd
    def _opcode_0x31_0x86_to_0xf6_bt(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        displacement = self._consume_byte()
        value = self.read_memory(address)
        self._operation_bt(value, bit, displacement)

    # and a,[hl+c]                ;31 5a
    def _opcode_0x31_0x5a_and(self, opcode2):
        address = self._based_hl_c()
        b = self.read_memory(address)
        a = self.read_gp_reg(Registers.A)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,[hl+b]                ;31 5b
    def _opcode_0x31_0x5b_and(self, opcode2):
        address = self._based_hl_b()
        b = self.read_memory(address)
        a = self.read_gp_reg(Registers.A)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,[hl+c]                 ;31 6a
    def _opcode_0x31_0x6a_or(self, opcode2):
        address = self._based_hl_c()
        b = self.read_memory(address)
        a = self.read_gp_reg(Registers.A)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,[hl+b]                 ;31 6b
    def _opcode_0x31_0x6b_or(self, opcode2):
        address = self._based_hl_b()
        b = self.read_memory(address)
        a = self.read_gp_reg(Registers.A)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor a,[hl+c]                ;31 7a
    def _opcode_0x31_0x7a_xor(self, opcode2):
        address = self._based_hl_c()
        b = self.read_memory(address)
        a = self.read_gp_reg(Registers.A)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor a,[hl+b]                ;31 7b
    def _opcode_0x31_0x7b_xor(self, opcode2):
        address = self._based_hl_b()
        b = self.read_memory(address)
        a = self.read_gp_reg(Registers.A)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # rol4 [hl]                   ;31 80
    def _opcode_0x31_0x80_rol4(self, opcode2):
        address = self.read_gp_regpair(RegisterPairs.HL)
        if (address & 0xff00) == 0xff00:
            raise Exception("ROL4 does not allow SFR area for operand [HL]")

        a = self.read_gp_reg(Registers.A)
        a_low_nib = a & 0x0f
        a_high_nib = a >> 4

        dest = self.read_memory(address)
        dest_low_nib = dest & 0x0f
        dest_high_nib = dest >> 4

        a = (a_high_nib << 4) | dest_high_nib
        self.write_gp_reg(Registers.A, a)

        dest = (dest_low_nib << 4) | a_low_nib
        self.write_memory(address, dest)

    # ror4 [hl]                   ;31 90
    def _opcode_0x31_0x90_ror4(self, opcode2):
        address = self.read_gp_regpair(RegisterPairs.HL)
        if (address & 0xff00) == 0xff00:
            raise Exception("ROR4 does not allow SFR area for operand [HL]")

        a = self.read_gp_reg(Registers.A)
        a_low_nib = a & 0x0f
        a_high_nib = a >> 4

        dest = self.read_memory(address)
        dest_low_nib = dest & 0x0f
        dest_high_nib = dest >> 4

        a = (a_high_nib << 4) | dest_low_nib
        self.write_gp_reg(Registers.A, a)

        dest = (a_low_nib << 4) | dest_high_nib
        self.write_memory(address, dest)

    # divuw c                     ;31 82
    def _opcode_0x31_0x82_divuw(self, opcode2):
        ax = self.read_gp_regpair(RegisterPairs.AX)
        c = self.read_gp_reg(Registers.C)
        if c == 0:
            quotient = 0xffff
            remainder = ax & 0xff
        else:
            quotient = ax // c
            remainder = ax % c
        self.write_gp_regpair(RegisterPairs.AX, quotient)
        self.write_gp_reg(Registers.C, remainder)

    # mulu x                      ;31 88
    def _opcode_0x31_0x88_mulu(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        x = self.read_gp_reg(Registers.X)
        product = a * x
        self.write_gp_regpair(RegisterPairs.AX, product)

    # xch a,[hl+c]                ;31 8a
    def _opcode_0x31_0x8a_xch(self, opcode2):
        address = self._based_hl_c()
        other_value = self.read_memory(address)
        a_value = self.read_gp_reg(Registers.A)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # xch a,[hl+b]                ;31 8b
    def _opcode_0x31_0x8b_xch(self, opcode2):
        address = self._based_hl_b()
        other_value = self.read_memory(address)
        a_value = self.read_gp_reg(Registers.A)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # br ax                       ;31 98
    def _opcode_0x31_0x98_br(self, opcode2):
        self.pc = self.read_gp_regpair(RegisterPairs.AX)

    # cmp a,!0abcdh               ;48 cd ab
    def _opcode_0x48(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        self._operation_sub(a, b)

    # cmp a,[hl+0abh]             ;49 ab
    def _opcode_0x49(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        self._operation_sub(a, b)

    # cmp a,#0abh                 ;4d ab
    def _opcode_0x4d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        self._operation_sub(a, b)

    # cmp a,0fe20h                ;4e 20          saddr
    def _opcode_0x4e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        self._operation_sub(a, b)

    # cmp a,[hl]                  ;4f
    def _opcode_0x4f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        self._operation_sub(a, b)

    # adjba                       ;61 80
    def _opcode_0x61_0x80_adjba(self, opcode2):
        psw = self.read_psw()
        cy = int(bool(psw & Flags.CY))
        ac = int(bool(psw & Flags.AC))

        a = self.read_gp_reg(Registers.A)
        a_low_nib = a & 0x0f
        a_high_nib = a >> 4

        if ac == 0:
            if a_low_nib <= 9:
                if (a_high_nib <= 9) and (cy == 0):
                    a = a
                    cy = 0
                    ac = 0
                if (a_high_nib >= 10) or (cy == 1):
                    a = (a + 0b01100000) & 0xff
                    cy = 1
                    ac = 0
            else:
                if (a_high_nib < 9) and (cy == 0):
                    a = (a + 0b00000110) & 0xff
                    cy = 0
                    ac = 1
                if (a_high_nib >= 9) or (cy == 1):
                    a = (a + 0b01100110) & 0xff
                    cy = 1
                    ac = 1
        else:
            if (a_high_nib <= 9) and (cy == 0):
                a = (a + 0b00000110) & 0xff
                cy = 0
                ac = 0
            if (a_high_nib >= 10) or (cy == 1):
                a = (a + 0b01100110) & 0xff
                cy = 1
                ac = 0

        psw &= ~(Flags.AC | Flags.CY | Flags.Z)
        if cy:
            psw |= Flags.CY
        if ac:
            psw |= Flags.AC
        if a == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        self.write_gp_reg(Registers.A, a)

    # adjbs                       ;61 90
    def _opcode_0x61_0x90_adjbs(self, opcode2):
        psw = self.read_psw()
        cy = int(bool(psw & Flags.CY))
        ac = int(bool(psw & Flags.AC))

        a = self.read_gp_reg(Registers.A)

        if ac == 0:
            if cy == 0:
                a = a
                cy = 0
                ac = 0
            else:
                a = (a - 0b01100000) & 0xff
                cy = 1
                ac = 0
        else:
            if cy == 0:
                a = (a - 0b00000110) & 0xff
                cy = 0
                ac = 0
            else:
                a = (a - 0b01100110) & 0xff
                cy = 1
                ac = 0

        psw &= ~(Flags.AC | Flags.CY | Flags.Z)
        if cy:
            psw |= Flags.CY
        if ac:
            psw |= Flags.AC
        if a == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        self.write_gp_reg(Registers.A, a)

    # sel rb0                     ;61 d0
    def _opcode_0x61_0xd0_to_0xf8_sel_rb(self, opcode2):
        banks_by_opcode2 = {0xD0: 0, 0xD8: 1, 0xF0: 2, 0xF8: 3}
        self.write_rb(banks_by_opcode2[opcode2])

    # or a,x                      ;61 68
    def _opcode_0x61_0x68_to_0x6f_or(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,a                      ;61 61
    def _opcode_0x61_0x61_to_0x67_or(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        result = self._operation_or(a, b)
        self.write_gp_reg(reg, result)

    # and a,x                     ;61 58
    def _opcode_0x61_0x58_to_0x5f_and(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # cmp reg,a                   ;61 40..47
    def _opcode_0x61_0x40_to_0x47_cmp(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(reg)
        b = self.read_gp_reg(Registers.A)
        self._operation_sub(a, b)

    # cmp a,reg                   ;61 48..4f
    def _opcode_0x61_48_to_4f_cmp(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        self._operation_sub(a, b)

    # and x,a                     ;61 50
    def _opcode_0x61_0x50_to_0x57_and(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        result = self._operation_and(a, b)
        self.write_gp_reg(reg, result)

    # xor a,x                     ;61 78
    def _opcode_0x61_0x78_to_0x7f_xor(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor x,a                     ;61 70
    def _opcode_0x61_0x70_to_0x77_xor(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        reg = _reg(opcode2)
        b = self.read_gp_reg(reg)
        result = self._operation_xor(a, b)
        self.write_gp_reg(reg, result)

    # set1 a.0                    ;61 8a
    def _opcode_0x61_0x8a_to_0xfa_set1(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        bit = _bit(opcode2)
        result = self._operation_set1(a, bit)
        self.write_gp_reg(Registers.A, result)

    # clr1 a.0                    ;61 8b
    def _opcode_0x61_0x8b_to_0xfb_clr1(self, opcode2):
        a = self.read_gp_reg(Registers.A)
        bit = _bit(opcode2)
        result = self._operation_clr1(a, bit)
        self.write_gp_reg(Registers.A, result)

    # mov1 cy,a.0                 ;61 8c
    def _opcode_0x61_0x8c_to_0xfc_mov1(self, opcode2):
        bit = _bit(opcode2)
        src = self.read_gp_reg(Registers.A)
        dest = self.read_psw()
        result = self._operation_mov1(src, bit, dest, 0)
        self.write_psw(result)

    # mov1 a.0,cy                 ;61 89
    def _opcode_0x61_0x89_to_0xf9_mov1(self, opcode2):
        bit = _bit(opcode2)
        src = self.read_psw()
        dest = self.read_gp_reg(Registers.A)
        result = self._operation_mov1(src, 0, dest, bit)
        self.write_gp_reg(Registers.A, result)

    # and1 cy,a.0                 ;61 8d
    def _opcode_0x61_0x8d_to_0xfd_and1(self, opcode2):
        bit = _bit(opcode2)
        src = self.read_gp_reg(Registers.A)
        dest = self.read_psw()
        result = self._operation_and1(src, bit, dest, 0)
        self.write_psw(result)

    # or1 cy,a.0                  ;61 8e
    def _opcode_0x61_0x8e_to_0xfe_or1(self, opcode2):
        bit = _bit(opcode2)
        src = self.read_gp_reg(Registers.A)
        dest = self.read_psw()
        result = self._operation_or1(src, bit, dest, 0)
        self.write_psw(result)

    # xor1 cy,a.0                 ;61 8f
    def _opcode_0x61_0x8f_to_0xff_xor1(self, opcode2):
        bit = _bit(opcode2)
        src = self.read_gp_reg(Registers.A)
        dest = self.read_psw()
        result = self._operation_xor1(src, bit, dest, 0)
        self.write_psw(result)

    # add a,x                     ;61 08
    def _opcode_0x61_0x08_to_0x0f_add(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(Registers.A)
        b = self.read_gp_reg(reg)
        result = self._operation_add(a, b)
        self.write_gp_reg(Registers.A, result)

    # addc a,x                    ;61 28
    def _opcode_0x61_0x28_to_0x2f_addc(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(Registers.A)
        b = self.read_gp_reg(reg)
        result = self._operation_addc(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub reg,a                   ;61 10..17
    def _opcode_0x61_0x10_to_0x17_sub(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(reg)
        b = self.read_gp_reg(Registers.A)
        result = self._operation_sub(a, b)
        self.write_gp_reg(reg, result)

    # subc reg,a                  ;61 30..37
    def _opcode_0x61_0x30_to_0x37_subc(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(reg)
        b = self.read_gp_reg(Registers.A)
        result = self._operation_subc(a, b)
        self.write_gp_reg(reg, result)

    # subc a,reg                  ;61 38..3f
    def _opcode_0x61_0x38_to_0x3f_subc(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(Registers.A)
        b = self.read_gp_reg(reg)
        result = self._operation_subc(a, b)
        self.write_gp_reg(Registers.A, result)

    # sub a,reg                   ;61 18..1f
    def _opcode_0x61_0x18_to_0x1f_except_0x11(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(Registers.A)
        b = self.read_gp_reg(reg)
        result = self._operation_sub(a, b)
        self.write_gp_reg(Registers.A, result)

    # add x,a                     ;61 00
    def _opcode_0x61_0x00_to_0x07_add(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(Registers.A)
        b = self.read_gp_reg(reg)
        result = self._operation_add(a, b)
        self.write_gp_reg(reg, result)

    # addc x,a                    ;61 20
    def _opcode_0x61_0x20_to_0x27_addc(self, opcode2):
        reg = _reg(opcode2)
        a = self.read_gp_reg(Registers.A)
        b = self.read_gp_reg(reg)
        result = self._operation_addc(a, b)
        self.write_gp_reg(reg, result)

    # set1 [hl].0                 ;71 82
    def _opcode_0x71_0x82_to_0xf2_set1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.read_memory(address)
        result = self._operation_set1(value, bit)
        self.write_memory(address, result)

    # clr1 0fffeh.0               ;71 0b fe       sfr
    def _opcode_0x71_0x0b_to_0x7b_clr1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        value = self.read_memory(address)
        result = self._operation_clr1(value, bit)
        self.write_memory(address, result)

    # set1 0fffeh.0               ;71 0a fe       sfr
    def _opcode_0x71_0x0a_to_0x7a_set1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        value = self.read_memory(address)
        result = self._operation_set1(value, bit)
        self.write_memory(address, result)

    # clr1 [hl].0                 ;71 83
    def _opcode2_0x71_0x83_to_0xf3_clr1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.read_memory(address)
        result = self._operation_clr1(value, bit)
        self.write_memory(address, result)

    # mov1 cy,0fffeh.0            ;71 0c fe       sfr
    def _opcode_0x71_0x0c_to_0x7c_mov1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        src = self.read_memory(address)
        dest = self.read_gp_reg(Registers.A)
        result = self._operation_mov1(src, bit, dest, 0)
        self.write_psw(result)

    # mov1 0fffeh.0,cy            ;71 09 fe       sfr
    def _opcode_0x71_0x09_to_0x79_mov1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        src = self.read_psw()
        dest = self.read_memory(address)
        result = self._operation_mov1(src, 0, dest, bit)
        self.write_memory(address, result)

    # mov1 0fe20h.0,cy            ;71 01 20       saddr
    def _opcode_0x71_0x01_to_0x71_mov1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        src = self.read_psw()
        dest = self.read_memory(address)
        result = self._operation_mov1(src, 0, dest, bit)
        self.write_memory(address, result)

    # mov1 cy,0fe20h.0            ;71 04 20       saddr
    def _opcode_0x71_0x04_to_0x74_mov1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_mov1(src, bit, dest, 0)
        self.write_psw(result)

    # mov1 cy,[hl].0              ;71 84
    def _opcode_0x71_0x84_to_0xf4_mov1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_mov1(src, bit, dest, 0)
        self.write_psw(result)

    # mov1 [hl].0,cy              ;71 81
    def _opcode_0x71_0x81_to_0xf1_mov1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        src = self.read_psw()
        dest = self.read_memory(address)
        result = self._operation_mov1(src, 0, dest, bit)
        self.write_memory(address, result)

    # and1 cy,[hl].0              ;71 85
    def _opcode_0x71_0x85_to_0xf5_and1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_and1(src, bit, dest, 0)
        self.write_psw(result)

    # and1 cy,0fffeh.0            ;71 0d fe       sfr
    def _opcode_0x71_0x0d_to_0x7d_and1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_and1(src, bit, dest, 0)
        self.write_psw(result)

    # and1 cy,0fe20h.0            ;71 05 20       saddr
    def _opcode_0x71_0x05_to_0x75_and1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_and1(src, bit, dest, 0)
        self.write_psw(result)

    # or1 cy,0fffeh.0             ;71 0e fe       sfr
    def _opcode_0x71_0x0e_to_0x7e_or1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_or1(src, bit, dest, 0)
        self.write_psw(result)

    # or1 cy,[hl].0               ;71 86
    def _opcode_0x71_0x86_to_0xf6_or1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_or1(src, bit, dest, 0)
        self.write_psw(result)

    # or1 cy,0fe20h.0             ;71 06 20       saddr
    def _opcode_0x71_0x06_to_0x76_or1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_or1(src, bit, dest, 0)
        self.write_psw(result)

    # xor1 cy,[hl].0              ;71 87
    def _opcode_0x71_0x87_to_0xf7_xor1(self, opcode2):
        bit = _bit(opcode2)
        address = self.read_gp_regpair(RegisterPairs.HL)
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_xor1(src, bit, dest, 0)
        self.write_psw(result)

    # xor1 cy,0fffeh.0            ;71 0f fe       sfr
    def _opcode_0x71_0x0f_to_0x7f(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_sfr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_xor1(src, bit, dest, 0)
        self.write_psw(result)

    # xor1 cy,0fe20h.0            ;71 07 20       saddr
    def _opcode_0x71_0x07_to_0x77_xor1(self, opcode2):
        bit = _bit(opcode2)
        address = self._consume_saddr()
        src = self.read_memory(address)
        dest = self.read_psw()
        result = self._operation_xor1(src, bit, dest, 0)
        self.write_psw(result)

    # or a,[hl+0abh]              ;69 ab
    def _opcode_0x69(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,#0abh                  ;6d ab
    def _opcode_0x6d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,0fe20h                 ;6e 20          saddr
    def _opcode_0x6e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,[hl]                   ;6f
    def _opcode_0x6f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # bt 0fe20h.bit,$label8         ;8c 20 fd       saddr
    def _opcode_0x8c_to_0xfc_bt(self, opcode):
        bit = _bit(opcode)
        address = self._consume_saddr()
        displacement = self._consume_byte()
        value = self.read_memory(address)
        self._operation_bt(value, bit, displacement)

    # or 0fe20h,#0abh             ;e8 20 ab      saddr
    def _opcode_0xe8(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_or(a, b)
        self.write_memory(address, result)

    # or a,!0abcdh                ;68 cd ab
    def _opcode_0x68(self, opcode):
        address = self._consume_addr16()
        a = self.read_gp_reg(Registers.A)
        b = self.read_memory(address)
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,[hl+0abh]             ;59 ab
    def _opcode_0x59(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,#0abh                 ;5d ab
    def _opcode_0x5d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,0fe20h                ;5e 20          saddr
    def _opcode_0x5e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,[hl]                  ;5f
    def _opcode_0x5f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,!0abcdh               ;58 cd ab
    def _opcode_0x58(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and 0fe20h,#0abh            ;d8 20 ab       saddr
    def _opcode_0xd8(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_and(a, b)
        self.write_memory(address, result)

    # xor a,!0abcdh               ;78 cd ab
    def _opcode_0x78(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.read_memory(address)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor a,[hl+0abh]             ;79 ab
    def _opcode_0x79(self, opcode):
        a = self.read_gp_reg(Registers.A)
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        b = self.read_memory(address)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor 0fe20h,#0abh            ;f8 20 ab       saddr
    def _opcode_0xf8(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_xor(a, b)
        self.write_memory(address, result)

    # xor a,#0abh                 ;7d ab
    def _opcode_0x7d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor a,0fe20h                ;7e 20          saddr
    def _opcode_0x7e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.read_memory(address)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor a,[hl]                  ;7f
    def _opcode_0x7f(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_memory(address)
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # mov a,[de]                  ;85
    def _opcode_0x85(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.DE)
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # mov [de],a                  ;95
    def _opcode_0x95(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.DE)
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # mov a,[hl]                  ;87
    def _opcode_0x87(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # add 0fe20h,#0abh            ;88 20 ab       saddr
    def _opcode_0x88(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_add(a, b)
        self.write_memory(address, result)

    # addc 0fe20h,#0abh           ;a8 20 ab       saddr
    def _opcode_0xa8(self, opcode):
        address = self._consume_saddr()
        a = self.read_memory(address)
        b = self._consume_byte()
        result = self._operation_addc(a, b)
        self.write_memory(address, result)

    # mov [hl],a                  ;97
    def _opcode_0x97(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # call !0abcdh                ;9a cd ab
    def _opcode_0x9a(self, opcode):
        address = self._consume_addr16()
        self._push_word(self.pc)
        self.pc = address

    # SET1 0fe20h.7               ;7A 20          saddr
    # SET1 PSW.7                  ;7A 1E          (psw=saddr ff1e)
    # EI                          ;7A 1E          alias for SET1 PSW.7
    def _opcode_0x0a_to_0x7a_set1(self, opcode):
        bit = _bit(opcode)
        address = self._consume_saddr()
        value = self.read_memory(address)
        result = self._operation_set1(value, bit)
        self.write_memory(address, result)

    # clr1 0fe20h.0               ;0b 20          saddr
    # clr1 psw.0                  ;0b 1e
    # di                          ;7b 1e          alias for clr1 psw.7
    def _opcode_0x0b_to_0x7b_clr(self, opcode):
        bit = _bit(opcode)
        address = self._consume_saddr()
        value = self.read_memory(address)
        result = self._operation_clr1(value, bit)
        self.write_memory(address, result)

    # ret                         ;af
    def _opcode_0xaf(self, opcode):
        self.pc = self._pop_word()

    # reti                        ;8f
    def _opcode_0x8f(self, opcode):
        self.pc = self._pop_word()
        self.write_psw(self._pop())

    # retb                        ;9f
    def _opcode_0x9f(self, opcode):
        self.pc = self._pop_word()
        self.write_psw(self._pop())

    # brk                         ;bf
    def _opcode_0xbf(self, opcode):
        psw = self.read_psw()
        self._push(psw)
        self._push_word(self.pc)
        self.write_psw(psw & ~Flags.IE)
        self.pc = self.read_memory_word(self.BRK_VECTOR_ADDRESS)

    # br $label7                  ;fa fe
    def _opcode_0xfa(self, opcode):
        displacement = self._consume_byte()
        address = _resolve_rel(self.pc, displacement)
        self.pc = address

    # bc $label3                  ;8d fe
    def _opcode_0x8d(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.CY:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # bnc $label3                 ;9d fe
    def _opcode_0x9d(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.CY == 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # bz $label5                  ;ad fe
    def _opcode_0xad(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.Z:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # bnz $label5                 ;bd fe
    def _opcode_0xbd(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.Z == 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # movw 0fe20h,#0abcdh         ;ee 20 cd ab    saddrp
    # movw sp,#0abcdh             ;ee 1c cd ab  (SP=0xFF1C)
    def _opcode_0xee(self, opcode):
        address = self._consume_saddrp()
        value_low = self._consume_byte()
        self.write_memory(address, value_low)
        value_high = self._consume_byte()
        self.write_memory(address+1, value_high)

    # inc x                       ;40
    # ...
    # inc h                       ;47
    def _opcode_0x40_to_0x47_inc(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(reg)
        result = self._operation_inc(value)
        self.write_gp_reg(reg, result)

    # dec x                       ;50
    # ...
    # dec h                       ;57
    def _opcode_0x50_to_0x57_dec(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(reg)
        result = self._operation_dec(value)
        self.write_gp_reg(reg, result)

    # inc 0fe20h                  ;81 20          saddr
    def _opcode_0x81(self, opcode):
        address = self._consume_saddr()
        value = self.read_memory(address)
        result = self._operation_inc(value)
        self.write_memory(address, result)

    # dec 0fe20h                  ;91 20          saddr
    def _opcode_0x91(self, opcode):
        address = self._consume_saddr()
        value = self.read_memory(address)
        result = self._operation_dec(value)
        self.write_memory(address, result)

    # 0c 00          0c = callf 0800h-08ffh
    # ...
    # 7c 00          7c = callf 0f00h-0fffh
    def _opcode_0x0c_to_0x7c_callf(self, opcode):
        base = 0x0800 + ((opcode >> 4) << 8)
        offset = self._consume_byte()
        self._push_word(self.pc)
        self.pc = base + offset

    # callt [0040h]               ;c1
    # ...
    # callt [007eh]               ;ff
    def _opcode_0xc1_to_0xff_callt(self, opcode):
        offset = (opcode & 0b00111110) >> 1
        vector_address = 0x40 + (offset * 2)
        address = self.read_memory_word(vector_address)
        self._push_word(self.pc)
        self.pc = address

    # dbnz c,$label1              ;8a fe
    def _opcode_0x8a(self, opcode):
        displacement = self._consume_byte()
        c = self.read_gp_reg(Registers.C) - 1
        if c < 0:
            c = 0xFF
        self.write_gp_reg(Registers.C, c)
        if c != 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # dbnz b,$label2              ;8b fe
    def _opcode_0x8b(self, opcode):
        displacement = self._consume_byte()
        c = self.read_gp_reg(Registers.B) - 1
        if c < 0:
            c = 0xFF
        self.write_gp_reg(Registers.B, c)
        if c != 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # dbnz 0fe20h,$label0         ;04 20 fd       saddr
    def _opcode_0x04(self, opcode):
        value_address = self._consume_saddr()
        displacement = self._consume_byte()
        value = self.read_memory(value_address) - 1
        if value < 0:
            value = 0xFF
        self.write_memory(value_address, value)
        if value != 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # movw ax,0fffeh              ;a9 fe          sfrp
    def _opcode_0xa9(self, opcode):
        address = self._consume_sfrp()
        value_low = self.read_memory(address)
        self.write_gp_reg(Registers.X, value_low)
        value_high = self.read_memory(address + 1)
        self.write_gp_reg(Registers.A, value_high)

    # mov a,[hl+c]                ;aa
    def _opcode_0xaa(self, opcode):
        address = self._based_hl_c()
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # mov a,[hl+b]                ;ab
    def _opcode_0xab(self, opcode):
        address = self._based_hl_b()
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # mov a,[hl+0abh]             ;ae ab
    def _opcode_0xae(self, opcode):
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        value = self.read_memory(address)
        self.write_gp_reg(Registers.A, value)

    # mov [hl+c],a                ;ba
    def _opcode_0xba(self, opcode):
        address = self._based_hl_c()
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # mov [hl+b],a                ;bb
    def _opcode_0xbb(self, opcode):
        address = self._based_hl_b()
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # mov [hl+0abh],a             ;be ab
    def _opcode_0xbe(self, opcode):
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        value = self.read_gp_reg(Registers.A)
        self.write_memory(address, value)

    # movw ax,bc                  ;c2
    # movw ax,de                  ;c4
    # movw ax,hl                  ;c6
    def _opcode_0xc2_to_0xc6_movw(self, opcode):
        regpair = _regpair(opcode)
        value = self.read_gp_regpair(regpair)
        self.write_gp_regpair(RegisterPairs.AX, value)

    # movw bc,ax                  ;d2
    # movw de,ax                  ;d4
    # movw hl,ax                  ;d6
    def _opcode_0xd2_to_0xd6_movw(self, opcode):
        regpair = _regpair(opcode)
        value = self.read_gp_regpair(RegisterPairs.AX)
        self.write_gp_regpair(regpair, value)

    # xch a,[hl+0abh]             ;de ab
    def _opcode_0xde(self, opcode):
        imm = self._consume_byte()
        address = self._based_hl_imm(imm)
        other_value = self.read_memory(address)
        a_value = self.read_gp_reg(Registers.A)
        self.write_gp_reg(Registers.A, other_value)
        self.write_memory(address, a_value)

    # movw 0fffeh,#0abcdh         ;fe fe cd ab    sfrp
    def _opcode_0xfe(self, opcode):
        address = self._consume_sfrp()
        value_low = self._consume_byte()
        self.write_memory(address, value_low)
        value_high = self._consume_byte()
        self.write_memory(address+1, value_high)

    # push ax                     ;b1
    # ...
    # push hl                     ;b7
    def _opcode_0xb1_to_0xb7_push_rp(self, opcode):
        regpair = _regpair(opcode)
        value = self.read_gp_regpair(regpair)
        self._push_word(value)

    # pop ax                      ;b0
    # ...
    # pop hl                      ;b6
    def _opcode_0xb0_to_0xb6_pop_rp(self, opcode):
        regpair = _regpair(opcode)
        value = self._pop_word()
        self.write_gp_regpair(regpair, value)

    # Operations

    def _operation_bt(self, value, bit, displacement):
        bitweight = 2 ** bit
        if value & bitweight:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    def _operation_bf(self, value, bit, displacement):
        bitweight = 2 ** bit
        if value & bitweight == 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    def _operation_btclr(self, value, bit, displacement):
        bitweight = 2 ** bit
        if value & bitweight:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address
        result = value & ~bitweight
        return result

    def _operation_xor1(self, src, src_bit, dest, dest_bit):
        src_bitweight = 2 ** src_bit
        dest_bitweight = 2 ** dest_bit
        if (src & src_bitweight) and (dest & dest_bitweight):
            result = dest & ~dest_bitweight # 1 xor 1 = 0
        elif (src & src_bitweight == 0) and (dest & dest_bitweight == 0):
            result = dest & ~dest_bitweight # 0 xor 0 = 0
        else:
            result = dest | dest_bitweight # 0 xor 1 = 1, 1 xor 0 = 1
        return result

    def _operation_or1(self, src, src_bit, dest, dest_bit):
        src_bitweight = 2 ** src_bit
        dest_bitweight = 2 ** dest_bit
        if (src & src_bitweight) or (dest & dest_bitweight):
            result = dest | dest_bitweight
        else:
            result = dest # dest bit must already be off
        return result

    def _operation_and1(self, src, src_bit, dest, dest_bit):
        src_bitweight = 2 ** src_bit
        dest_bitweight = 2 ** dest_bit
        if (src & src_bitweight) and (dest & dest_bitweight):
            result = dest | dest_bitweight
        else:
            result = dest & ~dest_bitweight
        return result

    def _operation_mov1(self, src, src_bit, dest, dest_bit):
        src_bitweight = 2 ** src_bit
        dest_bitweight = 2 ** dest_bit
        if src & src_bitweight:
            result = dest | dest_bitweight
        else:
            result = dest & ~dest_bitweight
        return result

    def _operation_addw(self, a, b):
        # TODO docs say AC is undefined, so we just clear it.  Find
        # out what the hardware really does to AC.
        psw = self.read_psw() & ~(Flags.Z + Flags.AC + Flags.CY)
        sum = a + b
        if sum > 0xFFFF:
            psw |= Flags.CY
        result = sum & 0xFFFF
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_subw(self, a, b):
        # TODO docs say AC is undefined, so we just clear it.  Find
        # out what the hardware really does to AC.
        psw = self.read_psw() & ~(Flags.Z + Flags.AC + Flags.CY)
        difference = a - b
        if difference < 0:
            psw |= Flags.CY
        result = difference & 0xFFFF
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_sub(self, a, b):
        psw = self.read_psw() & ~(Flags.Z + Flags.AC + Flags.CY)
        if ((a & 0x0f) - (b & 0x0f)) & 0x10:
            psw |= Flags.AC
        difference = a - b
        if difference < 0:
            psw |= Flags.CY
        result = difference & 0xff
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_subc(self, a, b):
        psw = self.read_psw()
        carry = psw & Flags.CY
        psw &= ~(Flags.Z + Flags.AC + Flags.CY)
        if ((a & 0x0f) - (b & 0x0f) - carry) & 0x10:
            psw |= Flags.AC
        difference = a - b - carry
        if difference < 0:
            psw |= Flags.CY
        result = difference & 0xff
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_add(self, a, b):
        psw = self.read_psw() & ~(Flags.Z + Flags.AC + Flags.CY)
        if ((a & 0x0F) + (b & 0x0F)) > 0x0F:
            psw |= Flags.AC
        sum = a + b
        if sum > 0xFF:
            psw |= Flags.CY
        result = sum & 0xFF
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_addc(self, a, b):
        psw = self.read_psw()
        carry = psw & Flags.CY
        psw &= ~(Flags.Z + Flags.AC + Flags.CY)
        if ((a & 0x0F) + (b & 0x0F) + carry) > 0x0F:
            psw |= Flags.AC
        sum = a + b + carry
        if sum > 0xFF:
            psw |= Flags.CY
        result = sum & 0xFF
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_inc(self, value):
        psw = self.read_psw() & ~(Flags.Z + Flags.AC)
        if value & 0x0f == 0x0f:
            psw |= Flags.AC
        result = (value + 1) & 0xFF
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_dec(self, value):
        psw = self.read_psw() & ~(Flags.Z + Flags.AC)
        if value & 0x0f == 0:
            psw |= Flags.AC
        result = (value - 1) & 0xFF
        if result == 0:
            psw |= Flags.Z
        self.write_psw(psw)
        return result

    def _operation_incw(self, value):
        return (value + 1) & 0xFFFF

    def _operation_decw(self, value):
        return (value - 1) & 0xFFFF

    def _operation_set1(self, value, bit):
        return value | (2 ** bit)

    def _operation_clr1(self, value, bit):
        return value & ~(2 ** bit)

    def _operation_or(self, a, b):
        result = a | b
        self._update_psw_z(result)
        return result

    def _operation_and(self, a, b):
        result = a & b
        self._update_psw_z(result)
        return result

    def _operation_xor(self, a, b):
        result = a ^ b
        self._update_psw_z(result)
        return result

    # Addressing Helpers

    def _consume_byte(self):
        value = self.read_memory(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return value

    def _consume_word(self):
        low = self._consume_byte()
        high = self._consume_byte()
        return _word(low, high)

    def _consume_addr16(self):
        low = self._consume_byte()
        high = self._consume_byte()
        return _addr16(low, high)

    def _consume_addr16p(self):
        low = self._consume_byte()
        high = self._consume_byte()
        return _addr16p(low, high)

    def _consume_sfr(self):
        offset = self._consume_byte()
        return _sfr(offset)

    def _consume_sfrp(self):
        offset = self._consume_byte()
        return _sfrp(offset)

    def _consume_saddr(self):
        offset = self._consume_byte()
        return _saddr(offset)

    def _consume_saddrp(self):
        offset = self._consume_byte()
        return _saddrp(offset)

    def _based_hl_imm(self, imm):
        '''MOV A,[HL+byte]'''
        hl = self.read_gp_regpair(RegisterPairs.HL)
        return (hl + imm) & 0xFFFF

    def _based_hl_b(self):
        '''MOV A,[HL+B]'''
        hl = self.read_gp_regpair(RegisterPairs.HL)
        b = self.read_gp_reg(Registers.B)
        return (hl + b) & 0xFFFF

    def _based_hl_c(self):
        '''MOV A,[HL+C]'''
        hl = self.read_gp_regpair(RegisterPairs.HL)
        c = self.read_gp_reg(Registers.C)
        return (hl + c) & 0xFFFF

    # Stack

    def _push(self, value):
        """Push a byte onto the stack"""
        # TODO add test for wrap-around behavior
        sp = (self.read_sp() - 1) & 0xFFFF
        self.write_sp(sp)
        self.write_memory(sp, value)

    def _pop(self):
        """Pop a byte off the stack"""
        sp = self.read_sp()
        value = self.read_memory(sp)
        # TODO add test for wrap-around behavior
        self.write_sp((sp + 1) & 0xFFFF)
        return value

    def _push_word(self, value):
        """Push a word onto the stack"""
        self._push(value >> 8)
        self._push(value & 0xFF)

    def _pop_word(self):
        """Pop a word off the stack"""
        low = self._pop()
        high = self._pop()
        return (high << 8) + low

    # Registers

    def read_gp_reg(self, regnum):
        address = self.address_of_gp_reg(regnum)
        return self.read_memory(address)

    def write_gp_reg(self, regnum, data):
        address = self.address_of_gp_reg(regnum)
        self.write_memory(address, data)

    def address_of_gp_reg(self, regnum):
        """Return the address in RAM of a general purpose register:
           A, X, B, C, etc."""
        bank_addr = self.REGISTERS_BASE_ADDRESS - (self.read_rb() * 8)
        return bank_addr + regnum

    # Register Pairs

    def read_gp_regpair(self, regpairnum):
        address = self.address_of_gp_regpair(regpairnum)
        low = self.read_memory(address)
        high = self.read_memory(address+1)
        return _word(low, high)

    def write_gp_regpair(self, regpairnum, value):
        address = self.address_of_gp_regpair(regpairnum)
        low = value & 0xFF
        high = value >> 8
        self.write_memory(address, low)
        self.write_memory(address+1, high)

    def address_of_gp_regpair(self, regpairnum):
        """Return the address in RAM of a general purpose register
           pair: AX, BC, DE, etc.  The pair is stored in two bytes:
           low then high"""
        return self.address_of_gp_reg(regpairnum << 1)

    # Register Banks

    def read_rb(self):
        """Reads PSW and returns a register bank number 0..3"""
        rbs0 = (self.read_psw() & Flags.RBS0) >> 3
        rbs1 = (self.read_psw() & Flags.RBS1) >> 4
        return rbs0 + rbs1

    def write_rb(self, value):
        """Writes a register bank number 0..3 to the PSW"""
        rbs0 = (value & 1) << 3
        rbs1 = (value & 2) << 4
        self.write_psw(self.read_psw() & ~(Flags.RBS0 + Flags.RBS1))
        self.write_psw(self.read_psw() | (rbs0 + rbs1))

    # SP

    def read_sp(self):
        """Read the Stack Pointer"""
        low = self.read_memory(self.SP_ADDRESS)
        high = self.read_memory(self.SP_ADDRESS+1)
        return _word(low, high)

    def write_sp(self, value):
        low = value & 0xFF
        self.write_memory(self.SP_ADDRESS, low)
        high = value >> 8
        self.write_memory(self.SP_ADDRESS+1, high)

    # PSW

    def read_psw(self):
        """Read the Processor Status Word"""
        return self.read_memory(self.PSW_ADDRESS) & 0b11111011 # psw bit 2 always stuck off

    def write_psw(self, value):
        """Write the Processor Status Word"""
        self.write_memory(self.PSW_ADDRESS, value & 0b11111011) # psw bit 2 always stuck off

    def _update_psw_z(self, value):
        """Set the Z flag in PSW if value is zero, clear otherwise"""
        self.write_psw(self.read_psw() & ~Flags.Z)
        if value == 0:
            self.write_psw(self.read_psw() | Flags.Z)

    # Memory Helpers

    def read_memory(self, address):
        if address in self.RESERVED_ADDRESSES:
            return 0x08

        value = self.memory[address]
        return value

    def write_memory(self, address, value):
        if address in self.RESERVED_ADDRESSES:
            return

        self.memory[address] = value

    def write_memory_bytes(self, address, data):
        for address, value in enumerate(data, address):
            self.write_memory(address, value)

    def read_memory_word(self, address):
        low = self.read_memory(address)
        high = self.read_memory((address + 1) & 0xffff)
        return (high << 8) + low


def _sfr(low):
    sfr = 0xff00 + low
    return sfr

def _sfrp(low):
    sfrp = _sfr(low)
    if sfrp & 1 != 0:
        raise Exception("sfrp must be an even address")
    return sfrp

def _saddr(low):
    saddr = 0xfe00 + low
    if low < 0x20:
        saddr += 0x100
    return saddr

def _saddrp(low):
    saddrp = _saddr(low)
    if saddrp & 1 != 0:
        raise Exception("saddrp must be an even address")
    return _saddr(low)

def _word(low, high):
    return low + (high << 8)

_addr16 = _word

def _addr16p(low, high):
    addr16p = _addr16(low, high)
    if addr16p & 1 != 0:
        raise Exception("addr16p must be an even address")
    return addr16p

def _reg(opcode):
    return opcode & 0b111

def _regpair(opcode):
    return (opcode >> 1) & 0b11

def _bit(opcode):
    return (opcode & 0b01110000) >> 4

def _resolve_rel(pc, displacement):
    if displacement & 0x80:
        displacement = -((displacement ^ 0xFF) + 1)
    return (pc + displacement) & 0xffff

class Registers(object):
    X = 0
    A = 1
    C = 2
    B = 3
    E = 4
    D = 5
    L = 6
    H = 7

class RegisterPairs(object):
    AX = 0
    BC = 1
    DE = 2
    HL = 3

class Flags(object):
    CY     = 2**0
    ISP    = 2**1
    UNUSED = 2**2
    RBS0   = 2**3
    AC     = 2**4
    RBS1   = 2**5
    Z      = 2**6
    IE     = 2**7


class RegisterTrace:
    NamedRegisterPairs = (
        ('AX', RegisterPairs.AX),
        ('BC', RegisterPairs.BC),
        ('DE', RegisterPairs.DE),
        ('HL', RegisterPairs.HL)
    )

    @classmethod
    def generate(klass, processor):
        s = ""
        for name, reg in klass.NamedRegisterPairs:
            s += "%s=%04X " % (name, processor.read_gp_regpair(reg))
        s += "SP=%04X" % processor.read_sp()

        psw = processor.read_psw()
        s += " [IE:%d RB:%d ISP:%d Z:%d AC:%d CY:%d]" % (
            int(bool(psw & Flags.IE)),
            processor.read_rb(),
            int(bool(psw & Flags.ISP)),
            int(bool(psw & Flags.Z)),
            int(bool(psw & Flags.AC)),
            int(bool(psw & Flags.CY)),
        )

        return s


class Memory(bytearray):
    def __setitem__(self, address, value):
        if address == Processor.PSW_ADDRESS:
            value = value & 0b11111011  # psw bit 2 always stuck off
        super().__setitem__(address, value)
