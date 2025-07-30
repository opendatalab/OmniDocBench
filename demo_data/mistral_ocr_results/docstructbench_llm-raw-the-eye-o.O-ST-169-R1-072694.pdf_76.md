# Result Parameter Details 

## Peripheral Control Status

The SMPC outputs the peripheral control status to the status register (SR) when the SMPC control mode is used. The status register (SR) is a register that can be read without regard for the INTBACK command. However, when the register is read when the INTBACK command is not in use, all bits except the RESB bit will be undefined.

| SR | bit7 |  |  |  |  |  | bit0 |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  | 1 | PDL | NPE | RESB | P2MD1 | P2MD0 | P1MD1 | P1MD0 |
|  | P1MD: | Port 1 Mode <br> 00: 15-byte mode (Returns peripheral data up to a maximum of 15 bytes.) <br> 01: 255-byte mode (Returns peripheral data up to a maximum of 255 bytes.) <br> 10: Unused <br> 11: 0-byte mode (Port is not accessed.) |  |  |  |  |  |  |
|  | P2MD: | Port 2 Mode <br> 00: 15-byte mode (Returns peripheral data up to a maximum of 15 bytes.) <br> 01: 255-byte mode (Returns peripheral data up to a maximum of 255 bytes.) <br> 10: Unused <br> 11: 0-byte mode (Port is not accessed.) |  |  |  |  |  |  |
|  | RESB: | Reset Button Status Bit <br> 0: Reset Button OFF <br> 1: Reset Button ON <br> Reading without regard for INTBACK command is possible. (Shows status for each V-BLANK-IN.) |  |  |  |  |  |  |
|  | NPE: | Remaining Peripheral Existence Bit <br> 0: No remaining data <br> 1: Remaining data |  |  |  |  |  |  |
|  | PDL: | Peripheral Data Location Bit <br> 0: 2nd or above peripheral data <br> 1: 1st peripheral data |  |  |  |  |  |  |
|  | bit7: | Always 1 |  |  |  |  |  |  |

Figure 3.13 Peripheral Control Status