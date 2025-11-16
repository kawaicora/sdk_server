docker run -d --network=host \
           -v /opt/1pannel/apps/sdk_server/sdk_server/turnserver.conf:/etc/coturn/turnserver.conf \
       instrumentisto/coturn
