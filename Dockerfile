FROM continuumio/miniconda3
RUN apt-get --allow-releaseinfo-change update && apt-get upgrade -y
WORKDIR /
COPY . /
#RUN conda env update --file docker-env/environment.yml
RUN pip install -U -r docs/requirements.txt