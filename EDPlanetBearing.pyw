import time, os, json, math, winreg
from tkinter import *
from tkinter import ttk

#Definitions
def callback():
    root.destroy()
    exit()

#Asking Windows Registry for the Saved Folders path.
key = winreg.OpenKey(
    winreg.HKEY_CURRENT_USER,
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
)
dir, type = winreg.QueryValueEx(key, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")

eliteJournalPath = dir + "\\Frontier Developments\\Elite Dangerous\\"
JournalFile = eliteJournalPath + "Status.json"
#print(JournalFile) #Prints the path to the file

CurrentLat = 0.0
CurrentLong = 0.0
CurrentHead = 0
CurrentAlt = 0

#Creates the app window
root = Tk()
root.title("EDPlanetBearing")
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

DestinationCoords = StringVar()
DestHeading = StringVar()

coords_entry = ttk.Entry(mainframe, width=16, justify=CENTER, textvariable=DestinationCoords)
coords_entry.grid(column=1, columnspan=2, row=1, sticky=(W, E))
ttk.Label(mainframe, textvariable=DestHeading, justify=CENTER, font=("Helvetica", 16)).grid(column=2, row=2, sticky=(W, E))

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
coords_entry.focus()
#root.bind('<Return>', calculate)


#Starts infinite loop for testing.
def calculate():
    #Getting the testing destination
    DestinationRaw = (DestinationCoords.get()).replace(","," ")
    Destination = str(DestinationRaw).split()
    print("Typed Coords: " + DestinationCoords.get())
    print("Readable Coords: " + DestinationRaw)
    print("Coords List: " + str(Destination))

    try:
        DstLat = round(float(Destination[0]),4)
        DstLong = round(float(Destination[1]),4)
    except:
        pass

    #Read and store the journal file
    with open(JournalFile, "rt") as in_file:
        JournalContent = in_file.read()

    #Extracting the data from the journal and doing it's magic.
    try:
        Status = json.loads(JournalContent)
        #print(Status)  #Prints the whole Status.json

        CurrentLat = round(Status['Latitude'],4)
        CurrentLong = round(Status['Longitude'],4)
        CurrentHead = round(Status['Heading'],0)
        CurrentAlt = round(Status['Altitude'],0)

        print("Current Lat: " + str(CurrentLat))
        print("Current Long: " + str(CurrentLong))
        print("Current Heading: " + str(CurrentHead))
        print("Current Altitude: " + str(CurrentAlt))
        print("Destination Lat: " + str(DstLat))
        print("Destination Long: " + str(DstLong))

        CurrentLatRad = math.radians(Status['Latitude'])
        CurrentLongRad = math.radians(Status['Longitude'])
        DstLatRad = math.radians(float(Destination[0]))
        DstLongRad = math.radians(float(Destination[1]))

        x = math.cos(CurrentLatRad) * math.sin(DstLatRad) - math.sin(CurrentLatRad) * math.cos(DstLatRad) * math.cos(DstLongRad-CurrentLongRad)
        y = math.sin(DstLongRad-CurrentLongRad) * math.cos(DstLatRad)
        BearingRad = math.atan2(y, x)
        BearingDeg = math.degrees(BearingRad) # * 180 / math.pi
        Bearing = int((BearingDeg + 360) % 360)

        print("Bearing: " + str(Bearing) + "°")
        DestHeading.set(str(Bearing) + "°")

        print("_" * 20)
    except:
        pass
    finally:
        root.after(1000, calculate)
root.after(1000, calculate)


#Creating window parameters
w = 118 # width for the Tk root
h = 80 # height for the Tk root
# get screen width and height
ws = root.winfo_screenwidth() # width of the screen
hs = root.winfo_screenheight() # height of the screen

# calculate x and y coordinates for the Tk root window
x = (ws/2) - (w/2)
y = (hs/25) - (h/2)

# set the dimensions of the screen
# and where it is placed
root.geometry('%dx%d+%d+%d' % (w, h, x, y))

root.protocol("WM_DELETE_WINDOW", callback)
root.wm_attributes('-toolwindow', True)
root.attributes("-topmost", True)
root.mainloop()
