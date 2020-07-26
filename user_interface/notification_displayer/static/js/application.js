document.addEventListener('DOMContentLoaded', () => {
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    //receive details from server
    socket.on('display_gui', function (msg) {
        console.log("Display message on gui " + msg);
        add_details(msg);
    });

    socket.on('user_alerts', function (msg) {
        console.log("Show user alert: " + msg);
        show_alert(msg);
    });
    socket.on('ask_config', function (msg) {
        console.log("Asking for Config: " + msg);
        show_alert(msg);
        document.getElementById('config_button').disabled = false;

    });
    socket.on('ask_dut', function (msg) {
        console.log("Asking for DUT: " + msg);
        document.getElementById('device_button').disabled = false;
        document.getElementById('form-eui').disabled = false;
        document.getElementById('form-devaddr').disabled = false;
        document.getElementById('form-appkey').disabled = false;
    });

    // If hide button is clicked, delete the post.
    document.addEventListener('click', event => {
        const element = event.target;
        if (element.className === 'hide') {
            element.parentElement.style.animationPlayState = 'running';
            element.parentElement.addEventListener('animationend', () =>  {
                element.parentElement.remove();
            });
        } else if (element.id === 'hide_controls') {
            document.getElementById('commands').hidden = true;
            document.getElementById('show_controls').hidden = false;

        } else if (element.id === 'show_controls_button') {
            document.getElementById('commands').hidden = false;
            document.getElementById('show_controls').hidden = true;

        } else if (element.id === 'config_button') {
            const selected = document.querySelectorAll('#test-list option:checked');
            const values = Array.from(selected).map(el => el.value);
            socket.emit('send_config', values);
            console.log("Config: " + values);
            document.getElementById('test-list').disabled = true;
            document.getElementById('config_button').disabled = true;

        } else if (element.id === 'device_button') {
            const deveui = document.getElementById('form-eui').value;
            const devaddr = document.getElementById('form-devaddr').value;
            const appkey = document.getElementById('form-appkey').value;
            const personalizeDUT = new Object();
            personalizeDUT.deveui = deveui;
            personalizeDUT.devaddr = devaddr;
            personalizeDUT.appkey = appkey;

            socket.emit('personalize_dut', JSON.stringify(personalizeDUT));
            console.log("Personalize DUT: " + JSON.stringify(personalizeDUT));

            document.getElementById('device_button').disabled = true;
            document.getElementById('form-eui').disabled = true;
            document.getElementById('form-devaddr').disabled = true;
            document.getElementById('form-appkey').disabled = true;

            document.getElementById('start_button').disabled = false;

        } else if (element.id === 'start_button') {
            socket.emit('start_test', "START");
            console.log("start button pressed");
            document.getElementById('start_button').disabled = true;

        }
    });

});

const temp1 = "<div class=\"post\"> {{{ contents }}} <button class=\"hide\">Hide</button> </div>"
const post_template = Handlebars.compile(temp1);

function show_alert(contents) {

    // Create new post.
    const post = post_template({'contents': contents});

    // Add post to DOM.
    document.querySelector('#user_alerts').innerHTML = post;
}

function add_details(contents) {

    // Create new post.
    const post = post_template({'contents': contents});

    // Add post to DOM.
    let current_content = document.querySelector('#test_details').innerHTML;
    document.querySelector('#test_details').innerHTML = post;
    document.querySelector('#test_details').innerHTML += current_content;
}




