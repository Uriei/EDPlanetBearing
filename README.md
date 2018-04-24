# EDPlanetBearing

This is an app to calculate the heading you need to follow to reach an specific point giving its coordinates on a planet in Elite Dangerous.

- It can tell you the heading you need to aim to reach your destination,
- also adds some direction arrows around the heading so you can check even faster in which general direction you need to go,
- and optional audio feedback for the same purpose. This audio feedback has 3 modes, ![alt text](https://raw.githubusercontent.com/Uriei/EDPlanetBearing/master/BMPingAudio0.png "No Audio Feedback")
 Red (no audio), ![alt text](https://raw.githubusercontent.com/Uriei/EDPlanetBearing/master/BMPingAudio1.png "Deviation alert only")
 Yellow (deviation alerts only, 45°), and ![alt text](https://raw.githubusercontent.com/Uriei/EDPlanetBearing/master/BMPingAudio2.png "Constant audio feedback") Green (constant audio feedback); this audio feedback will position automatically on the speaker/headset side of the heading you need to go.<br>
*I can't test it, but I think this would work even better with 5.1/7.1 systems as it uses 3D positioning for that*

To use it you have several options.

### The basic one, just start it, enter the coordinates and fly away.

### Using command line:
You can start the app with command line as:<br>
```EDPlanetBearing.exe +lat 1.2345 +long -98.7654 +audio 0```
- +lat = Latitude (duh!)
- +long = Longitude (duh again!)
- +audio = Audio mode you want to use, 0 for ![alt text](https://raw.githubusercontent.com/Uriei/EDPlanetBearing/master/BMPingAudio0.png "No Audio Feedback") no audio, 1 for ![alt text](https://raw.githubusercontent.com/Uriei/EDPlanetBearing/master/BMPingAudio1.png "Deviation alert only") only deviation alerts (over 45°), 2 for ![alt text](https://raw.githubusercontent.com/Uriei/EDPlanetBearing/master/BMPingAudio2.png "Constant audio feedback") constant audio feedback.

### Using the config file:
The app will create a folder in your Local Appdata folder ```%localappdata%/EDPlanetBearing``` inside this folder you can create a file called `Config.json` in which you can input the same info as in the command line way, but json formatted, this is:<br>
```{"lat":1.2345, "long":-98.7654, "audio":0}```

I added these two different ways to automate it depending on the needs of each person and the software they use for it, your choice.
In case of conflict, Command Line has preference.

Also, for automation purposes, you can close the app in both ways, adding `+close` to the command line, or replacing all the content of the `Config.json` file with `close` no brackets, no nothing, just `close`.

***

Quick video example of what it does (v0.5), the coordinates set are to a tip off I got.

More info about the test in the video description.

[![Example version v0.5](https://img.youtube.com/vi/MyaY__PWMTs/0.jpg)](https://youtu.be/MyaY__PWMTs)
