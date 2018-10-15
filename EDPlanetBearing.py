AppVer = "v2.6.5"

import datetime
import os
import tempfile

global no_open_al; no_open_al = False

try:
    import json, math, winreg, win32gui, re, random, time, errno
    from tkinter import *
    from tkinter import ttk
    import tkinter as tk
    from sys import argv, exit
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from urllib.request import urlopen
    from urllib.parse import quote as urlquote

    try:
        from openal.audio import SoundSink, SoundSource
        from openal.loaders import load_wav_file
    except:
        no_open_al = True


    def addLogEntry(log_entry):  # Adds an entry to the log file.
        global edpb_folder
        global debug_mode
        try:
            if debug_mode:
                log_file = edpb_folder + "EDPB_log_" + str(datetime.datetime.now().year) + "-" + str(
                    datetime.datetime.now().month) + "-" + str(datetime.datetime.now().day) + ".txt"
                entry_log = str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute) + ":" + str(
                    datetime.datetime.now().second) + "." + str(datetime.datetime.now().microsecond) + " - " + str(
                    log_entry)
                with open(log_file, "a") as f:
                    f.write(entry_log + "\n")
                print("Entry Log added: " + entry_log)
        except Exception as e:
            print("Log failed: " + str(e))


    def clearFiles(file="All"):
        global edpb_config_file
        global edpb_lock
        for x in range(0, 100):
            try:
                try:
                    if file == "SessionFile" or file == "All":
                        os.remove(edpb_lock)
                        print("Deleted: " + edpb_lock)
                except OSError as e:
                    print(e)
                    addLogEntry(e)
                    if e.errno != errno.ENOENT:
                        raise
                try:
                    if file == "ConfigFile" or file == "All":
                        os.remove(edpb_config_file)
                        print("Deleted: " + edpb_config_file)
                except OSError as e:
                    print(e)
                    addLogEntry(e)
                    if e.errno != errno.ENOENT:
                        raise
                print("Succesfully deleted files")
                break
            except OSError as e:
                addLogEntry(e)
                if e.errno != errno.ENOENT:
                    raise
            except:
                print("E.Deleting files")
                addLogEntry("Deleting files")
                time.sleep(0.01)


    def callback(clear_lock=True, clear_config=True):  # Clean files and close the app.
        if clear_lock and clear_config:
            clearFiles("All")
        elif clear_lock:
            clearFiles("SessionFile")
        elif clear_config:
            clearFiles("ConfigFile")

        try:
            observer.stop()
            observer.join()
            root.destroy()
            exit()
        except Exception as e:
            debug_mode = True
            addLogEntry(e)
            exit()


    def resource_path(relative):
        try:
            if os.path.exists(relative):
                return os.path.join(relative)
            elif hasattr(sys, "_MEIPASS"):
                return os.path.join(sys._MEIPASS, relative)
            else:
                return os.path.join(relative)
        except:
            addLogEntry("Detecting extra files: " + str(e))
            if hasattr(sys, "_MEIPASS"):
                return os.path.join(sys._MEIPASS, relative)
            return os.path.join(relative)


    def singleInstance(first_run=False):
        global edpb_lock
        global session_id
        try:
            if first_run:
                try:
                    session_id = str(random.randrange(0, 1000000000))
                    with open(edpb_lock, "w") as f:
                        f.write(session_id)
                    print("Singleton: " + edpb_lock)
                    print("Session ID: " + session_id)
                    root.after(1000, singleInstance)
                except Exception as e:  # Guard against race condition
                    print("E.Creating SessionLock file: " + str(e))
                    debug_mode = True
                    addLogEntry(e)
                    callback()
            elif not os.path.exists(edpb_lock):
                print("SessionLock file missing, closing.")
                callback()
            else:
                try:
                    with open(edpb_lock) as f:
                        edpb_lock_id = f.read()
                    if edpb_lock_id != session_id:
                        print("New session ID detected, closing instance.")
                        callback(False, False)
                    else:
                        root.after(1000, singleInstance)
                except Exception as e:  # Guard against race condition
                    print("E.Checking Session Lock: " + str(e))
                    debug_mode = True
                    addLogEntry(e)
                    callback(False)

        except Exception as e:
            print("E.Single Instancing: " + str(e))
            debug_mode = True
            addLogEntry(e)


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

        def __init__(self):
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


    def focusElite():
        try:
            w = WindowMgr()
            w.find_window("FrontierDevelopmentsAppWinClass")
            w.set_foreground()
        except:
            pass


    def dragwin(event):
        x = mainframe.winfo_pointerx() - offsetx
        y = mainframe.winfo_pointery() - offsety
        root.geometry("+{x}+{y}".format(x=x, y=y))


    def clickwin(event):
        global offsetx
        global offsety
        offsetx = event.x
        offsety = event.y


    def resize(root, info_hud_level=0, starting_up=False):
        # Creating window parameters
        w = 185  # width for the Tk root
        # h = 40 # height for the Tk root
        # get screen width and height
        ws = root.winfo_screenwidth()  # width of the screen
        hs = root.winfo_screenheight()  # height of the screen
        if info_hud_level == 2:
            h = 100
        elif info_hud_level == 1:
            h = 80
        else:
            h = 37

        try:
            if starting_up:
                # Calculate x and y coordinates for the Tk root window
                x = (ws / 2) - (w / 2)
                y = (hs / 100)  # - (h/2)
                root.after(100, journalUpdate.on_modified, journalUpdate, "Startup")
            else:
                x = root.winfo_rootx()
                y = root.winfo_rooty()

            # set the dimensions of the screen
            # and where it is placed
            root.geometry("%dx%d+%d+%d" % (w, h, x, y))
        except Exception as e:
            print("E05: " + str(e))
            addLogEntry(e)
            print("Error on resizing")


    class createToolTip(object):
        """
        create a tooltip for a given widget
        """

        def __init__(self, widget, text="widget info", waittime = 500):
            self.waittime = waittime
            self.wraplength = 180  # pixels
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
                             wraplength=self.wraplength)
            label.pack(ipadx=1)
            self.tw.attributes("-topmost", True)

        def hidetip(self):
            tw = self.tw
            self.tw = None
            if tw:
                tw.destroy()


    class readJournalFile:
        def status():
            global status_file
            global no_run
            global flag_srv
            global flag_sc
            global current_lat_deg
            global current_long_deg
            global current_head
            global current_alt

            with open(status_file) as f:
                j_status_content = f.read()

            try:
                status = json.loads(j_status_content)
                status_flags = status["Flags"]

                flag_docked = status_flags & 1 << 0  # If ship is docked
                flag_landed = status_flags & 1 << 1  # If ship is landed
                flag_srv = status_flags & (1 << 26)  # If driving SRV
                flag_sc = status_flags & (1 << 4)  # If in Supercruise
                flag_no_coords = 2097152 - (status_flags & (1 << 21))  # If coordinates are not available
                no_run = flag_docked + flag_landed + flag_no_coords

                print("Flags: " + str(status_flags))
                print("FlagDocked: " + str(flag_docked))
                print("FlagLanded: " + str(flag_landed))
                print("FlagNoCoords: " + str(flag_no_coords))
                print("FlagSRV: " + str(flag_srv))
                print("FlagSC: " + str(flag_sc))
                print("NoRun: " + str(no_run))

                current_lat_deg = round(status["Latitude"], 4)
                current_long_deg = round(status["Longitude"], 4)
                current_head = round(status["Heading"], 0)
                current_alt = round(status["Altitude"], 0)
                print("Current Lat: " + str(current_lat_deg))
                print("Current Long: " + str(current_long_deg))
                print("Current Heading: " + str(current_head))
                print("Current Altitude: " + str(current_alt))
            except Exception as e:
                print("Couldn't read status.json file: " + str(e))
                addLogEntry(e)

        def journal():
            global elite_journal_path
            global body
            global star_system
            global body_radius
            journal_done = False

            try:
                body
            except:
                body = 'Not set'
            try:
                star_system
            except:
                star_system = 'Not set'

            try:
                journal_list = reversed(os.listdir(elite_journal_path))
                for journal_item_folder in journal_list:
                    if journal_done:
                        break
                    if "Journal." in journal_item_folder:
                        print("Reading Journal: " + journal_item_folder)
                        journal_item_file = elite_journal_path + journal_item_folder
                        with open(journal_item_file) as f:
                            j_content = reversed(f.readlines())
                        for j_entry in j_content:
                            j_event = json.loads(j_entry)
                            if "ApproachBody" == j_event["event"] or "Location" == j_event["event"]:
                                if body.upper() == j_event["Body"].upper():
                                    raise Exception("SameBody")
                                else:
                                    star_system = j_event["StarSystem"]
                                    body = j_event["Body"]
                                    journal_done = True
                                    break
                try:
                    if star_system != "Not set" and body != "Not set":
                        body_radius = 0
                        edsm_raw = urlopen("https://www.edsm.net/api-system-v1/bodies?systemName={}".format(
                            urlquote(star_system))).read()
                        print("Extracted data from " + star_system)
                        edsm_system = json.loads(edsm_raw)
                        edsm_bodies = edsm_system["bodies"]
                        for body_name_raw in edsm_bodies:
                            if body_name_raw["name"].upper() == body.upper():
                                body_radius = body_name_raw["radius"] * 1000
                                print("Radius of " + body + " is: " + str(body_radius) + " meters")
                                break
                except Exception as e:
                    print("E.EDSM: " + str(e))
                    addLogEntry(e)
            except Exception as e:
                if str(e) == 'SameBody':
                    print("Same body, preventing extra polls to EDSM")
                else:
                    print("Failed Journal reading.")
                    addLogEntry(e)


    class journalUpdate(FileSystemEventHandler):
        def on_modified(self, event):
            readJournalFile.journal()
            readJournalFile.status()
            calculate()


    def create_gui(root):
        style.theme_create("EDBearing", parent="clam", settings=None)

        style.theme_settings("EDBearing", {
            "TFrame": {
                "map": {
                    "background": [("active", "black"),
                                   ("!disabled", "black")],
                    "fieldbackground": [("!disabled", "black")],
                    "foreground": [("focus", "black"),
                                   ("!disabled", "black")]
                }
            },
            "TLabel": {
                "map": {
                    "background": [("active", "black"),
                                   ("!disabled", "black")],
                    "fieldbackground": [("!disabled", "black")],
                    "foreground": [("focus", "orange"),
                                   ("!disabled", "orange")]
                }
            },
            "TEntry": {
                "configure": {"insertbackground": "orange"},
                "map": {
                    "fieldbackground": [("focus", "white"),
                                        ("disabled", "black"),
                                        ("!disabled", "black")],
                    "foreground": [("focus", "black"),
                                   ("disabled", "orange"),
                                   ("!disabled", "orange")]
                }
            },
            "TButton": {
                "map": {
                    "background": [("active", "black"),
                                   ("!disabled", "black")],
                    "foreground": [("focus", "orange"),
                                   ("!disabled", "orange")]
                }
            },
            "TCheckbutton": {
                "map": {
                    "background": [("active", "black"),
                                   ("disabled", "black"),
                                   ("!disabled", "black")],
                    "foreground": [("focus", "orange"),
                                   ("disabled", "orange"),
                                   ("!disabled", "orange")]
                }
            }
        })

        global destination_coords
        global dest_heading
        global dest_heading_d
        global dest_heading_r
        global dest_heading_l
        global dest_distance

        destination_coords = StringVar()
        dest_heading = StringVar()
        dest_heading_d = StringVar()
        dest_heading_r = StringVar()
        dest_heading_l = StringVar()
        dest_distance = StringVar()

        style.theme_use("EDBearing")
        root.title("EDPlanetBearing")

        global mainframe
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        mainframe.bind("<ButtonPress-1>", clickwin)
        mainframe.bind("<B1-Motion>", dragwin)

        global coords_entry
        coords_entry = ttk.Entry(mainframe, width=18, justify=CENTER, textvariable=destination_coords)
        coords_entry.grid(column=2, columnspan=8, row=1, sticky=(W, E))
        coords_entry.focus()
        coords_entry.bind("<Return>", calculate)

        ttk.Label(mainframe, textvariable=dest_heading, justify=CENTER, font=("Helvetica", 16)).grid(column=5,
                                                                                                     columnspan=6,
                                                                                                     row=2,
                                                                                                     sticky=(W, E))
        ttk.Label(mainframe, textvariable=dest_heading_l, justify=CENTER, font=("Helvetica", 14)).grid(column=2,
                                                                                                       columnspan=3,
                                                                                                       row=2,
                                                                                                       sticky=(E))
        ttk.Label(mainframe, textvariable=dest_heading_r, justify=CENTER, font=("Helvetica", 14)).grid(column=9,
                                                                                                       columnspan=2,
                                                                                                       row=2,
                                                                                                       sticky=(W))

        global dest_heading_d_lab
        dest_heading_d_lab = ttk.Label(mainframe, textvariable=dest_heading_d, justify=RIGHT, font=("Helvetica", 10))
        dest_heading_d_lab.grid(column=8, columnspan=4, row=3, sticky=(E))

        global dest_distance_lab
        dest_distance_lab = ttk.Label(mainframe, textvariable=dest_distance, justify=CENTER, font=("Helvetica", 9))
        dest_distance_lab.grid(column=5, columnspan=7, row=3, sticky=(N, W, E))

        close_b = ttk.Button(mainframe, text=" X ", command=callback)
        close_b.grid(column=10, row=1, sticky=(E))

        global ping_cb
        ping_cb = ttk.Button(mainframe, image=bm_ping_audio0, command=audioFeedBack.ping_cycle_mode)
        ping_cb.grid(column=1, row=1, sticky=(E))

        resize(root, info_hud_level, True)

        for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

        root.protocol("WM_DELETE_WINDOW", callback)
        root.attributes("-topmost", True)
        root.overrideredirect(True)

        # Add Tooltips
        close_b_ttp = createToolTip(close_b, "Close")
        coords_entry_ttp = createToolTip(coords_entry, "Type destination coordinates")
        if no_open_al:
            ping_cb_ttp = createToolTip(ping_cb, \
                                        "OpenAL libraries not detected,\n"
                                        "Audio is disabled,\n"
                                        "You can find a download link\n"
                                        "in my repository's main page.",
                                        0)
        else:
            ping_cb_ttp = createToolTip(ping_cb, \
                                        "Audio Feedback\n"
                                        "Red = No audio\n"
                                        "Yellow = Only when deviation greater than 45°\n"
                                        "Green = All the time")


    def getShellFolders():
        global elite_journal_path
        global status_file
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            journal_dir, type = winreg.QueryValueEx(key, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")

            elite_journal_path = journal_dir + "\\Frontier Developments\\Elite Dangerous\\"
            l_appdat_ddir, type = winreg.QueryValueEx(key, "Local AppData")
            status_file = elite_journal_path + "status.json"
            os.path.exists(status_file)
        except Exception as e:
            print("E.Getting Journal Path" + str(e))
            addLogEntry("Getting Journal Path" + str(e))
            root.after(0, callback)


    if no_open_al:
        class audioFeedBack:
            def start():
                global ping_delay
                global ping_pos_x
                global ping_pos_z
                global ping_pitch
                global ping_delay_mult
                ping_delay = 1000
                ping_pos_x = 0.0
                ping_pos_z = 0.0
                ping_pitch = 1.0
                ping_delay_mult = 2

            def ping_loop():
                pass

            def destination_reached():
                pass

            def ping_cycle_mode(AudioModeSet=-1):
                pass
    else:
        class audioFeedBack:
            def start():
                # Prepare audio feedback
                try:
                    global sink
                    global source
                    global data
                    global ping_delay
                    global ping_pos_x
                    global ping_pos_z
                    global ping_pitch
                    global ping_delay_mult
                    sound_beep = resource_path("beep.wav")
                    ping_delay = 1000
                    ping_pos_x = 0.0
                    ping_pos_z = 0.0
                    ping_pitch = 1.0
                    ping_delay_mult = 2

                    sink = SoundSink()
                    sink.activate()
                    source = SoundSource(position=[ping_pos_x, 0, ping_pos_z])
                    # source.looping = False
                    source.gain = 50.0
                    data = load_wav_file(sound_beep)
                    sink.play(source)
                    print("Audio system started")
                except Exception as e:
                    print("E.Starting Audio: " + str(e))
                    addLogEntry(e)

            def ping_loop():
                global ping_delay
                global ping_pos_x
                global ping_pos_z
                global ping_pitch
                global info_hud_level
                global sink
                global source
                global data
                global audio_mode
                global direction_over_margin
                try:
                    if info_hud_level != 0:
                        if (audio_mode == 1 and direction_over_margin) or audio_mode == 2:
                            source.bufferqueue = []  # Clear any residual queued sounds
                            source.position = [ping_pos_x, source.position[1], ping_pos_z]
                            source.pitch = ping_pitch
                            source.queue(data)
                            sink.update()
                            print("Ping at: " + str(source.position))
                            source.bufferqueue = []  # Clear any residual queued sounds
                except Exception as e:
                    print("E.Playing Audio(Loop): " + str(e))
                    addLogEntry(e)
                finally:
                    print("Ping Multiplier: " + str(ping_delay_mult) + " - Distance: " + str(
                        ping_delay * ping_delay_mult))
                    root.after(int(ping_delay * ping_delay_mult), audioFeedBack.ping_loop)

            def destination_reached():
                try:
                    global ping_pitch
                    global info_hud_level
                    global sink
                    global source
                    global data
                    global audio_mode
                    global direction_over_margin

                    source.bufferqueue = []  # Clear any residual queued sounds
                    PingPosX = 0.0
                    PingPosZ = 0.0
                    ping_pitch = 1.5

                    if info_hud_level != 0:
                        if audio_mode != 0:
                            audioFeedBack.ping_cycle_mode(0)
                            sink.update()
                            source.position = [0.0, source.position[1], 0.0]
                            source.pitch = ping_pitch
                            source.queue(data)
                            source.queue(data)
                            source.queue(data)
                            print("Triple Ping at: " + str(source.position))
                            sink.update()
                except Exception as e:
                    print("E.Playing Audio(Reached): " + str(e))
                    addLogEntry(e)
                finally:
                    if using_config_file:
                        root.after(0, callback)

            def ping_cycle_mode(audio_mode_set=-1):
                global audio_mode
                try:
                    if audio_mode_set != -1:
                        audio_mode = audio_mode_set
                    elif audio_mode == 2:
                        audio_mode = 0
                    else:
                        audio_mode = audio_mode + 1
                    exec('ping_cb["image"] = bm_ping_audio' + str(audio_mode))
                    coords_entry.focus()
                    print("Audio Mode set to: " + str(audio_mode) + " - " + str(ping_cb["image"]))
                except Exception as e:
                    print("E.Setting Audio Feedback image: " + str(e))
                    addLogEntry(e)


    def getCLArguments(argv=argv):
        global destination_coords
        try:
            argv = [element.lower() for element in argv]
            myargs = getopts(argv)
            if "+debug" in argv:
                global debug_mode
                debug_mode = True
            if "+close" in argv:
                root.after(0, callback)
            if "+lat" in myargs and "+long" in myargs:
                arg_lat = myargs["+lat"]
                arg_long = myargs["+long"]
                destination_coords.set(str(arg_lat) + ", " + str(arg_long))
                root.after(250, focusElite)
                clearFiles("ConfigFile")
            if "+audio" in myargs:
                audioFeedBack.ping_cycle_mode(int(myargs["+audio"]))
        except Exception as e:
            print(e)
            debug_mode = True
            addLogEntry(e)


    def getConfigFromFile(startup=False):  # Gets config from config file if exists and applies it
        global edpb_config_file
        global audio_mode
        global info_hud_level
        global using_config_file
        global edpb_config_content_previous
        global destination_coords
        try:
            edpb_config_content_previous
        except:
            edpb_config_content_previous = ''
        try:
            if os.path.exists(edpb_config_file):
                try:
                    with open(edpb_config_file) as f:
                        edpb_config_content = f.read().lower()
                    if edpb_config_content_previous == edpb_config_content:
                        raise Exception('SameConfig')
                    if "close" in edpb_config_content:
                        callback()
                    configs = json.loads(edpb_config_content)
                    try:
                        dst_lat = float(configs["lat"])
                        dst_long = float(configs["long"])
                    except:
                        print("E.Couldn't load coords from existing config file.")
                        addLogEntry("E.Couldn't load coords from existing config file.")
                        info_hud_level = 0
                        resize(root, info_hud_level)
                        destination_coords.set("")
                        audioFeedBack.ping_cycle_mode(0)
                        root.after(500, calculate)
                        try:
                            os.remove(edpb_config_file)
                        except:
                            print("E.Deleting empty config file")
                            addLogEntry("Deleting empty config file")
                        raise

                    try:
                        audioFeedBack.ping_cycle_mode(int(configs["audio"]))
                        using_config_file = True
                    except:
                        pass
                    if dst_lat == -0:
                        dst_lat = 0.0

                    destination_coords.set(str(dst_lat) + ", " + str(dst_long))

                    edpb_config_content_previous = edpb_config_content

                    if startup:
                        root.after(100, focusElite)
                        root.after(150, calculate)
                    elif info_hud_level == 0:
                        root.after(0, calculate)
                    # Disable GUI
                    if str(coords_entry["state"]) == "normal":
                        coords_entry["state"] = "disabled"
                        print("GUI Disabled")
                except Exception as e:
                    if str(e) == 'SameConfig':
                        pass
                    else:
                        print("E.Reading Config file: " + str(e))
                        addLogEntry(e)
                        if str(coords_entry["state"]) != "normal":
                            coords_entry["state"] = "normal"
                            print("GUI Enabled")
                    edpb_config_content_previous = edpb_config_content
            else:
                if str(coords_entry["state"]) != "normal":
                    coords_entry["state"] = "normal"
                    edpb_config_content_previous = ''
                    print("GUI Enabled")
        except:
            coords_entry["state"] = "normal"
            edpb_config_content_previous = ''
            print("GUI Enabled")
            addLogEntry(e)

        root.after(2000, getConfigFromFile)


    def calculate(event="None"):
        global no_run
        global dst_lat
        global dst_long
        global info_hud_level
        destination_raw = (destination_coords.get()).replace(",", " ")
        destination = str(destination_raw).split()
        try:
            dst_lat = float(destination[0])
            dst_long = float(destination[1])
            if dst_lat == -0:
                dst_lat = 0.0
        except:
            no_run = -1
            print("Destination missing")
        try:
            if "Return" in event.keysym:
                destination_coords.set(str(dst_lat) + ", " + str(dst_long))
                readJournalFile.status()
                calculate()
                focusElite()
        except:
            pass

        if no_run != 0:
            print("Coords irrelevant")
            info_hud_level = 0
        else:
            print("Coords relevant")
            calcHeading()
            calcDArrows()
            calcDistance()
            calcAngDesc()
        print("HUD level: " + str(info_hud_level))
        resize(root, info_hud_level)


    def calcHeading():
        global current_lat_deg
        global current_long_deg
        global dst_lat
        global dst_long
        global bearing
        global info_hud_level
        try:
            current_lat_rad = math.radians(current_lat_deg)
            current_long_rad = math.radians(current_long_deg)
            dst_lat_rad = math.radians(float(dst_lat))
            dst_long_rad = math.radians(float(dst_long))

            x = math.cos(current_lat_rad) * math.sin(dst_lat_rad) - math.sin(current_lat_rad) * math.cos(
                dst_lat_rad) * math.cos(dst_long_rad - current_long_rad)
            y = math.sin(dst_long_rad - current_long_rad) * math.cos(dst_lat_rad)
            bearing_rad = math.atan2(y, x)
            bearing_deg = math.degrees(bearing_rad)
            bearing = int((bearing_deg + 360) % 360)
            dest_heading.set(str(bearing) + "°")
            info_hud_level = 1
        except Exception as e:
            addLogEntry("CalcHeading(): " + str(e))


    def calcDArrows():
        global bearing
        global current_head
        global ping_pos_x
        global ping_pos_z
        global ping_pitch
        global direction_over_margin
        global info_hud_level
        try:
            if current_head < bearing:
                current_head += 360  # denormalize ...
            direction_raw = current_head - bearing  # Calculate left turn, will allways be 0..359
            direction = direction_raw
            print("DirectionRaw: " + str(direction_raw) + "°")
            left_arrow = ""
            right_arrow = ""
            # take the smallest turn
            if direction <= 1 or direction >= 359:
                print("Going Forward")
                if direction > 180:
                    direction = 360 - direction
            elif direction < 180:
                # Turn left : Direction degrees
                print("Going Left")
                left_arrow = "<"
                if direction >= 30:
                    left_arrow = "<<"
                if direction >= 90:
                    left_arrow = "<<<"
            elif direction > 180:
                # Turn right : 360-Direction degrees
                print("Going Right")
                direction = 360 - direction
                right_arrow = ">"
                if direction >= 30:
                    right_arrow = ">>"
                if direction >= 90:
                    right_arrow = ">>>"
            else:
                print("Going Backwards")
                left_arrow = "<<<"
                right_arrow = ">>>"
            dest_heading_l.set(left_arrow)
            dest_heading_r.set(right_arrow)

            # Setting 3D position of the beep source
            ping_pos_x = math.sin(math.radians(-direction_raw)) * 50
            ping_pos_z = math.cos(math.radians(-direction_raw)) * 50
            ping_pitch = 1.0 - (direction / 360)

            print("PingPosX: " + str(ping_pos_x))
            print("PingPosZ: " + str(ping_pos_z))
            print("PingPitch: " + str(ping_pitch))

            alert_margin = 45
            if alert_margin < direction:
                direction_over_margin = True
                print("Over 45º")
            else:
                direction_over_margin = False
                print("Not over 45º")

        except Exception as e:
            addLogEntry("CalcDArrows(): " + str(e))


    def calcDistance():
        global body_radius
        global current_lat_deg
        global current_long_deg
        global dst_lat
        global dst_long
        global current_alt
        global flag_srv
        global flag_sc
        global distance_meters
        global distance_surface
        global info_hud_level
        global ping_delay_mult
        min_distance = 100
        print("Starting Distance Calculation")

        try:
            if body_radius > 0:
                # Distance
                dif_lat = math.radians(dst_lat - current_lat_deg)
                dif_long = math.radians(dst_long - current_long_deg)

                dis1 = math.sin(dif_lat / 2) ** 2 + math.cos(math.radians(current_lat_deg)) * math.cos(
                    math.radians(float(dst_lat))) * math.sin(dif_long / 2) ** 2
                dis2 = 2 * math.atan2(math.sqrt(dis1), math.sqrt(1 - dis1))
                distance_surface = int(body_radius * dis2)
                distance_meters = int(math.sqrt(distance_surface ** 2 + current_alt ** 2))

                if distance_meters >= 100000:
                    distance = int(distance_meters / 1000)
                    dis_scale = "km"
                else:
                    distance = distance_meters
                    dis_scale = "m"
                distance = format(distance, ",d")
                dest_distance.set(str(distance) + " " + dis_scale)

                info_hud_level = 2

                try:
                    if flag_srv != 0:   # Distance calculations for SRV
                        min_distance = 100
                    elif flag_sc != 0:  # Distance calculations for supercruise
                        min_distance = 0
                    else:               # Distance calculations for normal flight
                        min_distance = 2000
                    if (distance_meters < min_distance):
                        audioFeedBack.destination_reached()
                except:
                    print("E.Shutting when destination is reached")

                print("Surface in meters:  " + str(distance_surface))
                print("Distance in meters: " + str(distance_meters))
            else:
                try:
                    ping_delay_mult = 2.0
                    if (dst_lat - current_lat_deg < 0.01 and dst_long - current_long_deg < 0.01 and flag_sc == 0):
                        audioFeedBack.destination_reached()
                except:
                    print("E.Shutting when destination is reached")
        except Exception as e:
            addLogEntry("CalcDistance(): " + str(e))


    def calcAngDesc():  # Angle of descent
        global descent_angle
        global current_alt
        global distance_meters
        global distance_surface
        global flag_srv
        global flag_sc
        global ping_delay_mult

        ping_delay_mult_min = 0.75
        ping_delay_mult_max = 2.0


        try:
            descent_angle = - int(math.degrees(math.atan(current_alt / distance_surface)))
            print("Angle of Descent: " + str(descent_angle))

            try:
                if flag_srv != 0:  # Distance calculations for SRV
                    min_beeping_distance = 50
                    max_beeping_distance = 2000
                    ping_delay_mult = distance_surface / 600
                else:  # Angle calculations for normal flight and supercruise
                    # WIP Delay calculations need testing!!!
                    current_delay = 10.0
                    if flag_sc != 0:
                        angle_delay = {
                            -5:2.0,
                            -10:1.8,
                            -20:1.4,
                            -30:1.0,
                            -40:0.75,
                            -90:0.0
                        }
                    else:
                        angle_delay = {
                            -5: 2.0,
                            -10: 1.8,
                            -20: 1.6,
                            -30: 1.4,
                            -40: 1.2,
                            -50: 1.0,
                            -60: 0.75,
                            -90: 0.0
                        }
                    for a, d in angle_delay.items():
                        if descent_angle >= a:
                            current_delay = d
                            break
                    ping_delay_mult = current_delay
                print("Ping Multiplier: " + str(ping_delay_mult))
                ping_delay_mult = max(ping_delay_mult_min, min(ping_delay_mult_max, ping_delay_mult))
            except:
                print("E.Calculating Beeping descent")

            if descent_angle <= 0 and distance_meters < 1000000:
                if  flag_srv == 0 and current_alt > 3000:
                    dest_heading_d.set(str(descent_angle) + "°")
                    dest_distance_lab.grid(column=3, columnspan=7, row=3, sticky=(N, W, E))
                    dest_heading_d_lab.config(foreground="orange")
                    ping_delay_mult = max(ping_delay_mult_min, min(2, ping_delay_mult))
                    if descent_angle <= -60 or descent_angle > -5:
                        dest_distance_lab.grid(column=3, columnspan=7, row=3, sticky=(N, W, E))
                        dest_heading_d_lab.config(foreground="red")
            else:
                dest_heading_d.set("")
        except Exception as e:
            addLogEntry("CalcAngDesc(): " + str(e))
except Exception as e:
    try:
        log_file = os.path.dirname(os.path.realpath(__file__)) + "\\" + "EDPB_log_" + str(
            datetime.datetime.now().year) + "-" + str(datetime.datetime.now().month) + "-" + str(
            datetime.datetime.now().day) + ".txt"
        entry_log = str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute) + ":" + str(
            datetime.datetime.now().second) + "." + str(datetime.datetime.now().microsecond) + " - " + str(e)
        with open(log_file, "a") as f:
            f.write(entry_log + "\n")
        print("Entry Log added: " + entry_log)
    except Exception as e:
        print("Log failed: " + str(e))
    finally:
        callback()

if __name__ == "__main__":
    try:
        root = Tk()
        style = ttk.Style()
        global edpb_folder

        debug_mode = False  # Temporary variables for testing

        getShellFolders()
        edpb_folder = os.path.dirname(os.path.realpath(__file__)) + "\\"

        edpb_lock = os.path.normpath(tempfile.gettempdir() + "/EDPBSingleton.lock")
        edpb_config_file = edpb_folder + "Config.json"
        info_hud_level = 0
        audio_mode = 0
        gfx_dir = 'GFX'
        bm_ping_audio0 = PhotoImage(file=resource_path(os.path.join(gfx_dir, "BMPingAudio0.png")))
        bm_ping_audio1 = PhotoImage(file=resource_path(os.path.join(gfx_dir, "BMPingAudio1.png")))
        bm_ping_audio2 = PhotoImage(file=resource_path(os.path.join(gfx_dir, "BMPingAudio2.png")))

        event_handler = journalUpdate()
        observer = Observer()
        observer.schedule(event_handler, path=elite_journal_path, recursive=False)
        observer.start()

        audioFeedBack.start()

        create_gui(root)
        getCLArguments()

        root.after(2500, audioFeedBack.ping_loop)
        root.after(100, getConfigFromFile, True)
        root.after(100, singleInstance, True)
        root.mainloop()
    except Exception as e:
        debug_mode = True
        addLogEntry(e)
        callback()
