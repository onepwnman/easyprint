FROM       raspbian/stretch
MAINTAINER onepwnman@gmail.com

RUN apt-get -y -qq update && \
    wget https://bootstrap.pypa.io/get-pip.py && \  
    apt-get -y -qq install \
        python3 \
        nginx \
        mysql-server=5.5.9999+default \
        redis-server \
        libv4l-dev && \
    python3 get-pip.py

ENV BASEDIR=/usr/src/app/ 

# Copying source code
COPY    . ${BASEDIR} 
WORKDIR ${BASEDIR}
COPY    ./scripts/.bashrc /.bashrc

RUN pip3 install -r requirements.txt

EXPOSE  80 \
        12000 \
        5001 \
        6379 \
        443 \
        25 \
        4000 

# Clean Up routine 
# RUN rm -rf /va/lib/apt/list/*

CMD ["/bin/bash"]
