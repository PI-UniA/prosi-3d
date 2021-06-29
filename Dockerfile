FROM continuumio/anaconda3
RUN apt-get update && apt-get upgrade -y
WORKDIR /
COPY ./docker-env/environment.yml ./
RUN conda env update --file environment.yml
COPY ./prosi3d ./prosi3d