Installing Stellarium

```bash
sudo apt update
sudo apt install snapd
sudo reboot
sudo snap install snapd
sudo snap install stellarium-daily
```

Build from source

```bash
git clone https://github.com/Stellarium/stellarium.git
mkdir build && cd build

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

# Qt6 dependencies
sudo apt install build-essential cmake zlib1g-dev libgl1-mesa-dev libdrm-dev libglx-dev \
                 gcc g++ graphviz doxygen gettext git libxkbcommon-x11-dev libgps-dev \
                 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-pulseaudio \
                 gstreamer1.0-libav gstreamer1.0-vaapi \
                 qt6-base-private-dev qt6-multimedia-dev qt6-positioning-dev qt6-tools-dev \
                 qt6-tools-dev-tools qt6-base-dev-tools qt6-qpa-plugins qt6-image-formats-plugins \
                 qt6-l10n-tools qt6-webengine-dev qt6-webengine-dev-tools libqt6charts6-dev \
                 libqt6charts6 libqt6opengl6-dev libqt6positioning6-plugins libqt6serialport6-dev \
                 qt6-base-dev libqt6webenginecore6-bin libqt6webengine6-data \
                 libexiv2-dev libnlopt-cxx-dev libqt6concurrent6 libmd4c-dev libmd4c-html0-dev

   cmake -DCMAKE_BUILD_TYPE="Release" ../stellarium
   nice make -j4
```

```bash
STELARIUM_PATH=~/.config/autostart/stellaium.desktop
if [! -f $STELARIUM_PATH]; then
  cat > $STELARIUM_PATH <<EOF
  [Desktop Entry]
  Type=Application
  Name=Stellarium
  NoDisplay=false
  Exec=snap run stellarium-daily.stellarium --opengl-compat -f yes
  EOF
fi
```

Installing `uv`

See [docs](https://docs.astral.sh/uv/getting-started/installation/)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Libraries for audio (check if required)

```bash
sudo apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev
```

How to keep the HDMI port on:

See [this](https://forums.raspberrypi.com/viewtopic.php?t=363503) discussion.

Edit `/boot/cmdline.txt` and add `video=HDMI-A-1:1920x1080@60` (or any other resolution) to the end of the line.

To verify if the port is connected use `kmsprint`.

To check the current configuration use `kmsprint -m` or `xrandr`.


# UI

```bash
sudo apt-get install raspberrypi-ui-mods

```