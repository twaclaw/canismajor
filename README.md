# Canis Major

> A sky projection based on Stellarium for very curious and inquisitive children

<img src="./img/planispheri_celeste.jpg"></img>

In Carl Sagan's Contact, SETI detects an intelligent signal coming from the star Vega in the constellation Lyra. In The Invincible by Stanislaw Lem, the crew of the eponymous spaceship lands on the planet Regis III, in the constellation Auriga, and finds the ruins of an ancient Lyran civilization (apparently Lyrans are super-advanced, or at least very popular). And in The Three Body Problem by Cixin Liu, the invaders come from the constellation Centaurus.

Constellations are not only the beautiful tapestry of the sky and the source of awe and inspiration for many stories and myths, they are essentially celestial landmarks. Whether it is a super intelligent civilization in a science fiction story or a scientific observation, the constellations are our reference points in the sky. For example, the planets move very close to the ecliptic, so the constellations not only give you your horoscope, but can help you find our traveling companions.

Constellations and their mythologies are also great material for bedtime stories. I was inspired to create this project while reading _Constellations_ by Govert Schilling.
In a way, I see this project as an extension of the book. I extended the book with an animated, real-time projection of the night sky. Of course, all the heavy lifting is done by [Stellarium](https://stellarium.org/), one of my all-time favorite open source software.

# Project description

This project is basically a remote control for Stellarium. It uses the API provided by the remote control plugin to trigger scripts written in the Stellarium scripting engine. The objects and animations to be displayed are controlled by QR codes (pasted in the corresponding constellations on the book).

![](./img/block_diagram.svg)

The application is designed in a way that it can run on a computer, such as a laptop running Linux or Mac, as well as a Raspberry Pi (I tried a Raspberry Pi 5).

# Steps to reproduce

### Step 1

Install Stellarium (follow the instructions for your OS, package manager, etc.)

### Step 2

Enable and make sure the remote control plugin in Stellarium is running. You can do this in the UI or by modifying the `config.ini` file. See the `[Remote Control]` section in the [example Stellarium configuration file](./conf/stellarium/config.ini) for reference.

You can check if the API provided by the remote control plugin is working by calling e.g:

```bash
curl -X POST -d 'id=zodiac.ssc' http://localhost:8090/api/scripts/run
```

### Step 3

Download this code

```bash
git clone https://github.com/twaclaw/canismajor.git
cd canismajor
```

### Step 4

Install the Python application.

Using [uv](https://docs.astral.sh/uv/):

```bash
uv venv venv --python 3.13 # or 3.11 or 3.12
. venv/bin/activate
uv pip install -e . # on the raspberry pi: uv pip install -e .[rpi]
```

Using `pip`:

```bash
virtualenv venv --python 3.13 # or 3.11 or 3.12
. venv/bin/activate
pip install -e . # on the raspberry pi: pip install -e .[rpi]
```

### Step 5

Modify the [conf.yaml](conf.yaml) configuration file. In particular:

- Make sure that the folder containing the Stellarium scripts is listed under `script_paths`
- Check which language the installed version of Stellarium uses to select the constellations. For example, version 24.4 uses `native` names, e.g., "Orion", "Canis Major", "Gemini", etc., while version 25.1 uses English names, e.g., "Hunter", "Great Dog", "Twins", etc. Set `constellations_language` accordingly, either "english" or "native" (you can use the search function CTRL + F to find out which language is used in your Stellarium version).

### Step 6

Run the application

```bash
python -m main --conf conf.yaml
```

# How to use the application

The application has a queue waiting for the names of the objects to be selected (constellations, planets, etc.), or otherwise the name of the script to be executed. Note that the names are case sensitive. The following logic and priorities are used:

### Names and scripts

- If the name is one of the keys in the `constellations` dictionary defined in [stellarium.py](./src/stellarium.py) (for example "Andromeda" or "Ursa Major"), then the [constellations](./templates/_constellations.ssc) template is used to select the constellation.

- If the name is one of the items in the `search:objects` list in the [configuration file](conf.yaml) (for example "Mars" or "Callisto"), then the [object](./templates/_objects.ssc) template is used to select the object. Feel free to add more objects to the list.

- If the name is one of the keys, other than "constellations" and "objects", in the `scripts` dictionary in the [configuration file](conf.yaml) (for example "zodiac2"), then the script with the same name in the [templates](./templates) folder will be executed without parameters. **If you add new scripts, choose the names so that they do not conflict with existing Stellarium scripts.**

- If the name is one of the scripts included in the official Stellarium distribution, this script will be executed without modifications.

### How names are passed to the application

The names can be passed to the application in one of the following ways:

#### On the Raspberry Pi

- By scanning a [QR code](./img/codes_constellations.svg) that encodes the corresponding object name. This approach assumes that the QR code scanner is identified as a keyboard (a HID device).
- The list `controls` in the [configuration file](conf.yaml) should contain `qrcode`.
- The console method described below can work if the application is called from the command line but not if it is run as a `systemd` service.

#### On a Linux or Mac computer

- By typing them into the standard input (console), which can be useful for debugging:
- The list `controls` in the [configuration file](conf.yaml) should contain `console`.

```bash
python -m main --conf conf.yaml
>>Auriga
>>
```

When the focus (mouse over) is on the console (terminal), this method can be used to test QR Code scans with no configuration (or code) required for the scanner (because the scanner is detected as a keyboard).

[This image](./img/codes_constellations.svg) is an example with QR Codes corresponding to the 88 constellations. The script [qrcodes.py](./scripts/qrcodes.py) can be used to generate this file, as well as other QR Codes corresponding to other objects.

```bash
python scripts/qrcodes.py --help

# For example to generate the QR codes for the 88 constellations on a single page:
python scripts/qrcodes.py --output codes_constellations.svg constellations

# to generate the QR codes for the objects and scripts:
python scripts/qrcodes.py --output objects_and_scripts.svg objects --conf conf.yaml --what SO

# or to generate a single QR code (exact spelling, case sensitive):
python scripts/qrcodes.py --output canis_major.svg single --data "Canis Major"
```

# Instructions to install on a Rapsberry Pi

## Hardware

- Raspberry Pi 5 (other models might work) with an SSD disk for better performance
- A QR scan code reader
- An HDMI projector or screen

My setup looks like this:

![](./img/connection.svg)

## Software and configuration

### Install Stellarium

It can be installed either by `snap` or by compiling from source. I found that version `v24.4` against Qt 5 generally works better on this device, and built it from source.

<details>
<summary>Using snap</summary>

```bash
sudo apt update
sudo apt install snapd
sudo reboot
sudo snap install snapd
sudo snap install stellarium-daily # latest version
```

</details>

<details>
<summary>Building from source</summary>

```bash
git clone https://github.com/Stellarium/stellarium.git
cd stellarium
git checkout v24.4 # or any other version
mkdir build24.4 && cd build24.4

# install dependencies, see: https://github.com/Stellarium/stellarium/blob/master/BUILDING.md
# v24.4 and head working with Qt5
sudo apt install build-essential cmake zlib1g-dev libgl1-mesa-dev libdrm-dev gcc g++ \
                 graphviz doxygen gettext git libgps-dev \
                 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-pulseaudio \
                 gstreamer1.0-libav gstreamer1.0-vaapi qtbase5-dev \
                 qtbase5-private-dev qtscript5-dev libqt5svg5-dev qttools5-dev-tools \
                 qttools5-dev libqt5opengl5-dev qtmultimedia5-dev libqt5multimedia5-plugins \
                 libqt5serialport5 libqt5serialport5-dev qtpositioning5-dev libqt5positioning5 \
                 libqt5positioning5-plugins qtwebengine5-dev libqt5charts5-dev \
                 libexiv2-dev libnlopt-cxx-dev libtbb-dev libtbb2 libqt5concurrent5 \
                 libmd4c-dev libmd4c-html0-dev


cmake -DCMAKE_BUILD_TYPE="Release" ../stellarium
nice make -j4
```

</details>

### Making stellarium run on startup

For instance:

```bash
STELARIUM_PATH=~/.config/autostart/stellaium.desktop
if [! -f $STELARIUM_PATH]; then
  cat > $STELARIUM_PATH <<EOF
  [Desktop Entry]
  Type=Application
  Name=Stellarium
  NoDisplay=false
  Exec=/home/pi/stellarium/build24.4/src/stellarium --opengl-compat --platform xcb -f yes
  EOF
fi
```

### Installing `uv`

See [uv docs](https://docs.astral.sh/uv/getting-started/installation/)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installing the Desktop UI

If you are coming from a headless Raspberry Pi, you will need to install the UI.

```bash
sudo apt-get install raspberrypi-ui-mods
```

### Running as a service

The application can run as a `systemd` service.

```bash
mkdir -p $HOME/.config/systemd/user
cp conf/systemd/canismajor.service $HOME/.config/systemd/user/
systemctl --user enable canismajor.service
systemctl --user start canismajor.service
loginctl enable-linger
```

### Configuring the QR code scanner

The QR code scanner I used is detected as a HID keyboard device (`/dev/hidraw0`). You can use `lsusb` to get information about this device, for example to create a `udev` rule.

```bash
lsusb
Bus 001 Device 014: ID 1a86:5456 QinHeng Electronics USB Keyboard

cat /etc/udev/rules.d/99-qrcode-reader-permissions.rules
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5456", MODE="0666"
```

I reversed-engineered the protocol by checking:

```bash
sudo hexdump -C /dev/hidraw0
```

# Contributing

This is tiny project but your contributions are more than welcome. If you have any suggestions, ideas, or improvements, please feel free to open an issue or a pull request. If you have any questions or want to start a discussion, please feel free to reach out.

Have a look at the [contributing guidelines](./CONTRIBUTING.md) for more information.

---

# References and Credits

- [Stellarium](https://stellarium.org/)
- [Constellations by Govert Schilling](https://www.goodreads.com/book/show/42275188-constellations)
- Title image: A celestial map by the Dutch cartographer Frederik de Wit, 1670, [Wikimedia](https://en.wikipedia.org/wiki/Star_chart#/media/File:Planisph%C3%A6ri_c%C5%93leste.jpg)

---
