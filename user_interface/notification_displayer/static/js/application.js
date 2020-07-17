$(document).ready(function () {
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var display_msg_received = [];

    //receive details from server
    socket.on('display_gui', function (msg) {
        console.log("Display message on gui " + msg);
        display_msg_received.push(msg);
        show_str = "";
        for (var i = 0; i < display_msg_received.length; i++) {
            show_str = show_str + display_msg_received[display_msg_received.length - 1 - i];
        }
        $('#test_details').html(show_str);
    });

    socket.on('user_alerts', function (msg) {
        console.log("Show user alert: " + msg);
        $('#user_alerts').html(msg);
    });

});
