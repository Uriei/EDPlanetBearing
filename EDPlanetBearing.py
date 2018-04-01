import json, math, winreg
from tkinter import *
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#Definitions
def callback():
    observer.stop()
    observer.join()
    root.destroy()
    exit()

def resize(root, h):
    #Creating window parameters
    w = 159 # width for the Tk root
    #h = 40 # height for the Tk root
    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/100)# - (h/2)

    # set the dimensions of the screen
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if "Status.json" in event.src_path:
            calculate()


def calculate(event="None"):
    #
    LeftArrow = ""
    RightArrow = ""

    #Getting the testing destination
    DestinationRaw = (DestinationCoords.get()).replace(","," ")
    Destination = str(DestinationRaw).split()
    print("Typed Coords: " + DestinationCoords.get())
    print("Readable Coords: " + DestinationRaw)
    print("Coords List: " + str(Destination))


    try:
        if "Return" in event.keysym:
            DestinationCoords.set(str(Destination[0]) + ", " + str(Destination[1]))
    except:
        pass

    try:
        DstLat = float(Destination[0])
        DstLong = float(Destination[1])
        if DstLat == -0:
            DstLat = 0
    except:
        pass

    #Read and store the journal file
    with open(JournalFile, "rt") as in_file:
        JournalContent = in_file.read()

    #Extracting the data from the journal and doing its magic.
    try:
        Status = json.loads(JournalContent)

        StatusFlags = Status['Flags']

        #Checking if coordinates are relevant or not
        FlagDocked = StatusFlags & 1<<0
        FlagLanded = StatusFlags & 1<<1
        FlagNoCoords = 2097152 - (StatusFlags & (1<<21))

        NoRun = FlagDocked+FlagNoCoords+FlagLanded
        print("Flags:" + str(StatusFlags))
        print("FlagDocked:" + str(FlagDocked))
        print("FlagLanded:" + str(FlagLanded))
        print("FlagNoCoords:" + str(FlagNoCoords))
        print("NoRun:" + str(NoRun))

        try:
            DstLat
            DstLong
            try:
                if NoRun != 0 :
                    print("Coords irrelevant")
                    resize(root, 40)
                else:
                    resize(root, 80)
                    try:

                        CurrentLat = round(Status['Latitude'],4)
                        CurrentLong = round(Status['Longitude'],4)
                        CurrentHead = round(Status['Heading'],0)
                        CurrentAlt = round(Status['Altitude'],0)

                        print("Coords relevant")
                        print("Current Lat: " + str(CurrentLat))
                        print("Current Long: " + str(CurrentLong))
                        print("Current Heading: " + str(CurrentHead))
                        print("Current Altitude: " + str(CurrentAlt))
                        print("Destination Lat: " + str(DstLat))
                        print("Destination Long: " + str(DstLong))

                        CurrentLatRad = math.radians(Status['Latitude'])
                        CurrentLongRad = math.radians(Status['Longitude'])
                        DstLatRad = math.radians(float(DstLat))
                        DstLongRad = math.radians(float(DstLong))

                        x = math.cos(CurrentLatRad) * math.sin(DstLatRad) - math.sin(CurrentLatRad) * math.cos(DstLatRad) * math.cos(DstLongRad-CurrentLongRad)
                        y = math.sin(DstLongRad-CurrentLongRad) * math.cos(DstLatRad)
                        BearingRad = math.atan2(y, x)
                        BearingDeg = math.degrees(BearingRad)
                        Bearing = int((BearingDeg + 360) % 360)

                        Direction = Bearing - CurrentHead

                        #This part is awful to see but does the job
                        #This calculates the amount of arrows to add to each side
                        if Direction > 180:
                            Direction = Direction - 360
                        if Direction < -2 and Direction > -180:
                            LeftArrow = "<"
                            if Direction < -20:
                                LeftArrow = "<<"
                            if Direction < -60:
                                LeftArrow = "<<<"
                        if Direction > 2 and Direction < 180:
                            RightArrow = ">"
                            if Direction > 20:
                                RightArrow = ">>"
                            if Direction > 60:
                                RightArrow = ">>>"
                        if Direction == 180 or Direction == -180:
                            LeftArrow = "<<<"
                            RightArrow = ">>>"

                        print("Direction: " + str(Direction) + "°")
                        print("Bearing: " + str(Bearing) + "°")
                        print(LeftArrow + RightArrow)

                        DestHeading.set(str(Bearing) + "°")
                        DestHeadingL.set(LeftArrow)
                        DestHeadingR.set(RightArrow)
                    except Exception as e:
                        print("E02: " + str(e))
                    print("_" * 20)

            except Exception as e:
                print("E03: " + str(e))
                print("Error on calculation")
        except Exception as e:
            print("E01: " + str(e))
            print("No Destination coords")
            DestHeading.set("")
            DestHeadingL.set("")
            DestHeadingR.set("")
            resize(root, 40)
    except Exception as e:
        print("E04: " + str(e))


#Asking Windows Registry for the Saved Folders path.
key = winreg.OpenKey(
    winreg.HKEY_CURRENT_USER,
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
)
dir, type = winreg.QueryValueEx(key, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")

eliteJournalPath = dir + "\\Frontier Developments\\Elite Dangerous\\"
JournalFile = eliteJournalPath + "Status.json"

#watchdog
event_handler = MyHandler()
observer = Observer()
observer.schedule(event_handler, path=eliteJournalPath, recursive=False)
observer.start()

#
CurrentLat = 0.0
CurrentLong = 0.0
CurrentHead = 0
CurrentAlt = 0


#Creates the app window
root = Tk()
style = ttk.Style()

style.theme_create("EDBearing", parent="clam", settings=None)

style.theme_settings("EDBearing", {
    "TFrame": {
        "map": {
            "background":       [("active", "black"),
                                ("!disabled", "black")],
            "fieldbackground":  [("!disabled", "black")],
            "foreground":       [("focus", "black"),
                                ("!disabled", "black")]
            }
    },
    "TLabel": {
        "map": {
            "background":       [("active", "black"),
                                ("!disabled", "black")],
            "fieldbackground":  [("!disabled", "black")],
            "foreground":       [("focus", "orange"),
                                ("!disabled", "orange")]
        }
    },
    "TEntry": {
        "configure":            {"insertbackground": "orange"},
        "map": {
            "fieldbackground":  [("focus", "white"),
                                ("!disabled", "black")],
            "foreground":       [("focus", "black"),
                                ("!disabled", "orange")]
        }
    },
    "TButton": {
        "map": {
            "background":       [("active", "black"),
                                ("!disabled", "black")],
            "foreground":       [("focus", "orange"),
                                ("!disabled", "orange")]
        }
    }
})

DestinationCoords = StringVar()
DestHeading = StringVar()
DestHeadingR = StringVar()
DestHeadingL = StringVar()

style.theme_use("EDBearing")
root.title("EDPlanetBearing")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

#Testing Window movement
def dragwin(event):
    x = mainframe.winfo_pointerx() - offsetx
    y = mainframe.winfo_pointery() - offsety
    root.geometry('+{x}+{y}'.format(x=x,y=y))

def clickwin(event):
    offsetx = event.x
    offsety = event.y
offsetx = 0
offsety = 0
mainframe.bind('<ButtonPress-1>',clickwin)
mainframe.bind('<B1-Motion>',dragwin)

coords_entry = ttk.Entry(mainframe, width=18, justify=CENTER, textvariable=DestinationCoords)
coords_entry.grid(column=1, columnspan=8, row=1, sticky=(W, E))
coords_entry.focus()
coords_entry.bind("<Return>", calculate)

ttk.Label(mainframe, textvariable=DestHeading, justify=CENTER, font=("Helvetica", 16)).grid(column=4, columnspan=6, row=2, sticky=(W, E))
ttk.Label(mainframe, textvariable=DestHeadingL, justify=CENTER, font=("Helvetica", 14)).grid(column=1, columnspan=3, row=2, sticky=(E))
ttk.Label(mainframe, textvariable=DestHeadingR, justify=CENTER, font=("Helvetica", 14)).grid(column=8, columnspan=2, row=2, sticky=(W))

CloseB = ttk.Button(mainframe, text=" X ", command=callback)
CloseB.grid(column=9, row=1, sticky=(E))

resize(root, 37)

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
root.protocol("WM_DELETE_WINDOW", callback)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.mainloop()
