import socketio
import time

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('client connected')

@sio.event
def disconnect():
    print('client disconnected')

@sio.on('connected')
def on_connected(data):
    print('connected event', data)

@sio.on('status')
def on_status(data):
    print('status event', data)

@sio.on('prediction')
def on_prediction(data):
    print('prediction event', data)

if __name__ == '__main__':
    try:
        sio.connect('http://localhost:5001')
        time.sleep(1)
        print('sending start_monitoring')
        sio.emit('start_monitoring')
        time.sleep(2)
        print('sending stop_monitoring')
        sio.emit('stop_monitoring')
        time.sleep(2)
    except Exception as e:
        print('error', e)
    finally:
        sio.disconnect()
