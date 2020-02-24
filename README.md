### 3D Printer web interface 

easyprint는 3d 프린터를 위한 웹 인터페이스로 stl파일의 슬라이싱과 실제 3d 출력을 가능하게 합니다.
그밖에도 모델링 파일의 3d 뷰어와 웹캠을 통한 실시간 출력모습을 확인할 수 있습니다.

Install
```
git glone https://github.com/onepwnman/easyprint.git
cd easyprint
```


서버 환경에 맞게 다음 파일의 변수들을 세팅해야 합니다.

```
scripts/init.sh
export MAIL_SERVER='메일 서버 ex) smtp.googlemail.com'
export MAIL_USERNAME='실제 메일 계정 아이디'
export MAIL_PASSWORD='실제 메일 계정 비밀번호'
export ADMINS='메일을 보낼 관리자 이메일 ex) easyprintserver@gmail.com'
export SECRET_KEY='보안을 위해 세팅할 무작위 문자열'
```

```
src/static/js/custom.js
웹소캣 연결을 위한 서버의 주소
let socket = io.connect('ws://your_server_ip_here:12000');
웹캠 연결을 위한 서버의 주소
let serverAddress = 'http://your_server_ip_here:5001/?action=stream';
```

실행
```
./start onepwnman/easyprint
```

웹브라우저에서 http://easyprint서버의ip:12000로 접속해 확인

