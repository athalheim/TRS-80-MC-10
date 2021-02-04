# TRS-80 MC-10 Micro Color Computer
# This code is part of the process to convert a .wav 'cassette' file for the MC-10 into a .vb file
#  Step 1: wavToC10.py:  Convert .wav code to .C10 format
#  Step 2: c10ToVb.py:   Convert .C10 code to .vb format

# This file covers step 2

# Albert M Thalheim
# January 2021


# Description from the MC-10 Service Manual:

# Step 1: Extract data from C10 block structure
#  The block format for Data, Namefile or EndOfFile blocks is as follows:
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

# Collection of keyword and associated int value
mc10Codes = {}

def main():
    getMC10VbCodes()

    # Select .c10 file
    from tkinter.filedialog import askopenfilename
    c10Filepath = askopenfilename()
    if (c10Filepath == ''):
        from tkinter import messagebox
        messagebox.showinfo('Error', 'No file selected.')
        exit()
    else:
        lastIndex = c10Filepath.rindex('.')
        extension = c10Filepath[lastIndex:]
        if (extension.upper() != '.C10'):
            from tkinter import messagebox
            messagebox.showinfo('Error', 'Expected format is .c10\nWas provided with ' + extension)
            exit()

    # Set VB filepath (same directory)
    c10FileRoot = c10Filepath[:lastIndex]
    vbFilepath = c10FileRoot + '.vb'

    fileContent = bytearray()
    with open(c10Filepath, 'rb') as f:
        f.seek(277)
        dataPart = f.read()

    # Step 1: Extract data from C10 block structure
    dataBytes = bytearray()
    while True:
        dataLengthByte = dataPart[3:4]
        dataLength = int.from_bytes(dataLengthByte, "big")
        blockLength = 4 + dataLength + 2
        if (blockLength == 6):
            break
        dataBytes.extend(dataPart[4:4 + dataLength])
        dataPart = dataPart[blockLength:]

    # Step 2: Decode data into text
    # Each code line:
    #  Skip 2 bytes: memory address
    #  Get 2 bytes: line number
    #  Find '0' delimiter
    #  Get code block without delimiter
    dataByteBlocks = bytearray
    with open(vbFilepath + 'a', 'w') as f:
        # Process until last two delimiters encountered
        while (len(dataBytes) > 2):
            lineNo = int.from_bytes(dataBytes[2:4], byteorder='big', signed=False)
            dataBytes = dataBytes[4:]
            indexZero = dataBytes.find(b'\x00')
            dataBlock = dataBytes[:indexZero]
            dataBytes = dataBytes[indexZero + 1:]
            
            dataLine = str(lineNo) + ' '
            for i in dataBlock:
                if (i> 127):
                    codeWord = getWordFromCode(i)
                    if (codeWord == None):
                        dataLine += '(Missing Code: ' + str(i) + ') '
                    else:
                        dataLine += codeWord + ' '
                else:
                    dataLine += chr(i)
            f.write(dataLine + '\n')

def getMC10VbCodes():
    global mc10Codes
    # Get MC10 Codes: (keyword: int value)
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
                mc10Codes[values[1]] = int(values[0], 16)


def getWordFromCode(code):
    # Code line to uppercase
    for codeWord in mc10Codes:
        if (mc10Codes[codeWord] == code):
            return codeWord
    return None


#==========================================================
# Call the main routine
main()

# EOF -\\-