#!/bin/bash


# 12000 easyprint local server
# 6379 redis-server
# 5001 webcam server
# 80 nginx 
# 443 nginx ssl 
# 25 mail server
# 4000 easyprint production server

docker run -p 12000:12000 -p 6379:6379 -p 5001:5001 -p 80:80 -p 443:443 -p 25:25 -p 4000:4000 --privileged=true -it -v /home/pi/project/easyprint:/usr/src/app -v /dev:/dev $1 /bin/bash

