media_streaming
===============

Server and Client based on vlc backend.

Install git to download (clone) the package into the client/server.
* sudo apt-get install git
* git clone https://github.com/rmonno/media_streaming


Install & Launch the server
===========================

Install dependencies
* cd media_streaming/server && sh depends.sh

Take a look at the server options
* python server.py -h

Launch the server as a daemon (and redirect the output)
* python server.py -d -a <server_addr> &>/tmp/server.log &

Take a look at the media-manager options & available commands
* python media-manager.py -h
* python media-manager.py -d ?
Usage:

append2play -n <index>
	Schedule a file to be played

list
	Get a list of all stored audio/video files

upload -f <file>
	Upload a file into the repository (absolute path)

remove -n <index>
	Remove a file from the repository

upload2remote -f <user>@<server-addr>:<file>
	Upload a (remote) file into the repository (user, server address, absolute path)

queuesize
	Get a size of scheduled audio/video files

* E.g. (list of files) python media-manager.py -d -a <server_addr> list 
* E.g. (play a file) python media-manager.py -d -a <server_addr> append2play -n 0


Install & Launch the client
===========================

Install dependencies
* cd media_streaming/client && sh depends.sh

Take a look at the client options
* python client.py -h

Launch the client
* python client.py -d -a <server_addr>


Streaming audio over ssh connection (using pulseaudio)
======================================================

On the remote pc (without audio devices) install & configure paprefs
* sudo apt-get install paprefs
* paprefs
** (Network Access) check Make discoverable PulseAudio network sound devices available locally
** (Network Server) check Enable network access to local sound devices
** (Network Server) check Allow other machines on the LAN to discover local sound devices
** (Simultaneous Output) check Add virtual output device for simultaneous output on all local sound cards

On the local machine (with audio devices) start pulseaudio-x11
* sudo sudo start-pulseaudio-x11

Login into remote with port-forward
* ssh -C -R 24713:localhost:4713 <user>@<remote> -X
* export PULSE_SERVER=tcp:localhost:24713

Launch the client
* cd media_streaming/client && python client.py -d -a <server_addr>
