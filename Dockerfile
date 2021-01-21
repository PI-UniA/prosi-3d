FROM continuumio/anaconda3
RUN apt-get update && apt-get upgrade -y
WORKDIR /
COPY ./env/environment.yml ./
COPY ./WIP ./WIP
RUN conda env update --file environment.yml