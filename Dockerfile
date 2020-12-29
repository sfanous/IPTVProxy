FROM alpine
RUN apk update
RUN apk upgrade
RUN apk add gcc
RUN apk add libffi-dev
RUN apk add libxml2-dev
RUN apk add libxslt-dev
RUN apk add musl-dev
RUN apk add openssl-dev
RUN apk add python3
RUN apk add python3-dev
RUN apk add py3-pip
RUN apk add sudo
RUN apk add tzdata

RUN addgroup iptv_proxy && adduser --disabled-password --gecos iptv_proxy --home /home/iptv_proxy --ingroup iptv_proxy iptv_proxy
RUN echo "iptv_proxy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER iptv_proxy

RUN mkdir /home/iptv_proxy/IPTVProxy
RUN chmod 755 /home/iptv_proxy/IPTVProxy
RUN mkdir /home/iptv_proxy/IPTVProxy/conf
RUN chmod 755 /home/iptv_proxy/IPTVProxy/conf
RUN mkdir /home/iptv_proxy/IPTVProxy/db
RUN chmod 755 /home/iptv_proxy/IPTVProxy/db
RUN mkdir /home/iptv_proxy/IPTVProxy/logs
RUN chmod 755 /home/iptv_proxy/IPTVProxy/logs
RUN mkdir /home/iptv_proxy/IPTVProxy/recordings
RUN chmod 755 /home/iptv_proxy/IPTVProxy/recordings
RUN mkdir /home/iptv_proxy/IPTVProxy/ssl
RUN chmod 755 /home/iptv_proxy/IPTVProxy/ssl
RUN mkdir /home/iptv_proxy/IPTVProxy/ssl/certificate
RUN chmod 755 /home/iptv_proxy/IPTVProxy/ssl/certificate
RUN mkdir /home/iptv_proxy/IPTVProxy/ssl/key
RUN chmod 755 /home/iptv_proxy/IPTVProxy/ssl/key
COPY --chown=iptv_proxy:iptv_proxy iptv_proxy /home/iptv_proxy/IPTVProxy/iptv_proxy
RUN find /home/iptv_proxy/IPTVProxy/iptv_proxy -type f -exec chmod 444 {} \;
COPY --chown=iptv_proxy:iptv_proxy resources /home/iptv_proxy/IPTVProxy/resources
RUN find /home/iptv_proxy/IPTVProxy/resources -type f -exec chmod 444 {} \;
COPY --chown=iptv_proxy:iptv_proxy templates /home/iptv_proxy/IPTVProxy/templates
RUN find /home/iptv_proxy/IPTVProxy/templates -type f -exec chmod 444 {} \;
COPY --chown=iptv_proxy:iptv_proxy HISTORY.rst /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/HISTORY.rst
COPY --chown=iptv_proxy:iptv_proxy iptv_proxy_logging_configuration_sample.json /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/iptv_proxy_logging_configuration_sample.json
COPY --chown=iptv_proxy:iptv_proxy iptv_proxy_optional_settings.json /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/iptv_proxy_optional_settings.json
COPY --chown=iptv_proxy:iptv_proxy iptv_proxy_runner.py /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/iptv_proxy_runner.py
COPY --chown=iptv_proxy:iptv_proxy LICENSE /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/LICENSE
COPY --chown=iptv_proxy:iptv_proxy README.rst /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/README.rst
COPY --chown=iptv_proxy:iptv_proxy requirements.txt /home/iptv_proxy/IPTVProxy/.
RUN chmod 444 /home/iptv_proxy/IPTVProxy/requirements.txt

RUN sudo pip install wheel
RUN sudo pip install -r /home/iptv_proxy/IPTVProxy/requirements.txt

ENV IPTV_PROXY_DIRECTORY_PATH="/home/iptv_proxy/IPTVProxy"
ENV IPTV_PROXY_EXECUTABLE_PATH="$IPTV_PROXY_DIRECTORY_PATH/iptv_proxy_runner.py"
ENV IPTV_PROXY_CONFIGURATION_FILE_PATH="$IPTV_PROXY_DIRECTORY_PATH/conf/iptv_proxy.ini"
ENV IPTV_PROXY_OPTIONAL_SETTINGS_FILE_PATH="$IPTV_PROXY_DIRECTORY_PATH/conf/iptv_proxy_optional_settings.json"
ENV IPTV_PROXY_LOG_FILE_PATH="$IPTV_PROXY_DIRECTORY_PATH/logs/iptv_proxy.log"
ENV IPTV_PROXY_RECORDINGS_DIRECTORY_PATH="$IPTV_PROXY_DIRECTORY_PATH/recordings"
ENV IPTV_PROXY_DB_FILE_PATH="$IPTV_PROXY_DIRECTORY_PATH/db/iptv_proxy_db"
ENV IPTV_PROXY_CERTIFICATE_FILE_PATH="/home/iptv_proxy/IPTVProxy/ssl/certificate/fullchain.pem"
ENV IPTV_PROXY_KEY_FILE_PATH="/home/iptv_proxy/IPTVProxy/ssl/key/privkey.pem"
ENV TZ Etc/UTC

ENTRYPOINT sudo python3 $IPTV_PROXY_EXECUTABLE_PATH -c $IPTV_PROXY_CONFIGURATION_FILE_PATH -l $IPTV_PROXY_LOG_FILE_PATH -r $IPTV_PROXY_RECORDINGS_DIRECTORY_PATH -d $IPTV_PROXY_DB_FILE_PATH -os $IPTV_PROXY_OPTIONAL_SETTINGS_FILE_PATH -sc $IPTV_PROXY_CERTIFICATE_FILE_PATH -sk $IPTV_PROXY_KEY_FILE_PATH