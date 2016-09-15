sudo echo "starting rabbitmq server"
sudo rabbitmq-server &
python initialization.py &
python classify.py
