from flask import Flask,render_template,request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import random
import time

app = Flask(__name__)

app.secret_key = "beatsync_secret_key_gg"
socketio = SocketIO(app, async_mode="eventlet")

# Empty Dict for listing the rooms and rooms<ID>
rooms = {}

# Generate the unqiue room <ID>
def generate_room_code():
    while True:
        code = f"{random.randint(0,999999):06d}"
        if code not in rooms:
            return code 

#for rendering the join.html page
@app.route("/")
def home():
    return render_template("index/join.html")

# if the user click on the create button
@app.route("/create", methods=["POST"])
def room_create():
    code = generate_room_code()
    rooms[code] = {
        "update":0,
        "status":"paused",
        "time":0,
        "is_playing":False,
        "video_ID":"#videoelementID",
    }
    return redirect(url_for("room", room_code=code))


# to check if room exist or not 
@app.route("/room/<room_code>")
def room(room_code):
    if room_code not in rooms:
        return "ERROR: Room not found",404
    return render_template("index/room.html", room_code=room_code)

#Socket IO event 
@socketio.on("join")
def handle_join(data):
    room_code = data["room"]
    join_room(room_code)
    if room_code not in rooms:
        rooms[room_code] = {
            "user":[],
            "status":"paused",
            "time":0,
        }
    if room in rooms:
        emit("sync_state", rooms[room], to=request.sid)

    current_user = rooms[room_code]["user"]

    if len(current_user) >= 4:
        return emit("ERROR", {"Message":"Room is full",},  room=request.sid )
         
    
    user_number = len(current_user) + 1
    user_id = f"User {user_number}"

    current_user.append({"sid": request.sid, "name": user_id})

    emit("your_identity", {"name": user_id, "is_admin":(user_number ==  1)}, room=request.sid)

    user_names = [u['name'] for u in current_user] # ['User 1', 'User 2']
    emit('room_update', {'users': user_names}, room=room_code)

@socketio.on("videochange")
def on_videochange(data):
    room = data["room"]
    video_id = data["videoid"]

    rooms[room]["current_video_id"] = video_id
    rooms[room]["time"] = 0
    rooms[room]["is_playing"] = True
    rooms[room]["update"] = time.time()

    emit("load_video", {"videoid": video_id}, to=room)


@socketio.on('play')
def handle_play(data):
    room_code = data['room']
    action = data["action"]
    current_time = data["current_time"]
    emit("sync_action",{
        "action":action,
        "current_time":current_time,
    }, to=room, include_self=False)

    rooms[rooms]["is_playing"] = (action == "play")
    rooms[room]["update"] = time.time()
    rooms[room]["time"] = current_time

# running server 
if __name__ == "__main__":
    socketio.run(app, debug=True)
