import json, math, winreg, os
from tkinter import *
from tkinter import ttk
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from urllib.request import urlopen

#Definitions
def callback():
    observer.stop()
    observer.join()
    root.destroy()
    exit()

def dragwin(event):
    x = mainframe.winfo_pointerx() - offsetx
    y = mainframe.winfo_pointery() - offsety
    root.geometry('+{x}+{y}'.format(x=x,y=y))
def clickwin(event):
    global offsetx
    global offsety
    offsetx = event.x
    offsety = event.y

def resize(root, InfoHudLevel, StartingUp=False):
    #Creating window parameters
    w = 159 # width for the Tk root
    #h = 40 # height for the Tk root
    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen
    if InfoHudLevel == 2:
        h = 100
    elif InfoHudLevel == 1:
        h = 80
    else:
        h = 37

    try:
        if StartingUp:
            # calculate x and y coordinates for the Tk root window
            x = (ws/2) - (w/2)
            y = (hs/100)# - (h/2)
        else:
            x = root.winfo_rootx()
            y = root.winfo_rooty()

        # set the dimensions of the screen
        # and where it is placed
        root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    except Exception as e:
        print("E05: " + str(e))
        print("Error on resizing")

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)
        self.tw.attributes("-topmost", True)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class JournalUpdate(FileSystemEventHandler):
    def on_modified(self, event):
        print("Detected change in: " + event.src_path)
        global Body
        global StarSystem
        global BodyRadius
        try:
            JournalList = reversed(os.listdir(eliteJournalPath))
            for JournalItemFolder in JournalList:
                if "Journal." in JournalItemFolder:
                    print(JournalItemFolder)
                    JournalItemFile = eliteJournalPath + JournalItemFolder
                    with open(JournalItemFile) as f:
                        JContent = reversed(f.readlines())
                    for JEntry in JContent:
                        JEvent = json.loads(JEntry)
                        if "ApproachBody" == JEvent['event'] or "Location" == JEvent['event']:
                            StarSystem = JEvent['StarSystem']
                            if Body == JEvent['Body']:
                                raise Exception("Same body, preventing extra polls to EDSM")
                                break
                            Body = JEvent['Body']
                            break
                    try:
                        EDSMraw = urlopen("https://www.edsm.net/api-system-v1/bodies?systemName=" + StarSystem).read()
                        EDSMSystem = json.loads(EDSMraw)
                        EDSMBodies = EDSMSystem['bodies']
                        for BodyNameRaw in EDSMBodies:
                            if BodyNameRaw['name'] == Body:
                                BodyRadius = BodyNameRaw['radius'] * 1000
                                print("Radius of "+Body+" is: "+str(BodyRadius)+" meters")
                    except Exception as e:
                        print("E.EDSM: "+str(e))
                    break
        except Exception as e:
            print("E.Journal read and parse: "+str(e))
        calculate()

def calculate(event="None"):
    #
    LeftArrow = ""
    RightArrow = ""
    global InfoHudLevel

    #Getting the testing destination
    DestinationRaw = (DestinationCoords.get()).replace(","," ")
    Destination = str(DestinationRaw).split()
    print("Typed Coords: " + DestinationCoords.get())
    print("Readable Coords: " + DestinationRaw)
    print("Coords List: " + str(Destination))


    try:
        DstLat = float(Destination[0])
        DstLong = float(Destination[1])
        if DstLat == -0:
            DstLat = 0.0
    except:
        pass

    try:
        if "Return" in event.keysym:
            DestinationCoords.set(str(DstLat) + ", " + str(DstLong))
    except:
        pass

    #Read and store the journal file
    with open(JournalFile, "rt") as in_file:
        JStatusContent = in_file.read()

    #Extracting the data from the journal and doing its magic.
    try:
        Status = json.loads(JStatusContent)

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
                    resize(root, 0)
                else:
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

                        CurrentLatDeg = Status['Latitude']
                        CurrentLongDeg = Status['Longitude']

                        CurrentLatRad = math.radians(CurrentLatDeg)
                        CurrentLongRad = math.radians(CurrentLongDeg)
                        DstLatRad = math.radians(float(DstLat))
                        DstLongRad = math.radians(float(DstLong))

                        x = math.cos(CurrentLatRad) * math.sin(DstLatRad) - math.sin(CurrentLatRad) * math.cos(DstLatRad) * math.cos(DstLongRad-CurrentLongRad)
                        y = math.sin(DstLongRad-CurrentLongRad) * math.cos(DstLatRad)
                        BearingRad = math.atan2(y, x)
                        BearingDeg = math.degrees(BearingRad)
                        Bearing = int((BearingDeg + 360) % 360)

                        #Direction = Bearing - CurrentHead

                        #This part is awful to see but does the job
                        #This calculates the amount of arrows to add to each side

                        if CurrentHead < Bearing:
                            CurrentHead += 360  # denormalize ...

                        Direction = CurrentHead - Bearing   # calculate left turn, will allways be 0..359
                        print("DirectionB: " + str(Direction) + "°")

                        # take the smallest turn
                        if Direction <= 1 or Direction >= 359:
                            print("Going Forward")
                            LeftArrow = ""
                            RightArrow = ""
                        elif Direction < 180:
                            # Turn left : Direction degrees
                            print("Going Left")
                            LeftArrow = "<"
                            if Direction >= 30:
                                LeftArrow = "<<"
                            if Direction >= 90:
                                LeftArrow = "<<<"
                        elif Direction > 180:
                            # Turn right : 360-Direction degrees
                            print("Going Right")
                            Direction = 360 - Direction
                            RightArrow = ">"
                            if Direction >= 30:
                                RightArrow = ">>"
                            if Direction >= 90:
                                RightArrow = ">>>"
                        else:
                            print("Going Backwards")
                            LeftArrow = "<<<"
                            RightArrow = ">>>"

                        print("DirectionA: " + str(Direction) + "°")
                        print("Bearing: " + str(Bearing) + "°")
                        print(LeftArrow + RightArrow)
                        InfoHudLevel = 1

                        #Calculate distance
                        if BodyRadius > 0:
                            DifLat = math.radians(DstLat - CurrentLatDeg)
                            DifLong = math.radians(DstLong - CurrentLongDeg)

                            Dis1 = math.sin(DifLat / 2)**2 + math.cos(CurrentLatRad) * math.cos(DstLatRad) * math.sin(DifLong / 2)**2
                            Dis2 = 2 * math.atan2(math.sqrt(Dis1), math.sqrt(1-Dis1))
                            Distance = int(BodyRadius * Dis2)

                            InfoHudLevel = 2
                            if Distance >= 100000:
                                Distance = int(Distance / 1000)
                                DisScale = "km"
                            else:
                                DisScale = "m"
                            Distance = format(Distance, ',d')
                            DestDistance.set(str(Distance)+" "+DisScale)

                        #Updating indicators
                        DestHeading.set(str(Bearing) + "°")
                        DestHeadingL.set(LeftArrow)
                        DestHeadingR.set(RightArrow)
                        resize(root, InfoHudLevel)
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
            resize(root, 0)
    except Exception as e:
        print("E04: " + str(e))

#Declaring variables
CurrentLat = 0.0
CurrentLong = 0.0
CurrentHead = 0
CurrentAlt = 0
offsetx = 0
offsety = 0
StarSystem = ""
Body = ""
BodyRadius = 0
InfoHudLevel = 0

#Asking Windows Registry for the Saved Folders path.
try:
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    )
    dir, type = winreg.QueryValueEx(key, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")

    eliteJournalPath = dir + "\\Frontier Developments\\Elite Dangerous\\"
    JournalFile = eliteJournalPath + "Status.json"

    #watchdog
    event_handler = JournalUpdate()
    observer = Observer()
    observer.schedule(event_handler, path=eliteJournalPath, recursive=False)
    observer.start()
except:
    pass

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
DestDistance = StringVar()

style.theme_use("EDBearing")
root.title("EDPlanetBearing")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

mainframe.bind('<ButtonPress-1>',clickwin)
mainframe.bind('<B1-Motion>',dragwin)

coords_entry = ttk.Entry(mainframe, width=18, justify=CENTER, textvariable=DestinationCoords)
coords_entry.grid(column=1, columnspan=8, row=1, sticky=(W, E))
coords_entry.focus()
coords_entry.bind("<Return>", calculate)

ttk.Label(mainframe, textvariable=DestHeading, justify=CENTER, font=("Helvetica", 16)).grid(column=4, columnspan=6, row=2, sticky=(W, E))
ttk.Label(mainframe, textvariable=DestHeadingL, justify=CENTER, font=("Helvetica", 14)).grid(column=1, columnspan=3, row=2, sticky=(E))
ttk.Label(mainframe, textvariable=DestHeadingR, justify=CENTER, font=("Helvetica", 14)).grid(column=8, columnspan=2, row=2, sticky=(W))

ttk.Label(mainframe, textvariable=DestDistance, justify=CENTER, font=("Helvetica", 8)).grid(column=4, columnspan=7, row=3, sticky=(N, W, E))

CloseB = ttk.Button(mainframe, text=" X ", command=callback)
CloseB.grid(column=9, row=1, sticky=(E))

resize(root, 0, True)

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

#Add Tooltips
CloseB_ttp = CreateToolTip(CloseB, 'Close')
coords_entry_ttp = CreateToolTip(coords_entry, 'Type destination coordinates')

root.protocol("WM_DELETE_WINDOW", callback)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.mainloop()
