from __future__ import print_function
import random
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bill_of_rights')

# --------------- Helpers that build all of the responses ----------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': '<speak>' + output + '</speak>'
        },
        'card': {
            'type': 'Simple',
            'title': " " + title,
            'content': " " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Hi there! You can ask me for a section of the Bill of Rights. What would you like to do?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I don't know if you heard me, what would you like to do?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_help_response():
    session_attributes = {}
    card_title = "Help"
    speech_output = "You can try saying, 'Tell me my rights'."
    reprompt_text = "I don't know if you heard me, but you can try saying, 'Tell me my rights'."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_section_response(intent):

    session_attributes = {}
    card_title = "Bill of Rights"
    reprompt_text = "Would you like to hear another?"
    should_end_session = False

    num = None  # unset state
    try:
        num = intent["slots"]["section"]["value"]
    except KeyError:
        pass

    test_msg = {}

    if num:
        # we have to look for a specific section number
        test_msg = table.get_item(
            Key={
                'section': str(num)
            })
        if 'Item' not in test_msg:
            # section number not found
            test_msg = "Sorry, there is no section " + \
                str(num) + " in my records."
        else:
            test_msg = "Section " + \
                str(test_msg['Item']['section']) + \
                ". " + str(test_msg['Item']['text'])
    else:
        # just take any random section
        test_msg = table.scan()
        # table.scan() with no parameters returns all of the rows
        # from the table (as long as it's less than some mb)

        test_msg = test_msg['Items'][
            random.randint(0, len(test_msg['Items']) - 1)]

        test_msg = "Section " + \
            str(test_msg['section']) + ". " + str(test_msg['text'])
        # structure for list of items {Items: [ {obj1}, {obj2}, {obj3} ],
        # count:, scannedcount:, metadata and other stuff}

    speech_output = test_msg

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_fallback_response():
    card_title = "Try again"
    speech_output = "I'm not sure what you're trying to do but you can ask me for a section from the Bill of Rights."
    reprompt_text = "Please try asking me for a section from the Bill of Rights."
    should_end_session = False
    session_attributes = {}
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session ended"
    speech_output = "Thank you for trying the constitution application. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Events ------------------


def on_session_started(session_started_request, session):
    pass


def on_launch(launch_request, session):
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "ConstitutionIntent":
        return get_section_response(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "AMAZON.FallbackIntent":
        return get_fallback_response()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # TODO: add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    print("Incoming request...")
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
