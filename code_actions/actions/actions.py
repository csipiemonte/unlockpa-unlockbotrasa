# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import requests
# local imports
from db.dbwrapper import Dbwrapper

import os
import logging
import random
import time
from datetime import datetime
import aiohttp


CONFIDENCE_TRESHOLD = float(os.environ.get('CONFIDENCE_TRESHOLD', 0.8))
CSI_BOT_URL = os.environ.get('CSI_BOT_URL')
DB_WRAPPER = Dbwrapper(
    schema=os.environ['PSQL_SCHEMA'],
    database=os.environ['PSQL_DATABASE'],
    user=os.environ['PSQL_USER'],
    password=os.environ['PSQL_PASSWORD'],
    dbhost=os.environ['PSQL_HOST'],
    dbport=os.environ['PSQL_PORT'],
)
FEEDBACK_YES_NO = bool(os.environ['FEEDBACK_YES_NO'])

CATEGORY_BUTTONS = {102: {'title': "🏀 Sport", 'payload': '/categoria{"category":102}'},
                    98: {'title': "🌲 Ambiente", 'payload': '/categoria{"category":98}'},
                    103: {'title': "🎻 Cultura e servizi", 'payload': '/categoria{"category":103}'},
                    100: {'title': "👩‍⚕️ Salute", 'payload': '/categoria{"category":100}'},
                    94: {'title': "🚌 Mobilità", 'payload': '/categoria{"category":94}'},
                    97: {'title': "✏️ Scuola", 'payload': '/categoria{"category":97}'},
                    99: {'title': "🏢 Uffici comunali", 'payload': '/categoria{"category":99}'},
                    104: {'title': "📋 Tributi", 'payload': '/categoria{"category":104}'},
                    1: {'title': "😷 Covid", 'payload': '/categoria{"category":1}'}, 
                    95: {'title': "🙋 Segnalazioni", 'payload': '/categoria{"category":95}'},
                    96: {'title': "👐 Volontariato", 'payload': '/categoria{"category":96}'}}
VIDE_BUTTON = {'title': "📅 Prenota Appuntamento", 'payload': '/vide'}

logger = logging.getLogger(__name__)


class ActionFallback(Action):
    def name(self) -> Text:
        return "action_fallback"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        comune = extract_comune(tracker)
        user_question = tracker.latest_message['text']
        answer_from_bot, confidence, question_id = await query_faqbot(user_question, comune)

        if confidence <= CONFIDENCE_TRESHOLD or answer_from_bot == '-1' or answer_from_bot == '-2':  # -1 -2 are error msg
            answer_from_bot = DB_WRAPPER.select_no_response_comune(comune)

        if FEEDBACK_YES_NO:
            b = domain.get('responses', {}).get(
                'utter_feedback_yes_no', [''])[0].get('buttons')
            dispatcher.utter_message(
                text=answer_from_bot, buttons=b, buttons_type='quick_replies')
        else:
            dispatcher.utter_message(text=answer_from_bot)
        return [SlotSet('question', user_question), SlotSet('answer', answer_from_bot), SlotSet('question_id', question_id)]


class ActionAnnouncement(Action):
    def name(self) -> Text:
        return "action_announcement"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        comune = extract_comune(tracker)
        avviso = DB_WRAPPER.select_avviso_comune(comune)

        dispatcher.utter_message(text=avviso)

        return []


class ActionVide(Action):
    def name(self) -> Text:
        return "action_vide"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        comune = extract_comune(tracker)
        vide_flag = DB_WRAPPER.select_vide_comune(comune)
        
        if vide_flag == True:
            vide_url = DB_WRAPPER.select_vide_url_comune(comune)
            if vide_url != '':
                vide_yes_message = domain.get('responses', {}).get('utter_vide_yes', [''])[0].get('text')
                vide_yes_message_with_link = vide_yes_message.format(vide_link=vide_url)
                dispatcher.utter_message(text=vide_yes_message_with_link)
                return []
                
        # if no vide flag or no vide url --> no response
        no_response = DB_WRAPPER.select_no_response_comune(comune)
        dispatcher.utter_message(text=no_response)
        return []


class ActionFeedback(Action):
    def name(self) -> Text:
        return "action_feedback"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        comune = extract_comune(tracker)
        feedback = extract_entity(tracker)

        DB_WRAPPER.insert_feedback(datetime=str(datetime.now()),
                                   id_session=tracker.sender_id,
                                   id_tenant=comune,
                                   content=feedback,
                                   last_question=tracker.get_slot('question'),
                                   last_answer=tracker.get_slot('answer'),
                                   question_id=tracker.get_slot('question_id'))

        dispatcher.utter_message(template='utter_thanks_for_feedback')
        return []


class ActionQuestionsOfCategory(Action):
    def name(self) -> Text:
        return "action_questions_of_category"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        comune = extract_comune(tracker)
        category = extract_entity(tracker)

        validated_questions = DB_WRAPPER.select_questions(comune)
        # TODO: this has to  be fixed in the query
        validated_questions_of_category = [q[0] for q in validated_questions if q[1] == category]
        buttons = [{'title': q, 'payload': q} for q in validated_questions_of_category]

        dispatcher.utter_message(template='utter_categoria', buttons=buttons)
        return []


class ActionCategories(Action):
    def name(self) -> Text:
        return "action_categories"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        comune = extract_comune(tracker)
        # TODO: the query return a tuple (id,) has to be fixed
        active_categories = [c[0] for c in DB_WRAPPER.select_categories(comune)]
        active_buttons = [CATEGORY_BUTTONS[ac] for ac in active_categories if ac in CATEGORY_BUTTONS]
        # vide
        vide_flag = DB_WRAPPER.select_vide_comune(comune)
        if vide_flag:
            active_buttons.append(VIDE_BUTTON)
        dispatcher.utter_message(
            template='utter_categories', buttons=active_buttons)
        return []


def extract_comune(tracker: Tracker) -> Optional[int]:
    return tracker.latest_message['metadata']['comune']


async def query_faqbot(message, comune) -> str:
    json = {"id": 1, "service": "query", "body": {
        "text": message, "tenant": str(comune)}}
    # TODO:hard fix of nivola proxy, NO SENSE
    proxies = {'http': None, 'https': None}

    #r = requests.post(csi_bot_url, json = json, verify=False, proxies=proxies)
    async with aiohttp.ClientSession() as session:
        async with session.post(CSI_BOT_URL, json=json) as resp:
            r = await resp.json()
    answer = r.get("result").get("answers")[0].get("text")
    confidence = r.get("result").get("answers")[0].get("confidence")
    id_question = r.get("result").get("answers")[0].get("index_ques")
    return answer, confidence, id_question
    #  r = await session).json()
    #  answer = r.json().get("result").get("answers")[0].get("text")
    #  confidence = r.json().get("result").get("answers")[0].get("confidence")
    #  return answer,confidence


def extract_entity(tracker):
    return tracker.latest_message['entities'][0]['value']
