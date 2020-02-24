#!/bin/sh

export FLASK_APP=src/main
export FLASK_ENV=development
export PRINT_MODE=demoprint
export MAIL_PORT=25
export MAIL_USE_TLS=1
export MAIL_SERVER=
export MAIL_USERNAME=
export MAIL_PASSWORD=
export ADMINS=
export SECRET_KEY=


# DB sttings
service mysql restart
mysql -u root < "${BASEDIR}"/settings/database.sql
if [ -d ${BASEDIR}/migrations ]; then
    rm -rf ${BASEDIR}/migrations 
fi

# db migrate
flask db init && flask db migrate -m "init database" && flask db upgrade

# nginx settings
cp "${BASEDIR}"/settings/default /etc/nginx/sites-enabled/default
service nginx restart

# redis settings
service redis-server start

# mjpg-streamer settings
MJPGDIR="${BASEDIR}"/util/mjpg-streamer/mjpg-streamer-experimental/
"${MJPGDIR}"/mjpg_streamer -b -i "${MJPGDIR}"/input_uvc.so -o "${MJPGDIR}""/output_http.so -p 5001"

# run server
python3 run.py

