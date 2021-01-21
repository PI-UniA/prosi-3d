FROM continuumio/anaconda3
RUN apt-get update && apt-get upgrade -y
WORKDIR /
COPY ./env/environment.yml ./
RUN conda env update --file environment.yml
COPY ./python ./python