# TRS-80 MC-10 Micro Color Computer
# This code is part of the process to convert a .vb file to .wav 'cassette' file for the MC-10
#  Step 1: vbToC10.py:  Convert .vb code to .C10 format
#  Step 2: C10ToWav.py: Convert .C10 code to .WAV format

# This file covers step 2

# Albert M Thalheim
# January 2021

# Description from the MC-10 Service Manual:

# The standard MC-10 tape is composed of the following items:
#  1. A leader consisting of 128 bytes of hex 55
#  2. A Namefile block (21 bytes)
#  3. A blank section of tape approximately equal to 0.5 seconds in length; this allows BASIC time to evaluate the Namefile.
#  4. A second leader of 128 bytes of Hex 55
#  5. One or more Data blocks (variable length)
#  6. An End of File block (6 bytes)

# ==============================================================
# The 'C10' file contains all the above EXCEPT the blank section
# Conversion to 'WAV' file SHOULD INSERT the blank section.
# ==============================================================

# This program will thus :
#  convert to wav format the first (128+21) 149 bytes,
#  add a half-second 'silence', and
#  convert to wav format the remainder of the .C10 file


# Global variables
#  Input data
firstPart = bytearray()
secondPart = bytearray()

# WAVE file parameters
#  Root parameters
chunkSize = 16
samples = 48000
channels = 1
bitsPerSample = 16
#  Computed parameters
blockAlign = channels * int(bitsPerSample / 8)
averageBytesPerSec = int(samples * blockAlign)


# Description from the MC-10 Service Manual:

#The cassette format uses a sinewave of 2400 or 1200 Hertz to yield a Baud rate of approximately 1500 Baud.
# In this format:
#  0 (or logic low) is represented by one cycle of 1200 Hertz.
cyclesFor0 = int(samples / 1200)
#  1 (or logic high) is represented by one cycle of 2400 Hertz
cyclesFor1 = int(samples / 2400)

amplitudeUp = 8000
amplitudeUpBytes = amplitudeUp.to_bytes(2, 'little', signed = True)

amplitudeDn = -amplitudeUp
amplitudeDnBytes =  amplitudeDn.to_bytes(2, 'little', signed = True)

bitsFor0 = bytearray()
bitsFor1 = bytearray()


def main():
    global firstPart
    global secondPart

    # Select .C10 file
    from tkinter.filedialog import askopenfilename
    c10Filepath = askopenfilename()
    if (c10Filepath == ''):
        from tkinter import messagebox
        messagebox.showinfo('Error', 'No file selected.')
        exit()
    else:
        # Set .WAV filepath (same directory)
        lastIndex = c10Filepath.rindex('.')
        extension = c10Filepath[lastIndex:]
        if (extension.upper() != '.C10'):
            from tkinter import messagebox
            messagebox.showinfo('Error', 'Expected format is .C10\nWas provided with ' + extension)
            exit()

    c10FileRoot = c10Filepath[:lastIndex]
    wavFilepath = c10FileRoot + '.wav'

    with open(c10Filepath, 'rb') as f:
        # First part is leader(128 bytes) + header(21 bytes) = 149 bytes:
        firstPart = f.read(149)
        # Second part is code block:
        secondPart = f.read()


    #==========================================================
    # 1. Build WAV Format Segment
    waveFormat = bytearray()
    # Set Wave Format Segment
    #   ChunkId: "fmt "
    waveFormat.extend(map(ord, "fmt "))
    #   chunkSize: 16
    waveFormat.extend(chunkSize.to_bytes(4, 'little'))
    #   FormatTag: 1
    waveFormat.extend((1).to_bytes(2, 'little'))
    #   channels: 2
    waveFormat.extend(channels.to_bytes(2, 'little'))
    #   samples: 48000
    waveFormat.extend(samples.to_bytes(4, 'little'))
    #   averageBytesPerSec:
    waveFormat.extend(averageBytesPerSec.to_bytes(4, 'little'))
    #   blockAlign: 4
    waveFormat.extend(blockAlign.to_bytes(2, 'little'))
    #   bitsPerSample: 16
    waveFormat.extend(bitsPerSample.to_bytes(2, 'little'))


    #==========================================================
    # 2. Build WAV Data Segment
    waveData = buildWaveData()


    #==========================================================
    # 3. Build WAV Header Segment
    waveHeader = bytearray()
    waveHeader.extend(map(ord, "RIFF"))
    fileLength = 12 + len(waveFormat) + len(waveData)
    waveHeader.extend(fileLength.to_bytes(4, 'little'))
    waveHeader.extend(map(ord, "WAVE"))


    #==========================================================
    # 4. Assemble and write WAV file
    wavBytes = bytearray()
    wavBytes.extend(waveHeader)
    wavBytes.extend(waveFormat)
    wavBytes.extend(waveData)

    with open(wavFilepath, 'w+b') as f:
        f.write(wavBytes)

    from tkinter import messagebox
    messagebox.showinfo('Done', 'Conversion complete.')


def buildWaveData():
    global bitsFor0
    global bitsFor1
    # Build cycle bytes
    bitsFor1 = buildCyclebits(cyclesFor1)
    bitsFor0 = buildCyclebits(cyclesFor0)

    # 1. Build data bytes
    waveBytes = bytearray()
    #  a). First Part
    waveBytes.extend(addPart(firstPart))
    #  b). Half-second silence
    waveBytes.extend(addBlank(0.5))
    #  c). Second Part
    waveBytes.extend(addPart(secondPart))

    # 2. Build data segment
    waveData = bytearray()
    #  a) Data Header
    waveData.extend(map(ord, "data"))
    #  b) Data bytes length
    waveData.extend(len(waveBytes).to_bytes(4, 'little'))
    #  c) Data bytes
    waveData.extend(waveBytes)

    # Return data segment
    return waveData


# Build one cycle of required frequency(defined by cycle count)
#  High amplitude followed by low amplitude
def buildCyclebits(cycleCount):
    cycleBytes = bytearray()
    halfCycle = int(cycleCount * 0.5)
    for i in range(0, halfCycle):
        cycleBytes.extend(amplitudeUpBytes)
    for i in range(0, halfCycle):
        cycleBytes.extend(amplitudeDnBytes)
    return cycleBytes


def addPart(currentPart):
    global bitsFor0
    global bitsFor1
    partArray = bytearray()
    for i in currentPart:
        # Get bits for this byte
        bits = bin(i)[2:]
        # Pad with '0's to fill up to 8 bits
        bits = bits.zfill(8)
        # Reverse the bits (MC-10 reads bits in reverse order)
        reverseBits = bits[::-1]
        # Process each bit, converting to 0/1 to a 1-cycle 'wav' data
        for j in reverseBits:
            if (j == '0'):
                partArray.extend(bitsFor0)
            else:
                partArray.extend(bitsFor1)
    return partArray


# Fill a byte array of required length with negative amplitude value (equivalent to silence for the required duration)
def addBlank(duration):
    blankArray = bytearray()
    count =  int(samples * duration * channels)
    for i in range(count):
        blankArray.extend(b'\x00')
    return blankArray


#==========================================================
# Call the main routine
main()

# EOF -\\-
