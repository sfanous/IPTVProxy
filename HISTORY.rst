.. :changelog:

Release History
===============
5.1.0 (22-09-2018)
------------------
* Fix VaderStreams EPG

5.0.0 (15-05-2018)
------------------
* Project renamed to IPTVProxy

4.0.0 (13-05-2018)
------------------
* Add security features
    * HTTPS server which is required by default for all WAN connections
    * Password which is required by default for all WAN connections
* Refactor JSON API into a separate module
* Various bug fixes

3.6.0 (03-05-2018)
------------------
* Refactor multithreading to be based on ThreadingMixIn instead of previous approach
* Various bug fixes

3.5.1 (02-05-2018)
------------------
* Code improvements

3.5.0 (01-05-2018)
------------------
* Add ability to generate either dynamic or static playlists

3.4.0 (01-05-2018)
------------------
* Retrieve a fresh hash before generating an RTMP playlist
    * Playlist will be valid for 4 hours

3.3.1 (01-05-2018)
------------------
* Code improvements

3.3.0 (01-05-2018)
------------------
* Redirect requests to "/" and "index.htm" to "index.html"
* Set the cookies path to "index.html"

3.2.2 (01-05-2018)
------------------
* Client IDs are generated based on source IP address and browser's user agent

3.2.1 (01-05-2018)
------------------
* Code cleanup and refactoring

3.2.0 (30-04-2018)
------------------
* Playback of recordings from the web UI is now possible
    * Seeking (Forward and Rewind) seems to be randomly problematic.
        * If you attempt to seek and end up with a spinning wheel then attempting a second seek usually fixes the issue.
        * Seeking by drag the progress bar works more reliably then seeking by clicking on the progress bar


3.1.0 (28-04-2018)
------------------
* Add a ts files cache
    * If more than 1 client is tuned to the same channel then all clients will request the same ts files
    * In an effort to conserve the proxy bandwidth as well as SmoothStreams server load, this functionality will ensure that a ts file is only downloaded once and then served from the cache for all subsequent requests.
    * ts files can either be cached in memory (preferred option) or on disk (for memory strapped devices). See iptv_proxy_optional_settings.json

3.0.0 (26-04-2018)
------------------
* Serve awesome HTML pages. Start the proxy and navigate to http://<hostname>:<port>
    * View all channels and scheduled programs
    * Play channels
    * Schedule recording of programs
    * Search for programs
    * Manage recordings
    * Update configuration
* Add optional settings file (iptv_proxy_optional_settings.json)
    * channel_name_map
        * Use it to map SmoothStreams/Fog channel names to clearer names
    * use_smooth_streams_icons
        * true to use the channel icons provided by SmoothStreams
        * false to use icons provided by SmoothStreamsProxy
* Add EPG source configuration parameter
* Significant refactoring into more modules
* Various bug fixes

2.5.1 (25-03-2018)
------------------
* Expand recordings REST API error messages to contain a message aimed at developers and a message aimed at users
* Various bug fixes

2.5.0 (23-03-2018)
------------------
* Migrate recordings REST API to `JSON API <http://jsonapi.org/>`_
* Expand the scope of actions taken following configuration file modifications. Previously only changes to the level option were handled.
* Move from ConfigParser to ConfigObj
* Incorporate Cerberus library to validate recordings JSON API requests
* Various bug fixes
* Significant refactoring including splitting the monolithic module into multiple modules with clear separation of concerns

2.0.1 (09-03-2018)
------------------
* Various bug fixes

2.0.0 (08-03-2018)
------------------
* Added the ability to record and playback recorded streams through a VOD HLS playlist. At this point in time managing recordings is through plain REST calls.

1.2.3 (03-03-2018)
------------------
* Improve parsing of command line arguments

1.2.2 (02-03-2018)
------------------
* Fixed a bug where the channel_number and client_uuid were not being added to the chunks.m3u8 link after hijacking the Nimble session
* Fixed a bug where the watchdog path being monitored for configuration file modifications was always set to the script's current working directory. Now the watchdog path being monitored is the full path to the parent folder of the configuration file
* Significant refactoring and various other minor bug fixes

1.2.1 (01-03-2018)
------------------
* Code refactoring and various bug fixes

1.2.0 (28-02-2018)
------------------
* Added nimble session "hijacking"
    * The chunks.m3u8 link returned by SmoothStreams contains 2 parameters (nimblesessionid & wmsAuthSign)
    * wmsAuthSign is the authorization hash
    * The chunks.m3u8 link is only updated if a user switches to a different channel. As long as the same channel is being watched, the same chunks.m3u8 link is being used
    * As a result if the authorization hash expires while a channel is being watched the stream will stop until the user switches channels to retrieve a new authorization hash
    * The functionality added is to prevent this from happening by manipulating the values of the 2 parameters (nimblesessionid & wmsAuthSign) to valid values
* Code refactoring and various bug fixes

1.1.0 (27-02-2018)
------------------
* Added validations when parsing the configuration file along with error messages
* Added a timer that will automatically retrieve a new authorization hash
    * The timer will trigger 45 seconds before the authorization hash is set to expire
    * If a new authorization hash is retrieved by a client request (As a result of a request to http://<hostname>:<port>/playlist.m3u8?channel_number=XX) then the current timer is cancelled and a new timer is initiated
* Added watchdog functionality that will monitor the configuration file for modifications
* Added functionality to obfuscate/encrypt the password in the configuration file following the first run
* Lots of refactoring and various bug fixes

1.0.0 (24-02-2018)
------------------
* First public release
