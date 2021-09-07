FROM continuumio/anaconda3
RUN apt-get update && apt-get upgrade -y
WORKDIR /
COPY . /
RUN conda env update --file docker-env/environment.yml