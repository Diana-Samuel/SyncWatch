from flask_socketio import join_room, leave_room, emit, SocketIO
from flask import Flask, render_template, jsonify, request

import pickle
import utils
import json

app = Flask(__name__)
socket = SocketIO(app)

Cache = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/createRoom")
def createRoom():
    roomId = str(utils.randomid(10))

    Cache[roomId] = {
        "videoLength": 0,
        "paused": 0,
        "inDuration": 0,
        "md5": "",
        "numberOfUsers": 0,
        "message": json.dumps([]),
        "users": json.dumps({})
    }

    return jsonify({"status": True, "roomId": roomId})

@socket.on("joinRoom")
def joinroom(data):
    roomId = data["roomId"]
    sid = request.sid

    try:
        cache = Cache[roomId]
        cache["numberOfUsers"] += 1
        users = cache["users"]
        users = json.loads(users)
        users[sid] = {"userName": "","muted": False}
        cache["users"] = json.dumps(users)
        Cache[roomId] = cache

        
    except KeyError:
        Cache[roomId] = {
                "videoLength": 0,
                "paused": 0,
                "inDuration": 0,
                "md5": "",
                "numberOfUsers": 1,
                "messsage": json.dumps({}),
                "users": json.dumps({sid: {"userName": "","muted": False}})
            }
    join_room(roomId)

    room_members = list(socket.server.manager.get_participants('/', roomId))
    other_users = [user for user in room_members if user != sid]

    emit("peersInRoom", {"peers": other_users}, room=sid)


@socket.on("leaveRoom")
def leaveroom(data):
    roomId = data["roomId"]
    sid = request.sid

    cache = Cache[roomId]
    users = cache["users"]
    users = json.loads(users)
    del users[sid]
    cache["users"] = json.dumps(users)
    cache[roomId] = cache

    leave_room(roomId)

    room_members = list(socket.server.manager.get_participants('/', roomId))
    other_users = [user for user in room_members if user != sid]

    emit("peersInRoom", {"peers": other_users}, room=sid)

@socket.on('signal')
def handle_signal(data):
    room = data['room']
    target = data['target']
    emit('signal', data, room=target, include_self=False)

@socket.on("sendMetaData")
def setmetadata(data):
    roomId = data["roomId"]
    fileData = pickle.loads(data["file"])
    try:
        cache = Cache[roomId]

        cache["paused"] = 1
        cache["videoLength"] = int(float(fileData["duration"]))
        cache["inDuration"] = 0
        cache["md5"] = fileData["md5"]

        Cache[roomId] = cache


    except KeyError:
        cache = {}
        cache["paused"] = 1
        cache["videoLength"] = int(float(fileData["duration"]))
        cache["inDuration"] = 0
        cache["md5"] = fileData["md5"]
        cache["users"] = json.dumps({})
        Cache[roomId] = cache


@socket.on("next10")
def add10sec(data):
    roomId = data["roomId"]
    duration = data["duration"]
    cache = Cache[roomId]
    cache["inDuration"] = duration
    cache["inDuration"] += 10
    if int(cache["inDuration"]) >= int(cache["videoLength"]):
        cache["inDuration"] = cache["videoLength"]
    Cache[roomId] = cache
    emit("setDuration",{"inDuration": cache["inDuration"]},room=roomId)

@socket.on("prev10")
def rem10sec(data):
    roomId = data["roomId"]
    duration = data["duration"]
    cache = Cache[roomId]
    cache["inDuration"] = duration
    cache["inDuration"] -= 10
    if cache["inDuration"] <= 0:
        cache["inDuration"] = 0
    Cache[roomId] = cache
    emit("setDuration",{"inDuration": cache["inDuration"]},room=roomId)

@socket.on("pause")
def pause(data):
    roomId = data["roomId"]
    cache = Cache[roomId]
    if cache:
        paused = cache["paused"]
        if bool(paused):
            cache["paused"] = 0
        else:
            cache["paused"] = 1

        Cache[roomId] = cache
        emit("pauseApply",{"status": cache["paused"]},room=roomId)
    else:
        emit("pauseApply",{"status": 1}, room=roomId)

@socket.on("send_message")
def sendMessage(data):
    roomId = data["roomId"]
    name = data["name"]
    message = data["message"]

    cache = Cache[roomId]
    if cache:
        msgInfo = {
            "name": name,
            "message": message
        }
        messagesJson = json.loads(cache["message"])
        messagesJson.append(msgInfo)
        cache["message"] = json.dumps(messagesJson)
        Cache[roomId] = cache
        emit("receive_message",msgInfo,room=roomId)
    else:
        emit("error",{"Error": "no cache found"},room=roomId)


@socket.on("getOldMessages")
def getoldmessages(data):
    roomId = data["roomId"]
    name = data["name"]

    cache = Cache[roomId]

    if cache:
        messages = json.loads(cache["message"])
        emit("receiveOldMessages",{"messages": messages,"requestedBy": name},roomId=roomId)
    else:
        emit("receiveOldMessages",{"messages": [],"requestedBy": name},room=roomId)


@socket.on("mute")
def setmute(data):
    roomId = data["roomId"]
    username = data["name"]
    sid = request.sid

    cache = Cache[roomId]
    users = json.loads(cache["users"])
    users[sid]["muted"] = not users[sid]["muted"]
    users[sid]["userName"] = username
    cache["users"] = json.dumps(users)

    Cache[roomId] = cache

@socket.on("getUsers")
def getUsers(data):
    roomId = data["roomId"]
    sid = request.sid

    cache = Cache[roomId]
    users = json.loads(cache["users"])
    users[sid]["userName"] = data["name"]
    cache["users"] = json.dumps(users)
    Cache[roomId] = cache
    editedUsers = []
    for i,(key,value) in enumerate(users.items()):
        editedUsers.append({"name": value["userName"], "muted": value["muted"]})

    emit("returnGetUsers",{"users": editedUsers},room=roomId)

if __name__ == "__main__":
    socket.run(app,debug=True,port=5000, host="0.0.0.0")