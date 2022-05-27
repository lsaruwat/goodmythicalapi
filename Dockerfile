FROM ubuntu:22.04

RUN apt -y update && apt -y upgrade
RUN apt update && apt -y install python3 python3-dev python3-pip gunicorn nano git

# Install any needed packages specified in requirements.txt
RUN pip3 install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Run api through gunicorn when the container launches
CMD ["gunicorn", "-b", ":80", "--workers=2", "--reload", "--timeout=300", "main"]
