"""
Appliction configuration settings
"""
import os

from tornado.options import define
import motor.motor_tornado
# define("debug", default=True, help="Debug settings")
# define("port", help="Port to run the server on")
#
APP_DIR = os.path.dirname(os.path.realpath(__file__))

#change the following password or cluster URI before running
client = motor.motor_tornado.MotorClient('mongodb://animeshjn:jain@cluster0-shard-00-00-1wwjj.mongodb.net:27017,cluster0-shard-00-01-1wwjj.mongodb.net:27017,cluster0-shard-00-02-1wwjj.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin')
#client = motor.motor_tornado.MotorClient()

settings = {
    "template_path": os.path.join(APP_DIR, "templates"),
    "static_path": os.path.join(APP_DIR, "static")
}
