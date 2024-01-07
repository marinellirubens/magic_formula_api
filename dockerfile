FROM python:3.10-slim-buster
USER root

WORKDIR /opt/magic_formula
#RUN apt update && apt install -y curl vim procps && apt clean

ADD ./requirements.txt /opt/magic_formula/requirements.txt
RUN pip install -r requirements.txt

ADD ./src /opt/magic_formula
ADD ./src/entrypoint_service.sh /usr/bin/entrypoint_service.sh
ADD ./src/entrypoint_api.sh /usr/bin/entrypoint_api.sh
RUN chmod +x /usr/bin/entrypoint_service.sh
RUN chmod +x /usr/bin/entrypoint_api.sh
ENTRYPOINT /usr/bin/entrypoint_service.sh
