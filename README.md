# TRS-80-MC-10
Code and data related to the TRS-80 MC-10 computer
Editing VB code using the MC-10 keyboard is a pain, particularly with long code.
The Python files found here help in using text files edited on another computer:

Data

-mc10BasicRom.bin --- MC-10 BASIC interpreter (8k)
  
mc10BasicRomInContext.bin --- vMC-10 BASIC interpreter (8k), in context (addresses E000-FFFF)


-----------------------------------------------------------

-MC10.png --- Graphic description of the process.

-----------------------------------------------------------

On the way from home computer to the MC-10:

-vbToC10.py --- Convert VB code (in a text file) into the C10 format (see below).
  
-c10ToWav.py --- Convert C10 formatted file (see below) to a wave-formatted sound file.
                              Play this file to the MC-10 computer to load the program.

-----------------------------------------------------------

From the MC-10 to home computer (Beware! This code was not extensively tested!)

-wavToC10.py --- Convert C10-formatted wave file to C10 format (see below)
  
-c10ToVb.py --- Convert C10 formatted file (see below) to plain text file.
  
-----------------------------------------------------------

MC10-Codes.txt --- Table of VB keywords and associated byte value, used in 'vbToC10.py' and 'c10ToVb.py'.
  
-----------------------------------------------------------

C10 format:
  A binary file formatted as per MC-10 specifications:
    -Leader: 128 bytes of value x55;
    
    -Header: Block containing program name and type;
    
    (Note: missing half-second 'silence');
    
    -Leader: 128 bytes of value x55;
    
    -Code blocks;
    
    -EOF block;
    
    
