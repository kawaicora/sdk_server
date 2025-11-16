from flask_socketio import emit
from app.route import bp
from flask import *
from uuid import UUID
from app.extensions import db,socketio

@socketio.on('cabbagedog-sync-connect')
def handle_sync_connect(data):
    current_app.logger.info(data)
    uuid = UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
    emit('cabbagedog-sync-connected', {'uuid': str(uuid)})