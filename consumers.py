# chat/consumers.py
# python file that handles the consumer side of the websockets
# relays updated game data to client

from cgitb import text
import json
from tokenize import Name
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from myapp import models
from chat import views
from channels.db import database_sync_to_async
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if 'chatMessage' in text_data_json:
            message = text_data_json['chatMessage']
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': self.scope['user'].username,
                    'message': message
                }
            )
        elif 'systemMessage' in text_data_json:
            message = text_data_json['systemMessage']

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'system_message',
                    'username': self.scope['user'].username,
                    'message': message
                }
            )
        elif 'shipArray' in text_data_json:
            shiparray = text_data_json['shipArray']
            readycount = text_data_json['readyCount']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ship_array',
                    'array': shiparray,
                    'readyCount': readycount,
                    'user': self.scope['user'].username
                }
            )
        elif 'shotX' in text_data_json:
            shotX = text_data_json['shotX']
            shotY = text_data_json['shotY']
            readycount = text_data_json['readyCount']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'shot_coord',
                    'shotX': shotX,
                    'shotY': shotY,
                    'readyCount': readycount,
                    'user': self.scope['user'].username
                }
            )
        elif 'winMessage' in text_data_json:
            message = text_data_json['winMessage']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'win_message',
                    'username': self.scope['user'].username,
                    'message': message
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['username'] + ": " + event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def system_message(self, event):
        message = event['username'] + event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def win_message(self, event):
        message = event['username'] + event['message']
        targetPlayer = User.objects.get(username=self.scope['user'].username)
        targetWinner = User.objects.get(username=event['username'])
        player = models.ProfileModel.objects.get(Name=targetPlayer)
        winner = models.ProfileModel.objects.get(Name=targetWinner)
        #if targetWinner == targetPlayer:
        winner.Wins += 1
        winner.save()
        player.GamesPlayed += 1
        player.save()
        #Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
        }))

    async def ship_array(self, event):
        array = event['array']
        readyCount = event['readyCount']
        user = event['user']
        await self.send(text_data=json.dumps({
            'array': array,
            'readyCount': readyCount,
            'user': user
        }))
        
    async def shot_coord(self, event):
        shotX = event['shotX']
        shotY = event['shotY']
        readyCount = event['readyCount']
        attacker = event['user']
        shootingSelf = False
        if attacker == self.scope['user'].username:
            shootingSelf = True

        await self.send(text_data=json.dumps({
            'shotX': shotX,
            'shotY': shotY,
            'readyCount': readyCount,
            'user': attacker,
            'shootingSelf': shootingSelf
        }))
