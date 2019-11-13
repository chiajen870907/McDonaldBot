from linebot.exceptions import (InvalidSignatureError)
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import *

from flask import Flask, request, abort
from datetime import datetime

from firebase_admin import credentials
from firebase_admin import firestore

import firebase_admin
import requests
import hashlib
import random
import time
import os

from McDonald import McDonald

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('Channel Access Token')

# Channel Secret
handler = WebhookHandler('Channel Secret')

# private_key
private_key = credentials.Certificate('/app/service-account.json')

# 初始化firebase
firebase_admin.initialize_app(private_key)
db = firestore.client()

# Global
LINE_USER_ID = None
account = None


# McDonald------------------


class Mask(object):
    """docstring for Mask."""

    def __init__(self, account, password):
        super(Mask, self).__init__()
        self.paramString = account + password  # Just Username + Password
        self.account = account  # Username
        self.password = password  # Password
        self.access_token = ""  # Token
        self.str1 = datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')  # Device Time
        self.str2 = '2.2.0'  # App Version
        self.str3 = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')  # Call time
        self.ModelId = 'MIX 3'  # Model ID
        self.OsVersion = '9'  # Android OS Version
        self.Platform = 'Android'  # Platform
        self.DeviceUuid = 'device_uuid'  # Device Uuid
        self.OrderNo = self.DeviceUuid + self.str3  # Order No
        self.cardNo = 'cardNo'  # Card NO

    def Login(self):
        # Mask = MD5('Mc' + OrderNo + Platform + OsVersion + ModelId + DeviceUuid + str1 + str2 + paramString + 'Donalds')
        data = 'Mc%s%s%s%s%s%s%s%sDonalds' % (
            self.OrderNo,
            self.Platform,
            self.OsVersion,
            self.ModelId,
            self.DeviceUuid,
            self.str1,
            self.str2,
            self.paramString
        )
        mask = hashlib.md5()
        mask.update(data.encode('utf-8'))

        # Form data
        json = {
            "account": self.account,
            "password": self.password,
            "OrderNo": self.OrderNo,
            "mask": mask.hexdigest(),
            "source_info": {
                "app_version": self.str2,
                "device_time": self.str1,
                "device_uuid": self.DeviceUuid,
                "model_id": self.ModelId,
                "os_version": self.OsVersion,
                "platform": self.Platform,
            }
        }
        headers = {
            'Connection': 'close'
        }
        # Get the response
        response = requests.post('https://api.mcddaily.com.tw/login_by_mobile', json=json, headers=headers).text

        # Clean the garbage date
        response = response.replace('null', '""')
        response = response.replace('true', '"true"')
        response = response.replace('false', '"false"')

        # Convert the string to dictionary type
        response = eval(response)

        # Get the token
        self.access_token = response['results']['member_info']['access_token']

        # Return the dictionary type of response
        return response

    def CardIM(self):
        # Mask = MD5('Mc' + OrderNo + access_token + cardNo + callTime + 'Donalds')
        data = 'Mc%s%s%s%sDonalds' % (
            self.OrderNo,
            self.access_token,
            self.cardNo,
            self.str3,
        )
        mask = hashlib.md5()
        mask.update(data.encode('utf-8'))

        # From data
        json = {
            "OrderNo": self.OrderNo,
            "access_token": self.access_token,
            "callTime": self.str3,
            "cardNo": self.cardNo,
            "mask": mask.hexdigest(),
        }

        # Get the response
        response = requests.post('https://api.mcddaily.com.tw/queryBonus', json=json).text

        # Convert the string to dictionary type
        response = eval(response)

        # Return the dictionary type of response
        return response

class Line:
    def __init__(self):
        print('OK')
        self.message = []

    def ImageCarouselColumn(self, n, list):
        text = []
        for i in range(0, int(n)):
            message2 = "ImageCarouselColumn(image_url=" + "'" + list[i] + "'" + ",action=PostbackTemplateAction(label='查看我的歡樂貼',text='我的歡樂貼',data='action=buy&itemid=1')),"
            text.append(message2)
        text[n-1] = text[n-1].strip(',')
        text = "".join(text)
        self.message = eval("TemplateSendMessage(alt_text='圖片訊息',template=ImageCarouselTemplate(columns=[" + text + "]))")

        return self.message


def login_MC():
    # Login and get the information
    info = (Mask(account[0], account[1])).Login()
    MC_Status = (info['rm'])
    MC_Token = (info['results']['member_info']['access_token'])
    return MC_Status, MC_Token


# --------------------------

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 等待伺服器回傳資料
@handler.add(PostbackEvent)
def handle_postback(event):
    temp = event.postback.data
    if temp == 'Login':
        MC_Status, MC_Token = login_MC()
        if MC_Status == '登入成功' and MC_Token != '':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MC_Status + '\n每天準時晚上12點幫你抽\nヽ(‘ ∇‘ )ノ'))
            Database_Increase_Counter()
            Count = Database_Get_Counter()
            doc_text = {
                'Token' + str(Count): MC_Token
            }
            doc2_text = {
                MC_Token: LINE_USER_ID
            }

            doc_ref = db.collection("Line_User").document('Info')
            doc2_ref = db.collection("Check").document('Token')
            doc_ref.update(doc_text)
            doc2_ref.update(doc2_text)

        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MC_Status + '\n 〒.〒 '))


def Database_Read_Data(path):
    doc_ref = db.document(path)
    result = doc_ref.get().to_dict()
    return result


def Database_Get_Counter():
    Path = 'Line_User/Counter'
    result = Database_Read_Data(Path)
    return int(result['Count'])


def Database_Increase_Counter():
    Count = Database_Get_Counter()
    Count = Count + 1
    doc_text = {
        'Count': Count
    }
    doc_ref = db.collection("Line_User").document('Counter')
    doc_ref.set(doc_text)


def Database_Get_TokenList():
    Path = 'Line_User/Info'
    Count = Database_Get_Counter()
    result = Database_Read_Data(Path)
    Token = []
    for i in range(Count + 1):
        Token.append(result['Token' + str(i)])
    return Token


def Database_Check_UserState(userid):
    result = Database_Read_Data('Check/Token')
    try:
        token = list(result.keys())[list(result.values()).index(userid)]
        user_exist = True
    except ValueError:
        user_exist = False
        token = ''
    return user_exist, token


def Database_Get_UserToken(User_ID):
    result = Database_Read_Data('Check/Token')
    try:
        token = list(result.keys())[list(result.values()).index(User_ID)]
    except ValueError:
        token = ''
    return token


def McDonald_Get_CouponList():
    Account = McDonald(Database_Check_UserState(LINE_USER_ID)[1])
    URLS_List = Account.Coupon_List()
    return URLS_List


def McDonald_Get_StickerList():
    Account = McDonald(Database_Check_UserState(LINE_USER_ID)[1])
    Sticker_List = Account.Sticker_List()
    return Sticker_List


def McDonald_ManualLottery_Coupon():
    Account = McDonald(Database_Check_UserState(LINE_USER_ID)[1])
    title, url = Account.Lottery()
    temp = url.split('/')[3]
    Filename = temp.split('.')[0]
    if not db.collection('Coupons').document(title).get().exists:
        doc_text = {'ID': Filename}
        doc_ref = db.collection("Coupons").document(title)
        doc_ref.set(doc_text)
    return title, url


def McDonald_AutoLottery_Coupon():
    Count = Database_Get_Counter()
    Token_List = Database_Get_TokenList()
    ref = db.document('Check/Token')
    doc_token = ref.get().to_dict()

    for i in range(Count + 1):
        time.sleep(1)
        userid = doc_token[Token_List[i]]
        token = Database_Check_UserState(userid)[1]
        Account = McDonald(token)
        print(userid,token)
        title, url = Account.Lottery()
        temp = url.split('/')[3]
        Filename = temp.split('.')[0]
        if not Filename == 'ccrotbJmNrxfvvc7iYXZ':
            if not db.collection('Coupons').document(title).get().exists:
                doc_text = {'ID': Filename}
                doc_ref = db.collection("Coupons").document(title)
                doc_ref.set(doc_text)

            message = TemplateSendMessage(alt_text='圖片訊息', template=ImageCarouselTemplate(columns=[ImageCarouselColumn(image_url=url, action=PostbackTemplateAction(label='查看我的優惠卷', text='我的優惠卷',data='action=buy&itemid=1')), ]))
            Message2 = TextSendMessage(text='每日抽獎~恭喜你獲得~')

            line_bot_api.push_message(userid, Message2)
            line_bot_api.push_message(userid, message)
    print('McDonald_AutoLottery_Coupon OK')


def McDonald_AutoLottery_Sticker():
    Count = Database_Get_Counter()
    Token_List = Database_Get_TokenList()
    ref = db.document('Check/Token')
    doc_token = ref.get().to_dict()

    for i in range(Count + 1):
        time.sleep(1)
        userid = doc_token[Token_List[i]]
        token = Database_Check_UserState(userid)[1]
        Account = McDonald(token)
        Sticker_List = Account.Sticker_List()

        if int(Sticker_List[0]) >= 6:
            title, url = Account.Sticker_lottery()
            temp = url.split('/')[3]
            Filename = temp.split('.')[0]

            if not db.collection('Coupons').document(title).get().exists:
                doc_text = {'ID': Filename}
                doc_ref = db.collection("Coupons").document(title)
                doc_ref.set(doc_text)

            message = TemplateSendMessage(alt_text='圖片訊息', template=ImageCarouselTemplate(columns=[ImageCarouselColumn(image_url=url, action=PostbackTemplateAction(label='查看我的優惠卷', text='我的優惠卷',data='action=buy&itemid=1')), ]))
            Message2 = TextSendMessage(text='歡樂貼自動抽獎~~恭喜你獲得~')

            line_bot_api.push_message(userid, Message2)
            line_bot_api.push_message(userid, message)
    print('McDonald_AutoLottery_Sticker OK')


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global LINE_USER_ID
    global account
    LINE_USER_ID = event.source.user_id
    # ----------------Login-----------------------
    if Database_Check_UserState(LINE_USER_ID)[0]:
        if event.message.text == '我的歡樂貼':
            StickerList = McDonald_Get_StickerList()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='目前擁有歡樂貼:{}\n月底即將到期歡樂貼:{}'.format(StickerList[0], StickerList[1])))

        elif event.message.text == '抽獎':
            url = McDonald_ManualLottery_Coupon()[1]
            message = TemplateSendMessage(alt_text='圖片訊息', template=ImageCarouselTemplate(columns=[ImageCarouselColumn(image_url=url, action=PostbackTemplateAction(label='查看我的優惠卷', text='我的優惠卷', data='action=buy&itemid=1')), ]))
            line_bot_api.reply_message(event.reply_token, message)

        elif event.message.text == '我的優惠卷':
            URLS_List = McDonald_Get_CouponList()
            if not URLS_List:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='o_O ||\n你沒有任何優惠卷ㅇㅁㅇ'))
            else:
                URLS_Items = len(URLS_List)
                res = Line()
                message = res.ImageCarouselColumn(URLS_Items, URLS_List)
                line_bot_api.reply_message(event.reply_token, message)

        elif event.message.text == '手動測試-1':
            McDonald_AutoLottery_Coupon()
        elif event.message.text == '手動測試-2':
            McDonald_AutoLottery_Sticker()

        else:
            Random_type = random.randint(1, 5)
            if Random_type == 1:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='你可以試試輸入【我的優惠卷】 \n(・∀・)'))
            elif Random_type == 2:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='說不定輸入【我的歡樂貼】會有事情發生呢 \n(ノ^o^)ノ'))
            elif Random_type == 3:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='輸入神秘指令【抽獎】會有怪事發生呢\nლ(｀∀´ლ) '))
            elif Random_type == 4:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='我好累，不想工作。\n罷工拉 \n(-。-;'))
            elif Random_type == 5:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='看我施展魔法 \n(∩｀-´)⊃━炎炎炎炎炎'))

    else:
        temp = event.message.text
        if temp != '登入':
            if '/' not in temp:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='注意!!少了斜線(/)  Σ( ° △ °|||)'))
            else:
                account = temp.split('/')
                if len(account) > 2:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='多打了斜線哦  Σ( ° △ °|||)'))
                else:
                    Login_message = TemplateSendMessage(alt_text='Template', template=ButtonsTemplate(title='登入確認', text='帳號:{}\n密碼:{}'.format(account[0], account[1]), actions=[PostbackTemplateAction(label='按此登入', text='登入', data='Login')]))
                    line_bot_api.reply_message(event.reply_token, Login_message)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
