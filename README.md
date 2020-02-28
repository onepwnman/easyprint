### 3D Printer web interface 


Easyrpint is a web interface for 3d printer running on the docker container on raspberry pi
which make it possible to slicing stl files and actual 3d printing on a physical machine.
It also support 3d viewer of the 3d model and real time streaming to check out printing progress.
#

### Install

You must install easyprint on the raspberry pi.
```
git glone https://github.com/onepwnman/easyprint.git
cd easyprint
```


You need to set the environment variables in the scripts/init.sh file before running server.

 

**_scripts/init.sh_**
```
export MAIL_SERVER='mail server ex) smtp.googlemail.com'
export MAIL_USERNAME='your mail account id'
export MAIL_PASSWORD='your mail account password'
export ADMINS='administrator email for sending mails ex) easyprintserver@gmail.com'
export SECRET_KEY='any random string value to make server secure'
```

**_src/static/js/custom.js_**
```
let socket = io.connect('ws://your_server_ip_here:12000'); 
let serverAddress = 'http://your_server_ip_here:5001/?action=stream';
```           
 
**_start server_**
```
./start onepwnman/easyprint
```
A docker image will be automatically fetched from **docker hub** to the local server
You can access server from 12000 port on web browser.


You also can check the demo page of  [easyprint](https://easyprint.hopto.org) server in this link . 
(The actual printing part has been replaced with dummy code which only indicating current printing state without actual printing. Please check out the below note.)   

#

### Note

_As i mentioned earlier easyprint server runs on the docker container on the raspberry pi as a single server.
While you're printing if the server receives a lot of requests or if the server is busy, you will not be guaranteed printing quality and sometime printer could be pause for 1 or 2 seconds.
This is the fundamental issue of putting every feature on a single physical machine and in order to fix this issue you need to separate server on different machines._



<br>

Here's a link of this project    
it's korean by the way      
[https://onepwnman.github.io/Easyprint-Project/](https://onepwnman.github.io/Easyprint-Project/)
