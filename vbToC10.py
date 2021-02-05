# TRS-80 MC-10 Micro Color Computer
# This code is part of the process to convert a .vb file to .wav 'cassette' file for the MC-10
#  Step 1: C10Builder.py:  Convert .vb code to .C10 format
#  Step 2: C10ToWav.py:    Convert .C10 code to .WAV format

# This file covers step 1

# Albert M Thalheim
# January 2021

# Description from the MC-10 Service Manual

# The standard MC-10 tape is composed of the following items:
#  1. A leader consisting of 128 bytes of hex 55
#  2. A Namefile block (21 bytes)
#  3. A blank section of tape approximately equal to 0.5 seconds in length; this allows BASIC time to evaluate the Namefile.
#  4. A second leader of 128 bytes of Hex 55
#  5. One or more Data blocks
#  6. An End of File block (6 bytes)

# ==============================================================
# The 'C10' file contains all the above EXCEPT the blank section
# Conversion to 'WAV' file SHOULD INSERT the blank section.
# ==============================================================

# (Description continues)
# The block format for Data, Namefile or EndOfFile blocks is as follows:
#  1. One leader byte - 55H
#  2. One sync byte - 3CH
#  3. One block type byte:
#       00H - Namefile
#       01H = Data
#       FFH =End of File
#  4. One block length byte - 00H to FFH
#  5. Data - 0 to 255 bytes
#  6. One checksum byte - the sum of all the data plus block type and block length
#  7. One leader byte - 55H

# The Namefile block is a standard block with a length of 15 bytes (0FH) and the block type equals 00H. 
#  The 15 bytes of data provide information to BASIC and are employed as described below:
#  1. Eight bytes for the program name
#  2. One file type byte:
#       00H = BASIC
#       01H = Data
#       02H = Machine Language
#  3. One ASCII flag byte:
#       00H = Binary
#       FFH =ASCII
#  4. One Gap flag byte:
#       01H = Continuous
#       FFH= Gaps
#  5. Two bytes for the start address of a machine language program
#  6. Two bytes for the load address of a machine language program

#The End of File block is a standard block with a length of 0 and the block type equal to FFH. 
# (Description ends)

# Global variables
#  Program's name
programName = ''
#  Output file path
c10Filepath = ''
#  Previous code line number, to ensure a logical order is maintained
previousLineNo = -1
# According to the MC10 memory map, x4346 (17222) is the usual start ob BASIC programs:
memoryAddress = 17222

# Conversion table from text to byte code
mc10Codes = {}
# VB code scanned, validated and converted to a byte array
C10CodeBytes = bytearray()


def main():
    global c10Filepath
    global programName

    getMC10VbCodes()

    # Select .vb file
    from tkinter.filedialog import askopenfilename
    vbFilepath = askopenfilename()
    if (vbFilepath == ''):
        from tkinter import messagebox
        messagebox.showinfo('Error', 'No file selected.')
        exit()

    # Set C10 filepath (same directory)
    lastIndex = vbFilepath.rindex('.')
    extension = vbFilepath[lastIndex:]
    if (extension.upper() != '.VB'):
        from tkinter import messagebox
        messagebox.showinfo('Error', 'Expected format is .vb\nWas provided with ' + extension)
        exit()

    vbFileRoot = vbFilepath[:lastIndex]
    c10Filepath = vbFileRoot + '.C10'

    # Set C10 program filename
    programName = vbFileRoot.rsplit('/', 1).pop()
    programName = programName[:8]
    programName = programName.upper()

    getCodeLines(vbFilepath)


        # End of code delimitation
    C10CodeBytes.extend(b'\x00')
    C10CodeBytes.extend(b'\x00')

    buildAndExportC10Bytes()

    from tkinter import messagebox
    messagebox.showinfo('Done', 'Conversion complete.')

# End of main code


#==========================================================
# Step 1: Format code lines (lineNo_space_code) to (memAddress_lineNo_code) into a byte array
#  1.a) Process all code lines
def getCodeLines(txtFilepath):
    global C10CodeBytes
    global memoryAddress

    # Process file text one line at a time
    with open(txtFilepath, 'r', encoding='ascii') as f:
        codeLines = f.readlines()
        for codeLine in codeLines:
            codeLine = codeLine.strip()
            if codeLine == '':
                # Skip empty lines
                codeLine = ''
            elif codeLine.startswith('#'):
                # Skip comments
                codeLine = ''
            else:
                codeFragment = buildByteLine(codeLine)
                #  Next line start address
                memoryAddress += len(codeFragment)
                first = memoryAddress // 256
                last = memoryAddress % 256
                codeFragment.insert(0, first)
                codeFragment.insert(1, last)
                # Add code bytes to global array
                C10CodeBytes.extend(codeFragment)

#  1.b) Process single code line
def buildByteLine(codeLine):
    global previousLineNo

    # Step 1: Get and validate code line number
    #  a) Get line number:
    firstSpaceIndex = codeLine.index(' ')
    lineNo = int(codeLine[:firstSpaceIndex])
    #  b) Remove line number from codeLine:
    codeLine = codeLine[firstSpaceIndex:]
    codeLine = codeLine.strip()

    #  c) Validate number: exit when invalid
    if (lineNo <= previousLineNo):
        from tkinter import messagebox
        messagebox.showinfo('Error', 'LineNo ' + str(lineNo) + ' follows lineNo ' + str(previousLineNo))
        exit()

    #  d) Keep reference of last line No
    previousLineNo = lineNo

    # Start process
    codeFragment = bytearray()
    #  Line number
    first = lineNo // 256
    last = lineNo % 256
    codeFragment.extend(first.to_bytes(1, 'big'))
    codeFragment.extend(last.to_bytes(1, 'big'))

    #  Code
    while codeLine != '':
        if (codeLine.startswith('"')):
            lastIndex = codeLine.index('"',1)
            codeFragment.extend(str.encode(codeLine[:lastIndex + 1]))
            codeLine = codeLine[lastIndex + 1:]
        else:
            codeWord = getCodeWord(codeLine)
            if (codeWord is None):
                codeFragment.extend(str.encode(codeLine[:1]))
                codeLine = codeLine[1:]
            else:
                codeFragment.extend(mc10Codes[codeWord])
                if len(codeWord) == len(codeLine):
                    codeLine = ''
                else:
                    codeLine = codeLine[len(codeWord):]
        codeLine = codeLine.strip()
    #  End of code line
    codeFragment.extend(b'\x00')
    #  return fragment
    return codeFragment


def getMC10VbCodes():
    global mc10Codes
    # Get MC10 Codes: (keyword: binary value)
    mc10Codes = {}
    with open('.\MC10-Codes.txt', 'r') as f:
        Lines = f.readlines()
        for line in Lines: 
            line = line.strip()
            if line == '':
                line = ''
            elif line.startswith('#'):
                line = ''
            else:
                values = line.split('\t')
                mc10Codes[values[1]] = bytes.fromhex(values[0]) 


#  1.c) scan code line (at start position) for codeWord
def getCodeWord(codeLine):
    # Code line to uppercase
    upperCodeLine = codeLine.upper()
    for codeWord in mc10Codes:
        if (upperCodeLine.startswith(codeWord)):
            return codeWord
    return None


#==========================================================
# Step 2: Build C10 data
#  Cut data in 255 bytes chunks
#  Build a data block from each chunk
#  Append each chunk to the dataBytes array
def buildC10Data():
    dataBytes = bytearray()

    for i in range(0,len(C10CodeBytes),255):
        dataLength = min(255, len(C10CodeBytes)-i)
        dataEnd = (i + dataLength)

        dataBlock = bytearray()
        # Data type:1
        dataBlock.extend(b'\x01')
        # Data length
        dataBlock.extend(dataLength.to_bytes(1, 'big'))
        # Data
        dataBlock.extend(C10CodeBytes[i:dataEnd])
        # Build data block and append to data bytes array
        dataBytes.extend(buildBlock(dataBlock))
    return dataBytes


#==========================================================
# Step 3: Export C10 data
#  3.a)
def buildAndExportC10Bytes():
    C10Bytes = bytearray()
    C10Bytes.extend(buildLeaderOf55s())
    C10Bytes.extend(buildC10Header())
    C10Bytes.extend(buildLeaderOf55s())
    C10Bytes.extend(buildC10Data())
    C10Bytes.extend(buildBlock(bytes([0xff, 0x00])))

    with open(c10Filepath, 'w+b') as f:
        f.write(C10Bytes)



#  3.b)
def buildLeaderOf55s():
    leaderOf55s = bytearray()
    for i in range(0, 128):
        leaderOf55s.extend(b'\x55')
    return leaderOf55s


#  3.c)
def buildC10Header():
    c10Header = bytearray()
    c10Header.extend(b'\x00')
    c10Header.extend(b'\x0f')
    # programName
    c10Header.extend(str.encode(programName))
    if len(programName) < 8:
        for i in range(len(programName), 8):
            c10Header.extend(b'\x20')
    # Block type: BASIC: 00
    c10Header.extend(b'\x00')
    # ASCII flag type:
    c10Header.extend(b'\x00')
    # Gap flag type:
    c10Header.extend(b'\x00')
    # Two bytes for the start address of a machine language program: N/A
    c10Header.extend(b'\x00')
    c10Header.extend(b'\x00')
    # Two bytes for the load address of a machine language program: N/A
    c10Header.extend(b'\x00')
    c10Header.extend(b'\x14')
    #
    return buildBlock(c10Header)


#==========================================================
# 4: Build Block
def buildBlock(data):
    dataBlock = bytearray()
    # Block start
    dataBlock.extend(b'\x55')
    # Block sync byte
    dataBlock.extend(b'\x3c')
    # Block Data
    dataBlock.extend(data)
    # Block Checksum
    sum = 0
    for i in data:
        sum += i
    dataBlock.extend((sum % 256).to_bytes(1, 'big'))
    # Block end byte
    dataBlock.extend(b'\x55')
    #
    return dataBlock



#==========================================================
# Call the main routine
main()

# EOF -\\-
