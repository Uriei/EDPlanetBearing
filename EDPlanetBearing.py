import json, math, winreg, os, win32gui, re, random, datetime, time, errno
from tkinter import *
from tkinter import ttk
import tkinter as tk
from sys import argv, exit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from urllib.request import urlopen
from openal.audio import SoundSink, SoundSource
from openal.loaders import load_wav_file

def AddLogEntry(LogEntry): #Adds an entry to the log file.
    global EDPBAppdata
    global DebugMode
    try:
        if DebugMode:
            LogFile = EDPBAppdata + str(datetime.datetime.now().year) + "-" + str(datetime.datetime.now().month) + "-" + str(datetime.datetime.now().day) + ".txt"
            EntryLog = str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute) + ":" + str(datetime.datetime.now().second) + "." + str(datetime.datetime.now().microsecond) + " - " + str(LogEntry)
            with open(LogFile,"a") as f:
                f.write(EntryLog + "\n")
            print("Entry Log added: " + EntryLog)
    except Exception as e:
        print("Log failed: " + str(e))

def ClearFiles(File="All"):
    global EDPBConfigFile
    global EDPBLock
    for x in range(0, 100):
        try:
            try:
                if File == "SessionFile" or File == "All":
                    os.remove(EDPBLock)
                    print("Deleted: " + EDPBLock)
            except OSError as e:
                print(e)
                AddLogEntry(e)
                if e.errno != errno.ENOENT:
                    raise
            try:
                if File == "ConfigFile" or File == "All":
                    os.remove(EDPBConfigFile)
                    print("Deleted: " + EDPBConfigFile)
            except OSError as e:
                print(e)
                AddLogEntry(e)
                if e.errno != errno.ENOENT:
                    raise
            print("Succesfully deleted files")
            break
        except OSError as e:
            AddLogEntry(e)
            if e.errno != errno.ENOENT:
                raise
        except:
            print("E.Deleting files")
            AddLogEntry("Deleting files")
            time.sleep(0.01)

def callback(ClearLock=True,ClearConfig=True): #Clean files and close the app.
    if ClearLock and ClearConfig:
        ClearFiles("All")
    elif ClearLock:
        ClearFiles("SessionFile")
    elif ClearConfig:
        ClearFiles("ConfigFile")

    try:
        observer.stop()
        observer.join()
        root.destroy()
        exit()
    except Exception as e:
        AddLogEntry(e)
        exit()

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

def SingleInstance(FirstRun=False):
    global EDPBLock
    global SessionID
    try:
        if FirstRun:
            try:
                SessionID = str(random.randrange(0, 1000000000))
                with open(EDPBLock,"w") as f:
                    f.write(SessionID)
                print("Session ID: " + SessionID)
                root.after(1000,SingleInstance)
            except Exception as e: # Guard against race condition
                print("E.Creating SessionLock file: " + str(e))
                AddLogEntry(e)
                callback()
        elif not os.path.exists(EDPBLock):
            print("SessionLock file missing, closing.")
            callback()
        else:
            try:
                with open(EDPBLock) as f:
                    EDPBLockID = f.read()
                if EDPBLockID != SessionID:
                    print("New session ID detected, closing instance.")
                    callback(False,False)
                else:
                    root.after(1000,SingleInstance)
            except Exception as e: # Guard against race condition
                print("E.Checking Session Lock: " + str(e))
                AddLogEntry(e)
                callback(False)

    except Exception as e:
        print("E.Single Instancing: " + str(e))
        AddLogEntry(e)

def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        try:
            if argv[0][0] == "+":  # Found a "-name value" pair.
                opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        except:
            pass
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts

class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""

    def __init__ (self):
        """Constructor"""
        self._handle = None

    def find_window(self, class_name, window_name=None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

def FocusElite():
    try:
        w = WindowMgr()
        w.find_window("FrontierDevelopmentsAppWinClass")
        w.set_foreground()
    except:
        pass

def dragwin(event):
    x = mainframe.winfo_pointerx() - offsetx
    y = mainframe.winfo_pointery() - offsety
    root.geometry("+{x}+{y}".format(x=x,y=y))
def clickwin(event):
    global offsetx
    global offsety
    offsetx = event.x
    offsety = event.y

def resize(root, InfoHudLevel=0, StartingUp=False):
    #Creating window parameters
    w = 185 # width for the Tk root
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
            # Calculate x and y coordinates for the Tk root window
            x = (ws/2) - (w/2)
            y = (hs/100)# - (h/2)
            root.after(100, JournalUpdate.on_modified, JournalUpdate, "Startup")
        else:
            x = root.winfo_rootx()
            y = root.winfo_rooty()

        # set the dimensions of the screen
        # and where it is placed
        root.geometry("%dx%d+%d+%d" % (w, h, x, y))
    except Exception as e:
        print("E05: " + str(e))
        AddLogEntry(e)
        print("Error on resizing")

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text="widget info"):
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
        label = tk.Label(self.tw, text=self.text, justify="left",
                       background="#ffffff", relief="solid", borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)
        self.tw.attributes("-topmost", True)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class ReadJournalFile:
    def Status():
        global StatusFile
        global NoRun
        global FlagSRV
        global CurrentLatDeg
        global CurrentLongDeg
        global CurrentHead
        global CurrentAlt

        with open(StatusFile) as f:
            JStatusContent = f.read()

        try:
            Status = json.loads(JStatusContent)
            StatusFlags = Status["Flags"]

            FlagDocked = StatusFlags & 1<<0 # If ship is docked
            FlagLanded = StatusFlags & 1<<1 # If ship is landed
            FlagSRV = StatusFlags & (1<<26) # If driving SRV
            FlagNoCoords = 2097152 - (StatusFlags & (1<<21)) # If coordinates are not available
            NoRun = FlagDocked+FlagLanded+FlagNoCoords

            print("Flags: " + str(StatusFlags))
            print("FlagDocked: " + str(FlagDocked))
            print("FlagLanded: " + str(FlagLanded))
            print("FlagNoCoords: " + str(FlagNoCoords))
            print("FlagSRV: " + str(FlagSRV))
            print("NoRun: " + str(NoRun))

            CurrentLatDeg = round(Status["Latitude"],4)
            CurrentLongDeg = round(Status["Longitude"],4)
            CurrentHead = round(Status["Heading"],0)
            CurrentAlt = round(Status["Altitude"],0)
            print("Current Lat: " + str(CurrentLatDeg))
            print("Current Long: " + str(CurrentLongDeg))
            print("Current Heading: " + str(CurrentHead))
            print("Current Altitude: " + str(CurrentAlt))
        except Exception as e:
            print("Couldn't read Status.json file: " + str(e))
            AddLogEntry(e)

    def Journal():
        global eliteJournalPath
        global Body
        global StarSystem
        global BodyRadius
        JournalDone = False

        try:
            Body
        except:
            Body = 'Not set'
        try:
            StarSystem
        except:
            StarSystem = 'Not set'

        try:
            JournalList = reversed(os.listdir(eliteJournalPath))
            for JournalItemFolder in JournalList:
                if JournalDone:
                    break
                if "Journal." in JournalItemFolder:
                    print("Reading Journal: " + JournalItemFolder)
                    JournalItemFile = eliteJournalPath + JournalItemFolder
                    with open(JournalItemFile) as f:
                        JContent = reversed(f.readlines())
                    for JEntry in JContent:
                        JEvent = json.loads(JEntry)
                        if "ApproachBody" == JEvent["event"] or "Location" == JEvent["event"]:
                            if Body == JEvent["Body"]:
                                raise Exception("SameBody")
                            else:
                                StarSystem = JEvent["StarSystem"]
                                Body = JEvent["Body"]
                                JournalDone = True
                                break
            try:
                if StarSystem != "Not set" and Body != "Not set":
                    BodyRadius = 0
                    EDSMraw = urlopen("https://www.edsm.net/api-system-v1/bodies?systemName=" + StarSystem).read()
                    print("Extracted data from " + StarSystem)
                    EDSMSystem = json.loads(EDSMraw)
                    EDSMBodies = EDSMSystem["bodies"]
                    for BodyNameRaw in EDSMBodies:
                        if BodyNameRaw["name"] == Body:
                            BodyRadius = BodyNameRaw["radius"] * 1000
                            print("Radius of "+Body+" is: "+str(BodyRadius)+" meters")
                            break
            except Exception as e:
                print("E.EDSM: "+str(e))
                AddLogEntry(e)
        except Exception as e:
            if str(e) == 'SameBody':
                print("Same body, preventing extra polls to EDSM")
            else:
                print("Failed Journal reading.")
                AddLogEntry(e)

class JournalUpdate(FileSystemEventHandler):
    def on_modified(self, event):
        ReadJournalFile.Journal()
        ReadJournalFile.Status()
        Calculate()

def CreateGUI(root):
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
                                    ("disabled", "black"),
                                    ("!disabled", "black")],
                "foreground":       [("focus", "black"),
                                    ("disabled", "orange"),
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
        },
        "TCheckbutton": {
            "map": {
                "background":       [("active", "black"),
                                    ("disabled", "black"),
                                    ("!disabled", "black")],
                "foreground":       [("focus", "orange"),
                                    ("disabled", "orange"),
                                    ("!disabled", "orange")]
            }
        }
    })

    global DestinationCoords
    global DestHeading
    global DestHeadingD
    global DestHeadingR
    global DestHeadingL
    global DestDistance

    DestinationCoords = StringVar()
    DestHeading = StringVar()
    DestHeadingD = StringVar()
    DestHeadingR = StringVar()
    DestHeadingL = StringVar()
    DestDistance = StringVar()

    style.theme_use("EDBearing")
    root.title("EDPlanetBearing")

    global mainframe
    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    mainframe.bind("<ButtonPress-1>",clickwin)
    mainframe.bind("<B1-Motion>",dragwin)

    global coords_entry
    coords_entry = ttk.Entry(mainframe, width=18, justify=CENTER, textvariable=DestinationCoords)
    coords_entry.grid(column=2, columnspan=8, row=1, sticky=(W, E))
    coords_entry.focus()
    coords_entry.bind("<Return>", Calculate)

    ttk.Label(mainframe, textvariable=DestHeading, justify=CENTER, font=("Helvetica", 16)).grid(column=5, columnspan=6, row=2, sticky=(W, E))
    ttk.Label(mainframe, textvariable=DestHeadingL, justify=CENTER, font=("Helvetica", 14)).grid(column=2, columnspan=3, row=2, sticky=(E))
    ttk.Label(mainframe, textvariable=DestHeadingR, justify=CENTER, font=("Helvetica", 14)).grid(column=9, columnspan=2, row=2, sticky=(W))

    global DestHeadingD_Lab
    DestHeadingD_Lab = ttk.Label(mainframe, textvariable=DestHeadingD, justify=RIGHT, font=("Helvetica", 10))
    DestHeadingD_Lab.grid(column=8, columnspan=4, row=3, sticky=(E))

    global DestDistance_Lab
    DestDistance_Lab = ttk.Label(mainframe, textvariable=DestDistance, justify=CENTER, font=("Helvetica", 9))
    DestDistance_Lab.grid(column=5, columnspan=7, row=3, sticky=(N, W, E))

    CloseB = ttk.Button(mainframe, text=" X ", command=callback)
    CloseB.grid(column=10, row=1, sticky=(E))

    global PingCB
    PingCB = ttk.Button(mainframe, image=BMPingAudio0, command=AudioFeedBack.PingCycleMode)
    PingCB.grid(column=1, row=1, sticky=(E))

    resize(root, InfoHudLevel, True)

    for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

    root.protocol("WM_DELETE_WINDOW", callback)
    root.attributes("-topmost", True)
    root.overrideredirect(True)

def GetShellFolders():
    global eliteJournalPath
    global EDPBAppdata
    global StatusFile
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        JournalDir, type = winreg.QueryValueEx(key, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")

        eliteJournalPath = JournalDir + "\\Frontier Developments\\Elite Dangerous\\"
        LAppdatDdir, type = winreg.QueryValueEx(key, "Local AppData")
        EDPBAppdata = LAppdatDdir + "\\EDPlanetBearing\\"
        StatusFile = eliteJournalPath + "Status.json"
    except Exception as e:
        print("E.Getting Journal Path" + str(e))
        AddLogEntry("Getting Journal Path" + str(e))
        root.after(0,callback)

class AudioFeedBack:
    def Start():
        #Prepare audio feedback
        try:
            global sink
            global source
            global data
            global PingDelay
            global PingPosX
            global PingPosZ
            global PingPitch
            sound_beep = "beep.wav" #Default sound file
            PingDelay = 1500
            PingPosX = 0.0
            PingPosZ = 0.0
            PingPitch = 1.0

            sink = SoundSink()
            sink.activate()
            source = SoundSource(position=[PingPosX, 0, PingPosZ])
            #source.looping = False
            source.gain = 50.0
            data = load_wav_file(sound_beep)
            sink.play(source)
            print("Audio system started")
        except Exception as e:
            print("E.Starting Audio: " + str(e))
            AddLogEntry(e)
    def PingLoop():
        global PingDelay
        global PingPosX
        global PingPosZ
        global PingPitch
        global InfoHudLevel
        global sink
        global source
        global data
        global AudioMode
        global DirectionOverMargin
        try:
            if InfoHudLevel != 0:
                if (AudioMode  == 1 and DirectionOverMargin) or AudioMode  == 2:
                    source.position = [PingPosX, source.position[1], PingPosZ]
                    source.pitch = PingPitch
                    source.queue(data)
                    sink.update()
                    print("Ping at: " + str(source.position))
        except Exception as e:
            print("E.Playing Audio(Loop): " + str(e))
            AddLogEntry(e)
        finally:
            root.after(PingDelay,AudioFeedBack.PingLoop)
    def DestinationReached():
        try:
            global PingPitch
            global InfoHudLevel
            global sink
            global source
            global data
            global AudioMode
            global DirectionOverMargin

            PingPosX = 0.0
            PingPosZ = 0.0
            PingPitch = 1.5

            if InfoHudLevel != 0:
                if AudioMode  != 0:
                    AudioFeedBack.PingCycleMode(0)
                    source.bufferqueue = [] #Clear any previously queued sound
                    sink.update()
                    source.position = [0.0, source.position[1], 0.0]
                    source.pitch = PingPitch
                    source.queue(data)
                    source.queue(data)
                    source.queue(data)
                    print("Triple Ping at: " + str(source.position))
                    sink.update()
        except Exception as e:
            print("E.Playing Audio(Reached): " + str(e))
            AddLogEntry(e)
        finally:
            if UsingConfigFile:
                root.after(0,callback)


    def PingCycleMode(AudioModeSet = -1):
        global AudioMode
        try:
            if AudioModeSet != -1:
                AudioMode = AudioModeSet
            elif AudioMode == 2:
                AudioMode = 0
            else:
                AudioMode = AudioMode + 1
            exec('PingCB["image"] = BMPingAudio' + str(AudioMode))
            coords_entry.focus()
            print("Audio Mode set to: " + str(AudioMode) + " - " + str(PingCB["image"]))
        except Exception as e:
            print("E.Setting Audio Feedback image: " + str(e))
            AddLogEntry(e)

def GetCLArguments(argv=argv):
    try:
        myargs = getopts(argv)
        if "+debug" in argv:
            global DebugMode
            DebugMode = True
        if "+close" in argv:
            root.after(0,callback)
        if "+lat" in myargs and "+long" in myargs:
            ArgLat = myargs["+lat"]
            ArgLong = myargs["+long"]
            DestinationCoords.set(str(ArgLat) + ", " + str(ArgLong))
            root.after(250,FocusElite)
            ClearFiles("ConfigFile")
        if "+audio" in myargs:
            AudioFeedBack.PingCycleMode(int(myargs["+audio"]))
    except Exception as e:
        print (e)
        AddLogEntry(e)

def GetConfigFromFile(Startup=False): #Gets config from config file if exists and applies it
    global EDPBConfigFile
    global AudioMode
    global InfoHudLevel
    global UsingConfigFile
    global EDPBConfigContentPrevious
    try:
        EDPBConfigContentPrevious
    except:
        EDPBConfigContentPrevious = ''

    if os.path.exists(EDPBConfigFile):
        try:
            with open(EDPBConfigFile) as f:
                EDPBConfigContent = f.read().lower()
            if EDPBConfigContentPrevious == EDPBConfigContent:
                raise Exception('SameConfig')
            if "close" in EDPBConfigContent:
                callback()
            Configs = json.loads(EDPBConfigContent)
            try:
                DstLat = float(Configs["lat"])
                DstLong = float(Configs["long"])
            except:
                print("E.Couldn't load coords from existing config file.")
                AddLogEntry("E.Couldn't load coords from existing config file.")
                InfoHudLevel = 0
                resize(root, InfoHudLevel)
                DestinationCoords.set("")
                AudioFeedBack.PingCycleMode(0)
                root.after(500, Calculate)
                try:
                    os.remove(EDPBConfigFile)
                except:
                    print("E.Deleting empty config file")
                    AddLogEntry("Deleting empty config file")
                raise

            try:
                AudioFeedBack.PingCycleMode(int(Configs["audio"]))
                UsingConfigFile = True
            except:
                pass
            if DstLat == -0:
                DstLat = 0.0

            DestinationCoords.set(str(DstLat) + ", " + str(DstLong))

            EDPBConfigContentPrevious = EDPBConfigContent

            if Startup:
                root.after(100, FocusElite)
                root.after(150, Calculate)
            elif InfoHudLevel == 0:
                root.after(0, Calculate)
            #Disable GUI
            if str(coords_entry["state"]) == "normal":
                coords_entry["state"] = "disabled"
                print("GUI Disabled")
        except Exception as e:
            if str(e) == 'SameConfig':
                pass
            else:
                print("E.Reading Config file: " + str(e))
                AddLogEntry(e)
                if str(coords_entry["state"]) != "normal":
                    coords_entry["state"] = "normal"
                    print("GUI Enabled")
            EDPBConfigContentPrevious = EDPBConfigContent
    else:
        if str(coords_entry["state"]) != "normal":
            coords_entry["state"] = "normal"
            EDPBConfigContentPrevious = ''
            print("GUI Enabled")
    root.after(2000, GetConfigFromFile)

def Calculate(event="None"):
    global NoRun
    global DstLat
    global DstLong
    global InfoHudLevel
    DestinationRaw = (DestinationCoords.get()).replace(","," ")
    Destination = str(DestinationRaw).split()
    try:
        DstLat = float(Destination[0])
        DstLong = float(Destination[1])
        if DstLat == -0:
            DstLat = 0.0
    except:
        NoRun = -1
        print("Destination missing")
    try:
        if "Return" in event.keysym:
            DestinationCoords.set(str(DstLat) + ", " + str(DstLong))
            ReadJournalFile.Status()
            Calculate()
            FocusElite()
    except:
        pass

    if NoRun != 0:
        print("Coords irrelevant")
        InfoHudLevel = 0
    else:
        print("Coords relevant")
        CalcHeading()
        CalcDArrows()
        CalcDistance()
        CalcAngDesc()
    resize(root, InfoHudLevel)

def CalcHeading():
    global CurrentLatDeg
    global CurrentLongDeg
    global DstLat
    global DstLong
    global Bearing
    global InfoHudLevel
    try:
        CurrentLatRad = math.radians(CurrentLatDeg)
        CurrentLongRad = math.radians(CurrentLongDeg)
        DstLatRad = math.radians(float(DstLat))
        DstLongRad = math.radians(float(DstLong))

        x = math.cos(CurrentLatRad) * math.sin(DstLatRad) - math.sin(CurrentLatRad) * math.cos(DstLatRad) * math.cos(DstLongRad-CurrentLongRad)
        y = math.sin(DstLongRad-CurrentLongRad) * math.cos(DstLatRad)
        BearingRad = math.atan2(y, x)
        BearingDeg = math.degrees(BearingRad)
        Bearing = int((BearingDeg + 360) % 360)
        DestHeading.set(str(Bearing) + "°")
        InfoHudLevel = 1
    except Exception as e:
        AddLogEntry("CalcHeading(): " + str(e))

def CalcDArrows():
    global Bearing
    global CurrentHead
    global PingPosX
    global PingPosZ
    global PingPitch
    global DirectionOverMargin
    global InfoHudLevel
    try:
        if CurrentHead < Bearing:
            CurrentHead += 360  # denormalize ...
        DirectionRaw = CurrentHead - Bearing   # Calculate left turn, will allways be 0..359
        Direction = DirectionRaw
        print("DirectionRaw: " + str(DirectionRaw) + "°")
        LeftArrow = ""
        RightArrow = ""
        # take the smallest turn
        if Direction <= 1 or Direction >= 359:
            print("Going Forward")
            if Direction > 180:
                Direction = 360 - Direction
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
        DestHeadingL.set(LeftArrow)
        DestHeadingR.set(RightArrow)

        #Setting 3D position of the beep source
        PingPosX = math.sin(math.radians(-DirectionRaw))*50
        PingPosZ = math.cos(math.radians(-DirectionRaw))*50
        PingPitch = 1.0 - (Direction / 360)

        print("PingPosX: " + str(PingPosX))
        print("PingPosZ: " + str(PingPosZ))
        print("PingPitch: " + str(PingPitch))

        AlertMargin = 45
        if AlertMargin < Direction:
            DirectionOverMargin = True
            print("Over 45º")
        else:
            DirectionOverMargin = False
            print("Not over 45º")

    except Exception as e:
        AddLogEntry("CalcDArrows(): " + str(e))

def CalcDistance():
    global BodyRadius
    global CurrentLatDeg
    global CurrentLongDeg
    global DstLat
    global DstLong
    global CurrentAlt
    global FlagSRV
    global Distance_meters
    global InfoHudLevel
    try:
        if BodyRadius > 0:
            #Distance
            DifLat = math.radians(DstLat - CurrentLatDeg)
            DifLong = math.radians(DstLong - CurrentLongDeg)

            Dis1 = math.sin(DifLat / 2)**2 + math.cos(math.radians(CurrentLatDeg)) * math.cos(math.radians(float(DstLat))) * math.sin(DifLong / 2)**2
            Dis2 = 2 * math.atan2(math.sqrt(Dis1), math.sqrt(1-Dis1))
            Distance_Surface = int(BodyRadius * Dis2)
            Distance_meters = int(sqrt(Distance_Surface**2 + CurrentAlt**2))

            if Distance_meters >= 100000:
                Distance = int(Distance_meters / 1000)
                DisScale = "km"
            else:
                Distance = Distance_meters
                DisScale = "m"
            Distance = format(Distance, ",d")
            DestDistance.set(str(Distance)+" "+DisScale)

            InfoHudLevel = 2

            try:
                if (Distance_meters < 2000 and FlagSRV == 0) or (Distance_meters < 250 and FlagSRV != 0):
                    AudioFeedBack.DestinationReached()
            except:
                print("E.Shutting when destination is reached")
            print("Distance in meters: " + str(Distance_meters))
        else:
            try:
                if (DstLat - CurrentLatDeg < 0.01 and DstLong - CurrentLongDeg < 0.01):
                    AudioFeedBack.DestinationReached()
            except:
                print("E.Shutting when destination is reached")
    except Exception as e:
        AddLogEntry("CalcDistance(): " + str(e))

def CalcAngDesc(): #Angle of descent
    global DescentAngle
    global CurrentAlt
    global Distance_meters
    global FlagSRV
    try:
        DescentAngle = - int(math.degrees(math.atan(CurrentAlt/Distance_meters)))
        print("Angle of Descent: " + str(DescentAngle))
        if DescentAngle <= 0 and Distance_meters < 1000000 and FlagSRV == 0 and CurrentAlt > 3000:
            DestHeadingD.set(str(DescentAngle) + "°")
            DestDistance_Lab.grid(column=3, columnspan=7, row=3, sticky=(N, W, E))
            DestHeadingD_Lab.config(foreground="orange")
            if DescentAngle <= -60 or DescentAngle > -5 :
                DestDistance_Lab.grid(column=3, columnspan=7, row=3, sticky=(N, W, E))
                DestHeadingD_Lab.config(foreground="red")
        else:
            DestHeadingD.set("")
    except Exception as e:
        AddLogEntry("CalcAngDesc(): " + str(e))

if __name__ == "__main__":
    root = Tk()
    style = ttk.Style()

    DebugMode = True    #Temporary variables for testing

    GetShellFolders()
    GetCLArguments()

    #Temporary variables for testing
    EDPBLock = EDPBAppdata + "Session.lock"
    EDPBConfigFile = EDPBAppdata + "Config.json"
    InfoHudLevel = 0
    AudioMode = 0
    data_dir = 'GFX'
    BMPingAudio0 = PhotoImage(file=resource_path(os.path.join(data_dir, "BMPingAudio0.png")))
    BMPingAudio1 = PhotoImage(file=resource_path(os.path.join(data_dir, "BMPingAudio1.png")))
    BMPingAudio2 = PhotoImage(file=resource_path(os.path.join(data_dir, "BMPingAudio2.png")))

    event_handler = JournalUpdate()
    observer = Observer()
    observer.schedule(event_handler, path=eliteJournalPath, recursive=False)
    observer.start()

    AudioFeedBack.Start()

    CreateGUI(root)

    root.after(2500,AudioFeedBack.PingLoop)
    root.after(100, GetConfigFromFile, True)
    root.after(100, SingleInstance,True)
    root.mainloop()
