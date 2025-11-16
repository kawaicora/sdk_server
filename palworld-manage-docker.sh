docker run -d --name pst \
-p 28080:8080 \
-v /opt/1panel/apps/palworld/palworld/data/SaveGames:/game \
-v ./backups:/app/backups \
-e WEB__PASSWORD="Virus@1994~" \
-e RCON__ADDRESS="10.0.0.25:25575" \
-e RCON__PASSWORD="" \
-e REST__ADDRESS="http://10.0.0.25:8212" \
-e REST__PASSWORD="" \
-e SAVE__PATH="/game" \
-e SAVE__SYNC_INTERVAL=120 \
jokerwho/palworld-server-tool:latest
