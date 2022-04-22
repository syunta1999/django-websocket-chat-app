import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat_Message
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Q
# from asgiref.sync import async_to_sync   # async_to_sync() : 非同期関数を同期的に実行する際に使用する。

USERNAME_SYSTEM = '*system*'
# ChatConsumerクラス: WebSocketからの受け取ったものを処理するクラス
class ChatConsumer(AsyncWebsocketConsumer):

    # ルーム管理(インスタンス変数ではなく、インスタンス間で使用可能なクラス変数)
    rooms = None

    # コンストラクタ グループ名メンバー変数の初期化とユーザー名メンバー変数とルーム名メンバー変数の初期化
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # クラス変数の初期か(最初のインスタンスが生成されたときのみ実施する)
        if ChatConsumer.rooms is None:
            ChatConsumer.rooms = {} # 空の連想配列
        self.strGroupName = ''
        self.strUserName = ''

    # WebSocket接続時の処理
    async def connect(self):
        # WebSocket接続を受け入れる。
        #  connect()でaccept()を呼び出さないと、接続は拒否されて閉じられる
        #  例えば、要求しているユーザーが要求されたアクションを実行する権限を持っていないために、接続を拒否したい場合がある
        #  接続を受け入れる場合は、connect()の最後のアクションとしてaccept()を呼び出す。
        await self.accept() # 最後に呼び出す
    
    # WebSocket切断時の処理
    async def disconnect(self, close_code):
        # チャットグループから離脱する処理
        await self.leave_chat()
    
    # WebSocketからデータを受信したときの処理   text_typeにjsonが入っていた場合に受信したときとなる
    # ブラウザ側のJavaScript関数のsocketChat.send()の結果、WebSocketを介してデータがChatConsumerに送信され、この関数で受信処理する。
    
    async def receive(self, text_data):
        # 受信データをjsonデータに復元
        text_data_json = json.loads(text_data)

        # チャットへの参加時の処理
        # 送られてきたデータのタイプがJOINだった場合に参加時の処理を実行する。
        if('join' == text_data_json.get('data_type')):
            # ユーザー名をクラスメンバー変数に設定
            self.strUserName = text_data_json['username']
            # ルーム名をクラスメンバー変数に設定
            strRoomName = text_data_json['roomname']
            # チャットへ参加する関数を呼び出し
            await self.join_chat(strRoomName)

        # チャットから離脱するときの処理
        elif('leave' == text_data_json.get('data_type')):
            # チャットから離脱する
            await self.leave_chat()
        
        # フロントから送られてきた自分のメッセージ受信時の処理
        else:
            # メッセージの取り出し
            strMessage = text_data_json['message']
            # ルーム名の取り出し
            strRoomName = text_data_json['roomname']
            # Dbにroomnameとmessageの保存をする関数を呼び出す  formを使わずにDBにデータを保存している。
            await self._save_message(strMessage, strRoomName)
            
            # グループ内の全コンシューマーに　メッセージ拡散送信(受信関数を('type')で指定)　 フロントから取得してからフロントに拡散
            data = {
                'type': 'chat_message', # 受信処理関数名
                'message': strMessage, # メッセージ
                'username': self.strUserName, # ユーザー名
                'datetime': datetime.datetime.now().strftime( '%Y/%m/%d %H:%M:%S' ), # 現在時刻
            }
            await self.channel_layer.group_send(self.strGroupName, data)


    # 拡散メッセージ受信時の処理
    # self.channel_layer.group_send()の結果、グループ内の全コンシューマーにメッセージ拡散され、各コンシューマーはこの関数で受信処理する。
    async def chat_message(self, data):
        data_json = {
            'message': data['message'], # メッセージ
            'username': data['username'], # ユーザー名
            'datetime': data['datetime'], # 現在時刻
        }

        # WebSocketにメッセージを送信
        # 送信されたメッセージは、ブラウザ側のJavaScript関数のsocketChat.onmessage()で受信処理
        # JSONデータをテキストデータにエンコードして送ります
        await self.send(text_data=json.dumps(data_json))

    # チャットへ参加する関数
    async def join_chat(self, strRoomName):
        # グループに参加する
        self.strGroupName = 'chat_%s' % strRoomName
        await self.channel_layer.group_add(self.strGroupName, self.channel_name)

        # 参加者数の更新 コンストラクタで作成したからの連想配列にグループ名を入れる　そしてroom変数に代入 Noneとグループ名は別々の値である。共存している
        room = ChatConsumer.rooms.get(self.strGroupName)
        # 連想配列の数字の枠がNoneの場合はNoneに {'participants_count': 1}　というキーバリュー型の値を代入する。
        if(None == room):
            # ルーム管理にルーム追加
            ChatConsumer.rooms[self.strGroupName] = {'participants_count': 1}
        else:
            # roomに既に値が入っていた場合は += 1 する。
            room['participants_count'] += 1
        # システムメッセージの作成  参加した人の名前と現在の参加者数を表示する。
        strMessage = '"' + self.strUserName + '" が参加しました。' + str(ChatConsumer.rooms[self.strGroupName]['participants_count']) + ' 入室者'

        # ルームネームに該当する同じメッセージをDBから取得
        # await self._get_all_message_filter_by_room(strRoomName)
        # db_message = self._get_all_message_filter_by_room
        # db_message = {
        #     'db_message': db_message,
        # }
        # print(db_message)
        # await self.channel_layer.group_send(self.strGroupName, db_message)

        # グループ内の全コンシューマーにシステムメッセージ拡散送信（受信関数を'type'で指定)
        data = {
            'type': 'chat_message',  # 受信処理関数名
            'message': strMessage, # システムメッセージ
            'username': USERNAME_SYSTEM, # ユーザー名
            'datetime': datetime.datetime.now().strftime( '%Y/%m/%d %H:%M:%S' ), # 現在時刻
        }
        # システムメッセージを参加したグループに対して送信する
        await self.channel_layer.group_send(self.strGroupName, data)

    # チャットから離脱する関数
    async def leave_chat(self):
        # 既に離脱状態なら処理を終了
        if('' == self.strGroupName):
            return 
        # グループから離脱するメソッド
        await self.channel_layer.group_discard(self.strGroupName, self.channel_name)

        # 参加者数の更新
        ChatConsumer.rooms[self.strGroupName]['participants_count'] -= 1
        # システムメッセージの作成
        strMessage = '"' + self.strUserName + '" 退出しました。' + str(ChatConsumer.rooms[self.strGroupName]['participants_count']) + ' 入室者'
        # グループ内の全コンシューマーにシステムメッセージ拡散送信（受信関数を'type'で指定)
        data = {
            'type': 'chat_message',  # 受信処理関数名
            'message': strMessage, # システムメッセージ
            'username': USERNAME_SYSTEM, # ユーザー名
            'datetime': datetime.datetime.now().strftime( '%Y/%m/%d %H:%M:%S' ), # 現在時刻
        }
        # システムメッセージを参加したグループに対して送信する
        await self.channel_layer.group_send(self.strGroupName, data)

        # 参加者がゼロの時は、ルーム管理からルームの削除
        if( 0 == ChatConsumer.rooms[self.strGroupName]['participants_count']):
            del ChatConsumer.rooms[self.strGroupName]

        # ルーム名を空にする
        self.strGroupName = ''

    # データベースにデータを保存する関数　
    @database_sync_to_async
    def _save_message(self, strMessage, strRoomName):
        # print(strMessage, strRoomName)
        Chat_Message.objects.create(
            message=strMessage,
            room=strRoomName,
        )
    # データーベースから値を取得は出来たけどHTMLに表示することはできなかった。
    @database_sync_to_async
    def _get_all_message_filter_by_room(self, strRoomName):
        chat_message = Chat_Message.objects.filter(room=strRoomName).all()
        message = [data.message for data in chat_message]
        room = [data.room for data in chat_message]
        print(message)
        return message
