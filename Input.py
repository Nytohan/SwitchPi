import Controller
from Controller import SwitchController
import time
import socketio
import threading

Threads = []

sc = SwitchController(StickDefaults = { "LX": 1.85, "LY": 1.85, "RX": 1.85, "RY": 1.85 })
sio = socketio.Client()
sio.connect("http://localhost")

@sio.on('connected')
def on_connected():
    print("Connected!")
    sio.emit("CONTROLLER", "Exists!")

@sio.on('FUNCTION')
def on_function(msg):
    if(msg == "CENTER_STICKS"):
        sc.ResetSticks()

@sio.on('HOLD')
def on_hold(msg):
    print("Holding {}".format(msg))
    if(msg != 'WAKE'):
        sc.Hold(msg)
    else:
        sc.WakeUp()

@sio.on('RELEASE')
def on_hold(msg):
    print("Releasing {}".format(msg))
    if(msg != 'WAKE'):
        sc.Release(msg)

@sio.on('macro')
def on_macro():
    t = threading.Thread(target=target_function,name=name,args=(args))



def main():
    while(True):
        pass




if __name__== "__main__":
    try:
        main()
    except:
        pass
