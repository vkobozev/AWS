#!/bin/bash
#update
sudo apt-get -y update

# install pip3 
sudo apt-get install -y python3-pip
sudo pip3 install pip --upgrade 

#install ipython
sudo pip install ipython

#config aws
mkdir -p /root/vasya/
touch /root/vasya/hi