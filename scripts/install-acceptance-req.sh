#!/usr/bin/env bash

# Install all the requirements for running the
# acceptance test suite and the JavaScript
# unit test suite.
# 
# Requires 32-bit Ubuntu

# Exit if any commands return a non-zero status
set -e

sudo apt-get update

sudo apt-get install unzip

# Install xvfb
if [ -z `command -v xvfb` ]; then
    echo "Installing Xvfb..."
    sudo apt-get install -y xvfb

    # Install the xvfb upstart script
    sudo cat > /etc/init/xvfb.conf <<END
    description     "Xvfb X Server"
    start on (net-device-up
              and local-filesystems
              and runlevel [2345])
    stop on runlevel [016]
    exec /usr/bin/Xvfb :99 -screen 0 1024x768x24
END

    cat >> .bashrc <<END

    # Set the display to the virtual frame buffer (Xvfb)
    export DISPLAY=:99
END
else
    echo "Already installed; skipping."
fi

# Ensure that xvfb is running
sudo start xvfb 2> /dev/null || sudo restart xvfb 2> /dev/null || echo "Cannot start xvfb"

# Move to a temp directory so we can download things
cd /var/tmp

# Install Chrome
echo "Downloading Google Chrome..."
if [ -z `command -v google-chrome` ]; then
    wget --quiet https://dl.google.com/linux/direct/google-chrome-stable_current_i386.deb
    sudo dpkg -i google-chrome*.deb 2> /dev/null || true
    sudo apt-get -f -y install
else
    echo "Already installed; skipping."
fi

# Install ChromeDriver
echo "Installing ChromeDriver..."
if [ -z `command -v chromedriver` ]; then
    wget --quiet https://chromedriver.googlecode.com/files/chromedriver_linux32_2.3.zip
    unzip chromedriver_linux32_2.3.zip
    sudo mv chromedriver /usr/local/bin/chromedriver
    sudo chmod go+rx /usr/local/bin/chromedriver
else
    echo "Already installed; skipping."
fi

# Install Firefox
echo "Installing Firefox..."
sudo apt-get -y install firefox

# Install dbus (required for FF)
sudo apt-get -y install dbus-x11

# Install PhantomJS
echo "Installing PhantomJS..."
if [ -z `command -v phantomjs` ]; then
    wget --quiet "https://phantomjs.googlecode.com/files/phantomjs-1.9.1-linux-i686.tar.bz2"
    tar -xjf phantomjs-1.9.1-linux-i686.tar.bz2
    sudo mv phantomjs-1.9.1-linux-i686/bin/phantomjs /usr/local/bin/phantomjs
else
    echo "Already installed; skipping."
fi

exit 0
