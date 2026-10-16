"""Real RabbitMQ streaming entry point. See platform_lab.streaming."""
from platform_lab.streaming import publish, consume_forever, demo

if __name__ == '__main__':
    consume_forever()
