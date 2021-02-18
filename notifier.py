import requests
import urllib
import sys
import os.path
import telegram

class Notifier:

    ERROR_API = "Error during API call"
    URL = 'https://api.smsmode.com/http/1.6/'
    PATH_SEND_SMS = "sendSMS.do"

    def send_sms_post(self, access_token, message, destinataires:list,):
        destinataires = ((((str(destinataires)).replace("'", "")).replace("]", "")).replace("[", "")).replace(" ", "")
        final_url = self.URL + self.PATH_SEND_SMS
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        payload = {
            'accessToken': access_token,
            'message': message,
            'numero': destinataires
        }
        r = requests.post(final_url, data=payload, headers=headers)
        if not r:
            return self.ERROR_API
        return r.text

    def sendTelegramMsg(self, token: str, chat_id: str, message: str, sms_destinataires:list):
        destinataires = ((((str(sms_destinataires)).replace("'", "")).replace("]", "")).replace("[", "")).replace(" ", "")
        if sms_destinataires : 
            if len(sms_destinataires) > 1:
                suf_msg = f"\n\t - Message envoyé aux : {destinataires}."
            else:
                suf_msg = f"\n\t - Message envoyé au : {destinataires}."
        else:
            suf_msg = "\n\t - Aucun numéro lié à ce robot, aucun SMS envoyé."

        request = telegram.utils.request.Request(read_timeout=30)
        bot = telegram.Bot(token, request=request)
        message = bot.send_message(chat_id=chat_id, text=message+suf_msg)

    def sendNotifications(self, message: str, clients: list, tokens: dict, sn: str, translate: dict, language: str):
        msg = f"{sn} : " + translate["Messages"][message]["fr"]
        self.sendTelegramMsg(tokens["telegram"],tokens["chat_id"],msg,clients)
        if clients:
            msg = f"{sn} : " + translate["Messages"][message][language]
            self.send_sms_post(tokens["sms"],msg,clients)
