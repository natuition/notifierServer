import requests
import urllib
import sys
import os.path
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext
import time

from telegram.files.document import Document
from generate import generatePdf

class Notifier:

    ERROR_API = "Error during API call"
    URL = 'https://api.smsmode.com/http/1.6/'
    PATH_SEND_SMS = "sendSMS.do"

    def __init__(self, token: str):
        self.updater = Updater(token)
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.button))
        self.updater.start_polling()

    def button(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        if "pdf" in query.data:
            url = str(query.data).replace("pdf_","")
            session_hours = url.rsplit("/",1)[1].split("%20")[1]
            session_date = url.rsplit("/",1)[1].split("%20")[0]
            session_hours_str = session_hours.replace("-",":")
            session_date_str = session_date.replace("-","/")
            
            msg = self.updater.bot.send_message(chat_id=query.from_user.id, text=f"Génération du pdf de la session du {session_date_str} à {session_hours_str}, veuillez patienter...")
            
            dirctory_log = url.rsplit("/",2)[1] + "/" + session_date + " " + session_hours + " " + url.rsplit("/",1)[1].split("%20")[2]
            pdf_name = "resume"

            if not os.path.exists(f"{dirctory_log}/{pdf_name}.pdf"):
                generatePdf("utils_generate/template", f"{dirctory_log}/{pdf_name}", url)

            self.updater.bot.send_document( chat_id=query.from_user.id, 
                                            document=open(f"{dirctory_log}/{pdf_name}.pdf", 'rb'),
                                            filename=f"resume_{session_date}_{session_hours}.pdf", 
                                            caption=f"Résumé de la session du {session_date_str} à {session_hours_str}.")

            msg.delete()

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

    def sendTelegramMsg(self, chat_id: str, message: str, sms_destinataires:list, sendingSms=True, buttons : dict=None):
        destinataires = ((((str(sms_destinataires)).replace("'", "")).replace("]", "")).replace("[", "")).replace(" ", "")
        suf_msg=""
        if sendingSms:
            if sms_destinataires : 
                if len(sms_destinataires) > 1:
                    suf_msg = f"\n\t - Message envoyé aux : {destinataires}."
                else:
                    suf_msg = f"\n\t - Message envoyé au : {destinataires}."
            else:
                suf_msg = "\n\t - Aucun numéro lié à ce robot, aucun SMS envoyé."

        if buttons is not None:
            keyboard = list()
            for name, data in buttons.items():
                keyboard.append([InlineKeyboardButton(name, callback_data=data)])
            reply_markup=InlineKeyboardMarkup(keyboard)
            message = self.updater.bot.send_message(chat_id=chat_id, text=message+suf_msg, reply_markup=reply_markup)
        else:
            message = self.updater.bot.send_message(chat_id=chat_id, text=message+suf_msg)

    def sendNotifications(self, message: str, clients: list, tokens: dict, sn: str, translate: dict, language: str):
        # msg = f"{sn} : " + translate["Messages"][message]["fr"]
        # self.sendTelegramMsg(tokens["telegram"],tokens["chat_id"],msg,clients)
        if clients:
            msg = f"{sn} : " + translate["Messages"][message][language]
            self.send_sms_post(tokens["sms"],msg,clients)
