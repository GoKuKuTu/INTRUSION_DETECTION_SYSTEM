const io = require('socket.io-client');
const socket = io('http://localhost:5000', { transports: ['websocket','polling'] });

socket.on('connect', () => {
  console.log('connected', socket.id);
  socket.emit('start_monitoring');
});

socket.on('disconnect', () => {
  console.log('disconnected');
});

socket.on('connected', (data) => {
  console.log('server connected message', data);
});

socket.on('prediction', (data) => {
  console.log('prediction:', data);
});

socket.on('status', (data) => {
  console.log('status:', data);
});

setTimeout(() => {
  console.log('closing after 20s');
  socket.close();
  process.exit(0);
}, 20000);
