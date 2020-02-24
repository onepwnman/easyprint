### 3D Printer web interface 

easyprint는 라즈베리파이 위에서 돌아가는 3d 프린터를 위한 웹 인터페이스로 stl파일의 슬라이싱과 실제 3d 출력을 가능하게 합니다.
그밖에도 모델링 파일의 3d 뷰어와 웹캠을 통한 실시간 출력모습을 확인할 수 있습니다.   

#

### Install

라즈베리파이 위에서 설치하여야 합니다.
```
git glone https://github.com/onepwnman/easyprint.git
cd easyprint
```


서버 환경에 맞게 다음 파일의 변수들을 세팅해야 합니다.

scripts/init.sh
```
export MAIL_SERVER='메일 서버 ex) smtp.googlemail.com'
export MAIL_USERNAME='실제 메일 계정 아이디'
export MAIL_PASSWORD='실제 메일 계정 비밀번호'
export ADMINS='메일을 보낼 관리자 이메일 ex) easyprintserver@gmail.com'
export SECRET_KEY='보안을 위해 세팅할 무작위 문자열'
```

src/static/js/custom.js
```
웹소캣 연결을 위한 서버의 주소
let socket = io.connect('ws://your_server_ip_here:12000');
웹캠 연결을 위한 서버의 주소
let serverAddress = 'http://your_server_ip_here:5001/?action=stream';
```

```
./start onepwnman/easyprint
```

웹브라우저에서 easyprint 서버의 ip 12000번 포트로 접속해 확인
다음의 주소로 이동해 [easyprint](https://easyprint.hopto.org) 서버의 모습을 미리 확인해 보실수 있습니다.
(실제 프린팅하는 출력부분은 출력 상황만 나타내어주는 dummy code로 대체되었습니다.)   

#

### Note

_easyprint 서버는 라즈베리파이 위의 도커 컨테이너상에서 하나의 서버로 돌아갑니다. 따라서 
슬라이싱 요청이 증가하거나 서버가 busy 상태일때 프린팅 중이라면 프린팅 프로세스의 스케쥴링 시간을 보장해주지 못해 프린팅도중 프린터가 중간중간 멈춰 프린팅 퀄리티가 떨어지게 됩니다.
따라서 근본적으로 이를 해결하기 위해서는 서버를 하나 이상의 physical machine으로 분리하여 프린팅 하는 머신과 사용자의 응답을 처리해 주는 머신으로 독립적으로 처리하여야 할 것입니다._
