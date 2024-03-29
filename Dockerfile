# Use a specific Ubuntu version
FROM ubuntu:20.04

# Set the working directory in the container
WORKDIR /app

# Install Python, pip, and necessary tools for adding a PPA
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    software-properties-common

# Add the MuseScore PPA and install MuseScore
RUN add-apt-repository ppa:mscore-ubuntu/mscore-stable -y && \
    apt-get update && apt-get install -y musescore

# Copy the current directory contents into the container at /app
COPY . /app

RUN chmod +x pdftomusicpro-1.7.6d.0.run && \
    printf 'Y' | ./pdftomusicpro-1.7.6d.0.run && \
    rm /app/pdftomusicpro-1.7.6d.0.run && \
    cp -a /app/pdftomusicpro-1.7.6d.0/InstallFiles/usr/bin/. /usr/bin/ && \
    cp -a /app/pdftomusicpro-1.7.6d.0/InstallFiles/usr/share/. /usr/share/ && \
    mkdir /usr/share/'PDFtoMusic Pro x64' && \
    cp -a /usr/share/'PDFtoMusic Pro'/. /usr/share/'PDFtoMusic Pro x64'/ && \
    rm -r /app/pdftomusicpro-1.7.6d.0

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World
ENV PORT 5002

# Run app.py when the container launches
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
