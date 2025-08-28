1. Command to build rabbitMQ docker image: 
docker build -t my-rabbitmq .

2. Command to create RabbitMQ container : 
docker run -d --name rabbitmq-test -p 5672:5672 -p 15672:15672 my-rabbitmq
