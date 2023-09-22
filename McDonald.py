import re
import requests
from datetime import datetime, timedelta



class McDonald(object):
    """docstring for McDonald."""

    def __init__(self, token):
        super(McDonald, self).__init__()
        self.json = {
          "access_token": token,
          "source_info": {
            "app_version": "2.2.0",
            "device_time": "2019/01/24 00:00:00",
            "device_uuid": "device_uuid",
            "model_id": "Pixel XL",
            "os_version": "7.1.1",
            "platform": "Android"
          }
        }

        self.headers = {
            'Connection': 'close'
        }

        self.respones = ""
        self.coupons = []
        self.urls = []
        self.stickers = 0
        self.expire_stickers = 0

    # Basic lottery function
    def Lottery(self):
        # Request to get a lottery
        self.respones = requests.post('https://api1.mcddailyapp.com/lottery/get_item', json=self.json).text

        # If you don't like to have the return value which lottery event , you can delete all the code below

        # Convert string to dictionary
        self.respones = eval(self.respones)

        # Check the return value of lottery
        if 'coupon' in self.respones['results']:
            Lottery_result = self.respones['results']['coupon']['object_info']['title']
            url = self.respones['results']['coupon']['object_info']['image']['url']
        else:
            Lottery_result = self.respones['results']['sticker']['object_info']['title']
            url = self.respones['results']['sticker']['object_info']['image']['url']

        # Return the result of lottery
        return self.Re(Lottery_result), url

    # Get the coupon list
    def Coupon_List(self):
        # Request to get the coupon list
        self.respones = requests.post('https://api1.mcddailyapp.com/coupon/get_list', json=self.json).text
        count = self.respones.count('coupon_id')  # Count the number of coupons
        self.respones = eval(self.respones)  # Convert string to dictionary

        # Check the status of the coupons to make sure that they are not used or expired
        for value in range(count):
            status = self.respones['results']['coupons'][value]['status']
            redeem_end_datetime = self.respones['results']['coupons'][value]['object_info']['redeem_end_datetime']
            redeem_end_datetime = datetime.strptime(redeem_end_datetime, '%Y/%m/%d %H:%M:%S')

            # Status code is 1 also redeem_end_datetime is not yet
            if status == 1 and redeem_end_datetime - datetime.now() > timedelta():
                url = self.respones['results']['coupons'][value]['object_info']['image']['url']
                self.urls.append(url)

        return self.urls

        # Return coupon list
        return self.coupons

    # Get the sticker list
    def Sticker_List(self):
        # Initializing the expired stickers again is a safe way to avoid the repeat addition
        self.expire_stickers = 0

        # Request to get the sticker list
        self.respones = requests.post('https://api1.mcddailyapp.com/sticker/get_list', json=self.json).text
        self.stickers = self.respones.count('歡樂貼') # Count the number of stickers
        self.respones = eval(self.respones)          # Convert string to dictionary

        # Every stickers are going to be checked is expired
        for value in range(self.stickers):
            expire_datetime = self.respones['results']['stickers'][value]['object_info']['expire_datetime']
            expire_datetime = datetime.strptime(expire_datetime, '%Y/%m/%d %H:%M:%S')

            if expire_datetime.month == datetime.now().month:
                self.expire_stickers += 1

        # Return stickers and expire_stickers
        return self.stickers, self.expire_stickers

    # Request to get a sticker lottery
    def Sticker_lottery(self):
        self.Sticker_List() # Get the stickers information
        sticker_ids = []    # Sticker ids list

        # If sticker number less than 6 , exit
        if self.stickers < 6:
            print('The stickers are not enough , just only %d !\n' % (self.stickers))

        # Make sure the user want to get a lottery
        else:
            # Get the 6 sticker ids
            for value in range(6):
                sticker_ids.append(self.respones['results']['stickers'][value]['sticker_id'])

            # Update the json dictionary
            self.json['sticker_ids'] = sticker_ids

            # Get a sticker lottery
            self.respones = requests.post('https://api1.mcddailyapp.com/sticker/redeem', json=self.json).text
            self.respones = eval(self.respones)  # Convert string to dictionary

            # Return the results of coupon information
            result = self.respones['results']['coupon']['object_info']['title']
            url = self.respones['results']['coupon']['object_info']['image']['url']
            return self.Re(result), url

    # Clear some characters are matched by Regular Expression
    def Re(self, coupon):
        coupon = re.sub(r'鷄', '雞', coupon)
        coupon = re.sub(r'\(G.*\)|_.*|\(新.*', '', coupon)
        return coupon

