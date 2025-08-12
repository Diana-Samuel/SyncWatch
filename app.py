from flask_socketio import join_room, emit, SocketIO
from flask import Flask, render_template, jsonify

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
        "message": json.dumps([])
    }

    return jsonify({"status": True, "roomId": roomId})

@socket.on("joinRoom")
def joinroom(data):
    roomId = data["roomId"]
    try:
        cache = Cache[roomId]
        cache["numberOfUsers"] += 1
        Cache[roomId] = cache
        
    except KeyError:
        Cache[roomId] = {
                "videoLength": 0,
                "paused": 0,
                "inDuration": 0,
                "md5": "",
                "numberOfUsers": 1,
                "messsage": json.dumps([])
            }
    join_room(roomId)

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




if __name__ == "__main__":
    socket.run(app,debug=True,port=5000)