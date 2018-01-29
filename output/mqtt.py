from output import OutputProcessor
import paho.mqtt.client as paho
import urlparse

class MqttOutput(OutputProcessor):
   name = "mqtt"

   def __init__(self,params):
      OutputProcessor.__init__(self, params)

      self.topic = self.get_param(params,'topic','')
      self.url   = urlparse.urlparse( self.get_param(params,'url','mqtt://localhost:1883' ) )
      self.mqttc = paho.Client()
      if self.url.username!=None:
         self.mqttc.username_pw_set( self.url.username, self.url.password )
      self.mqttc.connect( self.url.hostname, self.url.port if self.url.port!=None else 1883 , 60 )
      self.mqttc.loop_start()

   def output(self, value, parser_name ):
       self.mqttc.publish(self.topic, value )
       pass