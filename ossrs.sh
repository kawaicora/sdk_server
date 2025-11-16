#docker run --rm -it -p 1935:1935 -p 1985:1985 -p 8080:8080 -p 8000:8000/udp -p 10080:10080/udp ossrs/srs:6
docker run -d --network=host --name ossrs ossrs/srs:6
