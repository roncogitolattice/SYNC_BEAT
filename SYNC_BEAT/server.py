from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import random
import time

app = Flask(__name__)
app.secret_key = "beatsync_secret_key_gg"
socketio = SocketIO(app, async_mode="eventlet")

# Empty Dict for listing the rooms and rooms<ID>
rooms = {}

# Generate the unique room <ID>
def generate_room_code():
    while True:
        code = f"{random.randint(0,999999):06d}"
        if code not in rooms:
            return code 

# For rendering the join.html page
@app.route("/")
def home():
    return render_template("index/join.html")

# If the user clicks on the create button
@app.route("/create", methods=["POST"])
def room_create():
    code = generate_room_code()
    rooms[code] = {
        "user": [],  # ✅ Added missing "user" key
        "update": 0,
        "status": "paused",
        "time": 0,
        "is_playing": False,
        "video_ID": "#videoelementID",
        "current_video_id": None  # ✅ Added for videochange
    }
    return redirect(url_for("room", room_code=code))

# To check if room exists or not 
@app.route("/room/<room_code>")
def room(room_code):
    if room_code not in rooms:
        return "ERROR: Room not found", 404
    return render_template("index/room.html", room_code=room_code)

# Socket IO events 
@socketio.on("join")
def handle_join(data):
    room_code = data["room"]
    join_room(room_code)
    
    # Initialize room if not exists
    if room_code not in rooms:
        rooms[room_code] = {
            "user": [],
            "status": "paused",
            "time": 0,
            "is_playing": False,
            "update": 0
        }
    
    # ✅ FIXED: Use room_code instead of undefined 'room'
    if room_code in rooms:
        emit("sync_state", rooms[room_code], to=request.sid)

    current_user = rooms[room_code]["user"]

    if len(current_user) >= 4:
        emit("ERROR", {"Message": "Room is full"}, room=request.sid)
        return 
    
    user_number = len(current_user) + 1
    user_id = f"User {user_number}"

    current_user.append({"sid": request.sid, "name": user_id})

    emit("your_identity", {"name": user_id, "is_admin": (user_number == 1)}, room=request.sid)

    user_names = [u['name'] for u in current_user]
    emit('room_update', {'users': user_names}, room=room_code)

@socketio.on("videochange")
def on_videochange(data):
    room_code = data["room"]  # ✅ FIXED: Use room_code consistently
    video_id = data["videoid"]

    if room_code in rooms:
        rooms[room_code]["current_video_id"] = video_id  # ✅ FIXED
        rooms[room_code]["time"] = 0
        rooms[room_code]["is_playing"] = True
        rooms[room_code]["update"] = time.time()

        emit("load_video", {"videoid": video_id}, room=room_code)  # ✅ FIXED: Use room_code

@socketio.on('play')
def handle_play(data):
    room_code = data['room']
    action = data["action"]
    current_time = data["current_time"]
    
    if room_code in rooms:
        # ✅ FIXED: Use room_code everywhere
        emit("sync_action", {
            "action": action,
            "current_time": current_time,
        }, room=room_code, include_self=False)  # ✅ FIXED

        rooms[room_code]["is_playing"] = (action == "play")  # ✅ FIXED
        rooms[room_code]["update"] = time.time()  # ✅ FIXED
        rooms[room_code]["time"] = current_time  # ✅ FIXED

@socketio.on('pause')
def handle_pause(data):
    room_code = data['room']
    if room_code in rooms:
        rooms[room_code]["is_playing"] = False
        rooms[room_code]["time"] = data["current_time"]
        emit("sync_action", {
            "action": "pause",
            "current_time": data["current_time"]
        }, room=room_code, include_self=False)

@socketio.on('seek')
def handle_seek(data):
    room_code = data['room']
    if room_code in rooms:
        rooms[room_code]["time"] = data["current_time"]
        emit("seek", data, room=room_code, include_self=False)

# Running server 
if __name__ == "__main__":
    socketio.run(app, debug=True)
