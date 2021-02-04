# TRS-80 MC-10 Micro Color Computer
# This code is part of the process to convert a .wav 'cassette' file for the MC-10 into a .vb file
#  Step 1: wavToC10.py:  Convert .wav code to .C10 format
#  Step 2: c10ToVb.py:   Convert .C10 code to .vb format

# This file covers step 1

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
# Conversion from 'WAV' file SHOULD OMIT the blank section.
# ==============================================================
#

# Wave format:
#  Header (12 bytes):
#    0- 3       'RIFF'
#    4- 7       total wave file length
#    8-11      'WAVE'
#  Format (24 bytes):
#   12-15       chunkId (4 bytes String):       "fmt "
#   16-19       chunkSize (4 bytes):            16
#   20-21       formatTag (2 bytes):            1
#   22-23       channels (2 bytes):             2
#   24-25       samples (4 bytes):              48000
#   26-31       averageBytesPerSec (4 bytes):   96000
#   32-33       blockAlign (2 bytes):           4
#   34-35       bitsPerSample (2 bytes):        16
#  Data (variable length):
#   36-39       'data' (4 bytes)
#   40-43       data length (4 bytes)
#   44-         data


import array as arr


# Global variables
waveValues = bytearray


def main():
    global waveValues

    # Select .C10 file
    from tkinter.filedialog import askopenfilename
    wavFilepath = askopenfilename()
    if (wavFilepath == ''):
        from tkinter import messagebox
        messagebox.showinfo('Error', 'No file selected.')
        exit()
    else:
        lastIndex = wavFilepath.rindex('.')
        extension = wavFilepath[lastIndex:]
        if (extension.upper() != '.WAV'):
            from tkinter import messagebox
            messagebox.showinfo('Error', 'Expected format is .WAV\nWas provided with ' + extension)
            exit()

    # Set .WAV filepath (same directory)
    wavFileRoot = wavFilepath[:lastIndex]
    c10Filepath = wavFileRoot + '.c10'

    # Get wave data
    with open(wavFilepath, 'rb') as f:
        waveData = f.read()

    #====================================================
    # HEADER: Skip

    #====================================================
    # FORMAT:
    chunkId = waveData[12:16].decode('ascii')
    chunkSize =  int.from_bytes(waveData[16:20], byteorder='little', signed=False)
    formatTag = int.from_bytes(waveData[20:22], byteorder='little', signed=False)
    channels =  int.from_bytes(waveData[22:24], byteorder='little', signed=False)
    samples = int.from_bytes(waveData[24:28], byteorder='little', signed=False)
    averageBytesPerSec =  int.from_bytes(waveData[28:32], byteorder='little', signed=False)
    blockAlign =  int.from_bytes(waveData[32:34], byteorder='little', signed=False)
    bitsPerSample =  int.from_bytes(waveData[34:36], byteorder='little', signed=False)
    # This code ignores any extra parameters (See wav specification)

    #====================================================
    # DATA:
    #  Get data start index:
    #   Header length: 12 bytes
    waveDataStartIndex = 12
    #   Format length: 4 bytes ('fmt ': 4 bytes) + chunk length descriptor(4 bytes) + chunk length
    waveDataStartIndex += (4 + 4 + chunkSize)
    #   Data header: 4 bytes ('data': 4 bytes)
    waveDataStartIndex += 4
    waveDataLength =   int.from_bytes(waveData[waveDataStartIndex:waveDataStartIndex + 4], byteorder='little', signed=False)

    #   Data length descriptor(4 bytes)
    waveDataStartIndex += 4
    # Extract the data part
    waveData = waveData[waveDataStartIndex:waveDataStartIndex + waveDataLength]


    #====================================================
    # Convert from byte array to int array
    sampleByteCount = int(bitsPerSample / 8)
    waveValues = arr.array('i')
    for i in range(0, len(waveData), sampleByteCount):
        j=int.from_bytes(waveData[i:i + sampleByteCount], byteorder='little', signed=True)
        waveValues.append(j)


    #====================================================
    # Get average cycle height
    #  Scan data to estimate cycle heights
    #   Look for high/low values
    #  Sum and count all found spans
    #  Finally, divide sum by sample counts
    shortCycleLength = int(samples / 2400)
    sumCycleHeight = 0
    sumCount = 0
    for i in range(1,len(waveValues)-shortCycleLength):
        first = waveValues[i]
        second = waveValues[i+ shortCycleLength]
        if (first > second):
            span = abs(first - second)
            sumCycleHeight += span
            sumCount += 1
    avgCycleHeight = int(sumCycleHeight / sumCount)

    # Get cycles start indexes:
    waveCycleIndexes = getHighCycleIndexes(shortCycleLength, avgCycleHeight)

    # Sample:
    # print('waveCycleIndexes')
    # print(waveCycleIndexes[6200:])
    # exit()

    # Get average span length
    waveCycleIndexesAvg = int(sum(waveCycleIndexes) / len(waveCycleIndexes))

    # Convert groups of 8 spans to C10 values:
    #  Each group represents the C10 value bits, in reverse order
    c10Values = arr.array('i')
    for i in range(0, len(waveCycleIndexes), 8):
        data = 0
        refValue = 0.5
        for d in waveCycleIndexes[i:i+8]:
            refValue = int(refValue * 2)
            if (d < waveCycleIndexesAvg):
                # Short:1
                data += refValue
        c10Values.append(data)


    print('len(c10Values)')
    print(len(c10Values))
    print('c10Values')
    print(c10Values)

    exit()

    # Convert short integers to bytes
    c10Bytes = bytearray
    for d in c10Values:
        c10Bytes.extend(d.to_bytes(1,'big'))

    # Finally, write C10 file
    with open(c10Filepath, 'w+b') as f:
        f.write(c10Bytes)


# Done with 'Main'




# Get Wave cycles
# An cycle being divided in two parts of roughly equal lengths:
#   a sequence of high values,
#   followed by a sequence of low values
# At 48000 samples per second,
#   -short interval (roughly 2400Hz) translates to around 20 values
#   -long interval (roughly 1200Hz) translates to around 40 values

# Using the scheme defined in the MC-10 Service Manual, we are looking for:
#   -Short cycle translating into '1'
#   -Long cycle translating into '0', and
#   -Absence of cycle translating to the 'silence' between data blocks

# The scheme here is to find the intervals where lengths:
#   will vary when recorded from the MC-10 computer, or
#   will be constant when from python-generated code.


def getHighCycleIndexes(shortCycleLength, avgCycleHeight):
    global waveValues

    precedingBlockLength = shortCycleLength * 3
    waveCycleIndexes = arr.array('i')

    #---------------------------------------------------
    # Data processing
    i = 0
    refStartIndex = 0
    while (i < len(waveValues)):
        # Use preceding block
        startIndex = max(refStartIndex, i - precedingBlockLength)
        endIndex = min(startIndex + precedingBlockLength, len(waveValues) - 1)
        precedingBlockValues = waveValues[startIndex:endIndex]
        precedingBlockValuesAvg = sum(precedingBlockValues) / len(precedingBlockValues)
        precedingBlockValuesSpan = max(precedingBlockValues) - min(precedingBlockValues)
        upperTriggerValue = precedingBlockValuesAvg + (precedingBlockValuesSpan / 6)

        # 1. Count successive 'higher than average' values
        count = 0
        while ((waveValues[i] > precedingBlockValuesAvg) or 
               (waveValues[i+1] > precedingBlockValuesAvg) or 
               (waveValues[i+2] > precedingBlockValuesAvg) or 
               (waveValues[i+3] > precedingBlockValuesAvg)):
            count += 1
            i += 1
        if (count > 0):
            waveCycleIndexes.append(count)
        # 2. Skip successive 'lower than trigger' values
        #  When count exceeds block lengh, reinitialize reference start index
        count = 0
        while (i < len(waveValues)) and (waveValues[i] < upperTriggerValue):
            count += 1
            i += 1
            if (count > precedingBlockLength):
                refStartIndex = i

    return waveCycleIndexes


#==========================================================
# Call the main routine
main()

# EOF -\\-
