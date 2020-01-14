
module.exports = function(socket) {

socket.on("HOLD", function(msg){
  console.log(socket.id + " HOLD: " + msg)
  socket.io.mycontroller.emit("HOLD", msg)
})

socket.on("RELEASE", function(msg){
  console.log(socket.id + " RELEASE: " + msg)
  socket.io.mycontroller.emit("RELEASE", msg)
})

socket.on("CONTROLLER", function(msg){
    socket.io.mycontroller = socket
    console.log(socket.id + ": IS THE CONTROLLER")
})

socket.on("FUNCTION", function(msg){
    console.log(socket.id + " FUNCTION: " + msg)
    socket.io.mycontroller.emit("FUNCTION", msg)
})

};
