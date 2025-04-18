# stream-web-provider

## General 

This is a little useful tool to provide access to the camera of a PC to remote users via a web application.

The tool runs a Flask webserver on the PC.
When a user connects to the web application and requests the camera stream, a connection the connected USB camera is established and the live video is streamed to the browser of the remote user.
As soon as the user stops the stream or the selected/default stream duration is expired, the stream is stopped and the USB camera is released.
After the stream other applications can access the camera.

To run the tool, please install the Python package and run command: ``stream-web-provider``

For information about available configuration arguments please run ``stream-web-provider --help``.

## Firewall Rules

Please be aware that you have to add the port of the web application to the exceptions of your system firewall. 
Otherwise, it's not possible to access the application from other PCs.

Open the firewall port:

``sudo uft allow <port>``

## System Service

For a permanent execution of the application, please install the provided system service (*stream_web_provider.service*).
Please add this file inside the */etc/systemd/system* directory of your system.
Inside this file you have to update the dummy username with your username.

After this steps you have to enable the servie:

``sudo systemctl enable stream_web_provider.service``

Now the service can be started: 

``sudo systemctl restart stream_web_provider.service``

Please check if the service runs properly: 

``sudo systemctl status stream_web_provider.service``
