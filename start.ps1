docker build --tag 'ipotechka' .;
docker run -p 5001:80 -d --name 'Ipotechka' ipotechka;