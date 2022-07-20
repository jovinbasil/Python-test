import serial.tools.list_ports
import keyboard
import datetime
import os
from os import remove
import os.path
from tkinter.filedialog import askdirectory
from tkinter import Tk


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        i = self.buf.find(b"\n")

        if i >= 0:
            r = self.buf[:i + 1]
            self.buf = self.buf[i + 1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i + 1]
                self.buf[0:] = data[i + 1:]
                return r
            else:
                self.buf.extend(data)


def search_port():
    # Search for serial port
    ports = list(serial.tools.list_ports.comports())
    port = ""
    for p in ports:
        # print(p.description)
        if "USB to UART Bridge" in p.description:
            port = p.device

    if port == "":
        select = input("Serial port could not be detected automatically. Enter the name shown in the Device Manager: ")
        for p in ports:
            if select in p.description:
                port = p.device
    if port == "":
        print("Error accessing serial port. Please fix connection and restart.")
        exit()

    serialPort = serial.Serial(port, baudrate=921600)  # 115200 230400 460800 921600

    return serialPort


def open_port(serial_port):
    try:
        if serial_port.isOpen():
            serial_port.close()
        serial_port.open()
    except:
        print("Error accessing serial port. Please fix connection and restart.")
        exit()


def gather_data(serial_port, file, selected_mode, device, name):
    count = 0
    reader = ReadLine(serial_port)

    while True:
        if keyboard.is_pressed('spacebar'):
            if selected_mode == 7:
                try:
                    duration = end_time - start_time
                    duration_s = duration.total_seconds()
                    freq = count / duration_s
                    print("Sampling frequency: %s Hz" % freq)
                except UnboundLocalError:
                    print("No data captured")
            file.close()
            return

        if keyboard.is_pressed('esc'):
            file.close()
            #print(name)
            file_exists = os.path.exists("{}".format(name))
            if file_exists == True:
                print ("Deleting file.. ")
                delete_data(serial_port, file, selected_mode, device, name)

        data = reader.readline()
        time = datetime.datetime.now()
        try:
            data_string = data.decode("ASCII")
            data_string = data_string.strip()
            print(data_string)

            if data_string.__contains__("--"):
                summary_file = open("%s Summary.txt" % device, "w")

                while True:
                    data = reader.readline()
                    data_string = data.decode("ASCII")
                    data_string = data_string.strip()
                    print(data_string)

                    if data_string.__contains__("Going to sleep!"):
                        file.close()
                        summary_file.close()
                        return

                    summary_file.write(data_string)
                    summary_file.write('\n')

            if data_string.__contains__("Going to sleep!"):
                file.close()
                return

            array = data_string.split(",")
            # Skip text and \n lines, skip incomplete lines
            if len(array) == 5 or len(array) == 6:
                # ACT mode: [timestamp, pressure adj, pressure raw, short avg, long avg, ]
                # PFT mode: [timestamp, pressure adj, pressure raw, flowrate, ]
                if count == 0:
                    start_time = time
                count = count + 1
                end_time = time

                if selected_mode == 1 or selected_mode == 6:
                    # Only write raw pressure values
                    file.write(array[2])
                    file.write('\n')
                else:
                    # Only write adj pressure values
                    file.write(array[1])
                    file.write('\n')

                # Print pressure values in Other Test mode
                """if selected_mode == 7:
                    print(array[1])"""

        except UnicodeDecodeError:
            print("Decode error")

def delete_data(serial_port, f_ile, s_elected_mode, d_evice, n_ame):
    remove("{}".format(n_ame))
    input("Ready to recapture data. Press ENTER to begin.")
    print("Data capture in progress. Press the SPACEBAR to stop.\n")
    logfile = open(n_ame, "w")
    open_port(serial_port)
    gather_data(serial_port, logfile, s_elected_mode, d_evice, n_ame)
    return


print("Initializing Data Capture Script")
print(". . . . . . . . . . . . . . . . . . . . . . . . . . . \n\n")

# Request directory
print("Select the directory where the data should be stored.")
# Tk().withdraw()
selectedPath = askdirectory(title='Select Folder')
os.chdir(selectedPath)

# Request mode
modes = ["Static Pressure", "Constant Flow ACT", "Dynamic Flow ACT", "PQ Equation", "PFT", "Pressure Sensor Check",
         "Other Test"]
selectedMode = input("Enter the mode number:\n1. Static Pressure\n2. Constant Flow ACT\n3. Dynamic Flow ACT\n4. PQ "
                     "Equation\n5. PFT\n6. Pressure Sensor Check\n7. Other Test\n")
selectedMode = int(selectedMode)
if selectedMode == 1:
    flowTests = ["atm", "0", "5"]
elif selectedMode == 2:
    flowTests = ["High-10", "High-30", "Low-10", "Low-30"]
elif selectedMode == 3:
    flowTests = ["Low-15PEF", "Low-40PEF", "High-40PEF", "High-60PEF"]
elif selectedMode == 4:
    flowTests = ["Combined Waveform"]
elif selectedMode == 5:
    flowTests = ["C01", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13"]
elif selectedMode == 6:
    flowTests = ["atm", "0", "1", "2", "3", "4", "5"]
else:
    flowTests = []

# Create test folder
os.makedirs(modes[selectedMode - 1], exist_ok=True)
os.chdir(modes[selectedMode - 1])

# If 'Other' selected, request name of device and test before each run
if selectedMode == 7:
    newTest = True

    while newTest:
        # Search for serial port
        serialPort = search_port()

        currDevice = input("Enter device name: ")
        currTest = input("Enter test name: ")
        currTime = datetime.datetime.now()

        # Create log file
        fileName = "%s - %s - %s.txt" % (currTime.strftime("%Y%m%d %H%M%S"), currDevice, currTest)
        logFile = open(fileName, "w")

        input("Ready to collect data for %s - %s. Press ENTER to begin." % (currDevice, currTest))
        print("Data capture in progress. Press the SPACEBAR to stop.\n")

        # Open serial port and read data
        open_port(serialPort)
        gather_data(serialPort, logFile, selectedMode, currDevice, fileName)
        serialPort.close()

        repeat = input("Perform another test? (y/n) ")
        repeat = repeat.strip()
        if repeat.upper() == 'N':
            newTest = False

# If 'Other' not selected, request number and name of devices before running tests
else:
    numDevices = input("Enter the number of devices: ")
    numDevices = int(numDevices)

    deviceNames = []
    for i in range(0, numDevices):
        deviceName = input("Enter device name %s: " % (i + 1))
        deviceNames.append(deviceName)

    for x in range(0, len(deviceNames)):
        currDevice = deviceNames[x]

        # Search for serial port
        serialPort = search_port()

        for y in range(0, len(flowTests)):
            # Create log file
            currTime = datetime.datetime.now()
            fileName = "%s - %s - %s.txt" % (currTime.strftime("%Y%m%d %H%M%S"), currDevice, flowTests[y])
            logFile = open(fileName, "w")

            input("Ready to collect data for %s - %s. Press ENTER to begin." % (currDevice, flowTests[y]))
            print("Data capture in progress. Press the SPACEBAR to stop.\n")

            open_port(serialPort)
            gather_data(serialPort, logFile, selectedMode, currDevice, fileName)

        serialPort.close()

        if x < len(deviceNames) - 1:
            input("Data capture complete for %s. Connect %s and press ENTER to continue." % (
                currDevice, deviceNames[x + 1]))

print("Data capture complete.\n")
