IPTVProxy: A playlist generator and PVR for IPTV providers written in Python 3
==============================================================================

Introduction
============
IPTVProxy is a lean yet powerful playlist generator and PVR for IPTV providers. Lean in the sense that it can fully run on CPU and memory strapped devices. Powerful in the features it offers.

Installation
============
At this point the only way to install IPTVProxy is by downloading `git <https://git-scm.com/downloads>`_ and cloning the repository

.. code-block:: bash

    $ git clone https://github.com/sfanous/IPTVProxy.git

Updating to the latest version is just a matter of updating your local repository to the newest commit

.. code-block:: bash

    $ git pull

IPTVProxy depends on a few packages. To install these packages run the following command

.. code-block:: bash

    $ pip install -r requirements.txt

Tested Clients
==============
IPTVProxy has been tested with the following clients

1. Kodi's IPTV Simple Client
2. Perfect Player
3. PotPlayer
4. VLC

Running
=======
To start IPTVProxy run the following command

.. code-block:: bash

    $ python iptv_proxy_runner.py

IPTVProxy supports a number of command line arguments. Run the following command to get a help message with all the options

.. code-block:: bash

    $ python iptv_proxy_runner.py -h

Configuration
==============
There are multiple options to configure IPTVProxy. I recommend using option #3.

1. Use your favourite text editor and edit iptv_proxy.ini before starting IPTVProxy
2. Use your favourite text editor and edit iptv_proxy.ini after starting IPTVProxy. Updates to the file will be picked up as soon as the file is saved
3. Use the builtin web interface by browsing to http<s>://<IP Address>:<Port>/index.html, where <IP Address> is the IP address of the machine on which IPTVProxy is running, and <Port> is the port number which the machine is listening on. You will be presented with the following

.. image:: https://i.imgur.com/ovwC0SB.png

Click on the Configuration button in the top navigation bar and you will be presented with the following

.. image:: https://i.imgur.com/PrkO8oy.png

Understanding the Configuration Options
---------------------------------------
######
Server
######
Password
    * The password that clients will need to provide to be able to establish a connection with IPTVProxy
    * By default, the password is required for clients connecting through the Internet (See Optional Settings)
    * By default, the password is not required for clients connecting through the loopback interface or through the LAN (See Optional Settings)
HTTP Port Number
    * The port number IPTVProxy will listen on for incoming HTTP (Insecure) connections
    * The default port is 28080
    * Recommended value: Any unused port number between between 1024 and 65535
HTTPS Port Number
    * The port number IPTVProxy will listen on for incoming HTTPS (Secure) connections
    * The default port is 28443
    * A SSL certificate is required to start the HTTPS server (See SSL Certificate)
    * Recommended value: Any unused port number between between 1024 and 65535
Loopback Hostname
    * The loopback address of the machine on which IPTVProxy is running
    * The value specified will be used in generated playlists for clients connecting through the loopback interface
    * Can be a hostname or IP address
    * Recommended value: Either "loopback" or "127.0.0.1"
Private LAN Hostname
    * The private address of the machine on which IPTVProxy is running
    * The value specified will be used in generated playlists for clients connecting through the LAN
    * Can be a hostname or IP address
Public WAN Hostname
    * The public address of the machine on which IPTVProxy is running
    * The value specified will be used in generated playlists for clients connecting through the Internet
    * Can be a hostname or IP address

#####
Beast
#####
Username
    * The Beast account username
Password
    * The Beast account password
Playlist Protocol
    * By default IPTVProxy will generate playlists for the selected protocol
    * Can be overridden by the client (See below)
Playlist Type
    * By default IPTVProxy will generate playlists for the selected type
    * Can be overridden by the client (See below)
    * Recommended value: "Dynamic"
EPG Source
    * The source from which to retrieve the EPG
EPG URL
    * The URL to a XMLTV file to be used if EPG Source is set to "other"

############
CrystalClear
############
Username
    * The CrystalClear account username
Password
    * The CrystalClear account password
Playlist Protocol
    * By default IPTVProxy will generate playlists for the selected protocol
    * Can be overridden by the client (See below)
Playlist Type
    * By default IPTVProxy will generate playlists for the selected type
    * Can be overridden by the client (See below)
    * Recommended value: "Dynamic"
EPG Source
    * The source from which to retrieve the EPG
EPG URL
    * The URL to a XMLTV file to be used if EPG Source is set to "other"

#############
SmoothStreams
#############
Service
    * The SmoothStreams service IPTVProxy will connect to
Server
    * The SmoothStreams server IPTVProxy will connect to
Username
    * The SmoothStreams account username
Password
    * The SmoothStreams account password
Playlist Protocol
    * By default IPTVProxy will generate playlists for the selected protocol
    * Can be overridden by the client (See below)
Playlist Type
    * By default IPTVProxy will generate playlists for the selected type
    * Can be overridden by the client (See below)
    * Recommended value: "Dynamic"
EPG Source
    * The source from which to retrieve the EPG
EPG URL
    * The URL to a XMLTV file to be used if EPG Source is set to "other"

############
VaderStreams
############
Server
    * The VaderStreams server IPTVProxy will connect to
Username
    * The VaderStreams account username
Password
    * The VaderStreams account password
Playlist Protocol
    * By default IPTVProxy will generate playlists for the selected protocol
    * Can be overridden by the client (See below)
Playlist Type
    * By default IPTVProxy will generate playlists for the selected type
    * Can be overridden by the client (See below)
    * Recommended value: "Dynamic"

What Happened to My IPTV provider Password?
--------------------------------------------------------
IPTVProxy automatically encrypts the IPTV provider password in the configuration file.

The encryption key used to encrypt the password is automatically generated by IPTVProxy and stored within an internal storage repository

The encryption occurs in the following cases
1. On IPTVProxy startup, if IPTVProxy determines that the password in the configuration file is not encrypted.
2. Whenever the password is changed and IPTVProxy determines that the password in the configuration file is not encrypted

What Do I Do If I Lose My Encryption Key?
-----------------------------------------
If for any reason you lose your encryption key by deleting IPTVProxy's internal storage repository, you will need to re-input your IPTV provider password into the configuration file. IPTVProxy will generate a new encryption key and use that key to encrypt the password

SSL Certificate
---------------
To enable HTTPS, you need to get a certificate (a type of file) from a Certificate Authority (CA) or use a self-signed certificate.

* A certificate from a CA is a trusted certificate
    * `Let's Encrypt <https://letsencrypt.org/>`_ is a CA from which you can generate a trusted certificate for your Public WAN Hostname
    * Using a trusted certificate allows clients and browsers to automatically connect without displaying any warnings
* A self-signed certificate is an identity certificate that is signed by the same entity whose identity it certifies
    * IPTVProxy has functionality to generated a self-signed certificate for you (See Optional Settings)
    * Using a self-signed certificate will result in a warning similar to this one

    .. image:: https://i.imgur.com/JF5izG0.png

    * You can force your client to trust the self-signed certificate

    .. image:: https://i.imgur.com/oC8Yw8l.png

    * Some devices (e.g. Amazon Fire devices) do not give the user options to trust self-signed certificates, so there is no way to use a self-signed certificate with any client running on these devices

Optional Settings
=================
IPTVProxy looks for an optional JSON settings file called iptv_proxy_optional_settings.json. If this file is not found, or if any setting is missing then a safe default will be used

allow_insecure_lan_connections
    * Accepted values are true or false
    * The default value is true
    * Setting this value to true allows clients connecting through the loopback interface or LAN to connect using the HTTP protocol and port
    * Setting this value fo false will block clients connecting through the loopback interface or LAN from connecting using the HTTP protocol and port
        * Connections must be made using the HTTPS protocol and port
allow_insecure_wan_connections
    * Accepted values are true or false
    * The default value is false
    * Setting this value to true allows clients connecting through the Internet to connect using the HTTP protocol and port (Not recommended)
    * Setting this value fo false will block clients connecting through the Internet from connecting using the HTTP protocol and port
        * Connections must be made using the HTTPS protocol and port
auto_generate_self_signed_certificate
    * Accepted values are true or false
    * The default value is true
        * Setting this value to true will result in IPTVProxy generating a new self-signed certificate every time it determines a change in any of the hostname (Loopback, Private, or Public) options in the configuration file
        * Setting this value fo false will result in IPTVProxy not generating a self-signed certificate
            * Set it to false if you plan to use a certificate generated from a CA
cache_downloaded_segments
    * Accepted values are true or false
    * The default value is true
        * Setting this value to true will result in IPTVProxy enabling the cache thus preventing duplicate segments from being downloaded
        * Setting this value fo false will result in IPTVProxy disabling the cache
lan_connections_require_credentials
    * Accepted values are true or false
    * The default value is false
    * Setting this value to true requires clients connecting through the loopback interface or LAN to authenticate themselves using the value specified in the Password option in the configuration file
    * Setting this value fo false does not require clients connecting through the loopback interface or LAN to authenticate themselves
reduce_provider_delay
    * Providers supported are beast, crystalclear, and vaderstreams
    * Accepted values are true or false
    * The default value is false
    * Setting this value to true reduces the delay in the HLS stream. This is done by skipping all but the last 2-3 segment files on a new channel request
    * Setting this value fo false maintains the delay
provider_channel_name_map
    * Providers supported are beast, crystalclear, smoothstreams, and vaderstreams
    * Accepted value is a JSON object
    * Setting this value to a non empty JSON object will result in IPTVProxy mapping of the providers channel names
use_provider_icons
    * Providers supported are beast, crystalclear, smoothstreams, and vaderstreams
    * Accepted values are true or false
    * The default value is true
    * Setting this value to true will result in IPTVProxy directing clients to download the original channel icons provided by the provider
    * Setting this value fo false will result in IPTVProxy directing clients to download the channel icons that come with IPTVProxy
wan_connections_require_credentials
    * Accepted values are true or false
    * The default value is true
    * Setting this value to true requires clients connecting through the Internet to authenticate themselves using the password specified in the Password option in the configuration file
    * Setting this value fo false does not require clients connecting through the Internet to authenticate themselves (Not recommended)

URLs
====
Configure your preferred client with the following URLs

Live Playlist URL
    * http<s>://<IP Address>:<Port>/live/playlist.m3u8?http_token=<TP>
        * By default this URL will generate a playlist based on the values of Protocol and Type options specified in the configuration file
        * Query String Parameters
            * protocol=<protocol>
                * Optional
                * Defaults to the value of the Protocol option in the configuration file
                * Replace <protocol> with either "hls" or "rtmp"
            * http_token=<http_token>
                * Required by clients connecting through the loopback interface or LAN if lan_connections_require_credentials is true
                * Required by clients connecting through the Internet if wan_connections_require_credentials is true
                * Replace <http_token> with the value of the Password option in the configuration file
            * type=<type>
                * Optional
                * Defaults to the value of the Type option in the configuration file
                * Replace <type> with either "dynamic" or "static"
            * Examples
                * http<s>://<IP Address>:<Port>/live/playlist.m3u8?protocol=rtmp&type=dynamic will result in a dynamically generated playlist containing RTMP links
                * http<s>://<IP Address>:<Port>/live/playlist.m3u8?protocol=rtmp will result in a generated playlist containing RTMP links. Whether this will be a Dynamic or Static playlist will be determined based on the value of Type specified in the configuration file
                * http<s>://<IP Address>:<Port>/live/playlist.m3u8?type=static will result in a generated playlist containing static links. Whether this will be an HLS or RTMP playlist will be determined based on the value of Protocol specified in the configuration file
VOD Playlist URL (Perfect Player supports VOD Playlists)
    * http<s>://<IP Address>:<Port>/vod/playlist.m3u8
        * Query String Parameters
            * http_token=<http_token>
                * Required by clients connecting through the loopback interface or LAN if lan_connections_require_credentials is true
                * Required by clients connecting through the Internet if wan_connections_require_credentials is true
                * Replace <http_token> with the value of the Password option in the configuration file
EPG URL
    * http<s>://<IP Address>:<Port>/live/epg.xml
        * By default this will retrieve the EPG for the next 24 hours
        * Query String Parameters
            * number_of_days=<number_of_days>
                * Optional
                * The default is 1 day
                * Replace <number_of_days> the number of days you want the retrieved EPG to span
            * http_token=<http_token>
                * Required by clients connecting through the loopback interface or LAN if lan_connections_require_credentials is true
                * Required by clients connecting through the Internet if wan_connections_require_credentials is true
                * Replace <http_token> with the value of the Password option in the configuration file
            * style=<style>
                * Optional
                * The default is minimal
                * Replace <style> with complete to have the EPG generated by IPTVProxy include all available tags
        * Examples
            * http<s>://<IP Address>:<Port>/live/epg.xml?number_of_days=3 will retrieve the EPG for the next 3 days (72 hours)
            * http<s>://<IP Address>:<Port>/live/epg.xml?number_of_days=5 will retrieve the EPG for the next 5 days (120 hours)

Web Interface
=============
IPTVProxy comes with a rich web interface. To access the web interface browse to http://<IP Address>:<Port>/index.html

The web interface has mainly been tested on a PC with Firefox but should reliably work across most modern browsers and scale well regardless of the device screen size albeit with some changes in the way the UI is presented

Guide
-----
.. image:: https://i.imgur.com/ovwC0SB.png

From the Guide page you are able to:

Search for a program
    .. image:: https://i.imgur.com/gpUnq3g.png
Start playing a channel
    .. image:: https://i.imgur.com/wOxdgFM.png
Schedule a recording (Once a program is recorded it either becomes a Live recording if it is already in progress or a Scheduled recording if it is a future dated program)
    .. image:: https://i.imgur.com/SRh65QJ.png
    .. image:: https://i.imgur.com/PiNztqa.png

Recordings
----------
Recordings are divided into 3 types

Live
    * Recordings that are currently in progress
    * Can be stopped (Once a live recording completes or is manually stopped it becomes a Persisted recording)
Persisted
    * Recordings that have completed and are available for playback
    * Can be deleted
Scheduled
    * Recordings that are scheduled
    * Can be deleted

.. image:: https://i.imgur.com/qQpvoBo.png

Configuration
-------------
.. image:: https://i.imgur.com/PrkO8oy.png

Monitor
-------
Coming soon...

Settings
--------
From the Settings dialog you can configure the following options

EPG -> Days
    * The number of days that the Guide web interface will display
    * By default, the number is set to 1
    * A larger number will result in a larger page which can result in
        * A slightly slower browser
        * A slower search

EPG -> Sorting
    * The criteria on which the guide is sorted

    .. image:: https://i.imgur.com/6qxRADk.png

Streaming -> Protocol
    * The protocol to use to play live videos
    * Note that RTMP is not available on mobile devices

    .. image:: https://i.imgur.com/xRQ3URZ.png

Changes to Settings are applied as soon as the Settings dialog is closed

Playing Recordings Using Perfect Player
=======================================
To have Perfect Player play your recordings you first have to configure a VOD playlist as follows

* Set the URL to the VOD playlist URL (See URLs above)
* Select M3U
* Check the VOD option

.. image:: https://i.imgur.com/UM6ICab.png

You then need to instruct Perfect Player to display the VOD playlist content

* Open Perfect Player menu and select the highlighted icon

.. image:: https://i.imgur.com/L1K4zcs.png

* Scroll down to the VOD option

.. image:: https://i.imgur.com/4P1uDjL.jpg

* If you have any recordings to replay, then Perfect Player will display the available recordings

.. image:: https://i.imgur.com/jTlp7eM.jpg

Selecting any of the available recordings will start playing it

To return back to the live TV playlist repeat the above steps and select the IPTV option instead of the VOD option