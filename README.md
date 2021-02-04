# TRS-80-MC-10
Code and data related to the TRS-80 MC-10 computer
Editing VB code using the MC-10 keyboard is a pain, particularly with long code.
The Python files found here help in using text files edited on another computer:

-MC10.png
  Graphic description of the process.
  
-vbToC10.py
  Convert VB code (in a text file) into the C10 format (see below).
  
-c10ToWav.py
  Convert C10 formatted file (see below) to a wave-formatted sound file.
  Play this file to the MC-10 computer to load the program.
  
-wavToC10.py
  Convert C10-formatted wave file to C10 format (see below)
  Beware! This code was not extensively tested!
  
-c10ToVb.py
  Convert C10 formatted file (see below) to plain text file.
  
C10 format:
  A binary file formatted as per MC-10 specifications:
    -Leader: 128 bytes of value x55;
    
    -Header: Block containing program name and type;
    
    (Note: missing half-second 'silence');
    
    -Leader: 128 bytes of value x55;
    
    -Code blocks;
    
    -EOF block;
    
    
