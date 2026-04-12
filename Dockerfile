FROM ubuntu:latest
LABEL authors="tomro"

ENTRYPOINT ["top", "-b"]