const socket = io("http://localhost:5000");

const audio = document.getElementById("audioPlayer");
const ROOM_CODE = window.location.pathname.split("/").pop();

let isAdmin = false;

// JOIN ROOM

socket.emit("join", {
    room: ROOM_CODE
});


// RECEIVE IDENTITY

socket.on("your_identity", (data) => {
    isAdmin = data.is_admin;
    console.log("You are:", data.name, "Admin:", isAdmin);
});

// SYNC STATE WHEN JOINING

socket.on("sync_state", (state) => {
    audio.currentTime = state.time;
    if (state.is_playing) {
        audio.play();
    } else {
        audio.pause();
    }
});


// ADMIN CONTROLS → SERVER

audio.addEventListener("play", () => {
    if (!isAdmin) return;
    socket.emit("play", {
        room: ROOM_CODE,
        time: audio.currentTime
    });
});

audio.addEventListener("pause", () => {
    if (!isAdmin) return;
    socket.emit("pause", {
        room: ROOM_CODE,
        time: audio.currentTime
    });
});

audio.addEventListener("seeked", () => {
    if (!isAdmin) return;
    socket.emit("seek", {
        room: ROOM_CODE,
        time: audio.currentTime
    });
});


// SYNC USERS

socket.on("play", (data) => {
    if (isAdmin) return;
    audio.currentTime = data.time;
    audio.play();
});

socket.on("pause", (data) => {
    if (isAdmin) return;
    audio.currentTime = data.time;
    audio.pause();
});

socket.on("seek", (data) => {
    if (isAdmin) return;
    audio.currentTime = data.time;
});

//
socket.on("user_count", (count) => {
    if (!isAdmin && count < 2) {
        audio.pause();
    }
});