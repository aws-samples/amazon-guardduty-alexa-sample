
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import boto3
import os
import re
from collections import Counter

# Variables

# Max number of findings to return. Although 50 can be returned without paginating,
# keeping this below 15 is a good idea to avoid Alexa size limit.
MAXRESP = os.environ['MAXRESP']

# Comma separated list of region codes with NO spaces to include in flash briefing stats.
# GuardDuty must be enabled in declared regions.
FLASHREGIONS = os.environ['FLASHREGIONS']


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
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

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to skill's launch
    return get_welcome_response()

def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch intent handlers
    if intent_name == "FlashBriefing":
        return get_flash_briefing(intent, session)
    elif intent_name == "SetRegion":
        return set_region_in_session(intent, session)
    elif intent_name == "ListFindings":
        return list_findings(intent, session)
    elif intent_name == "ListStats":
        return list_stats(intent, session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

# --------------- Functions that control the skill's behavior ------------------

# Initial welcome
def get_welcome_response():
    session_attributes = {}
    card_title = "Ask GuardDuty Welcome"
    should_end_session = False

    speech_output = "<speak>Welcome to Ask GuardDuty. <break time='.5s'/> To get started, you can get" \
                    " global GuardDuty finding statistics by saying, get flash briefing. For additional information, you can say, Help.</speak>"

    reprompt_text = "<speak>Are you still there? <break time='.3s'/> For regional statistics, you can say for example, get statistics for Virginia." \
                    " Or, get high severity findings for Oregon. You can also get" \
                    " global statistics by saying, <break time='.2s'/> Get flash briefing. For additional information, you can say, Help.</speak>"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def create_selected_region(selected_region):
    return {"selectedRegion": selected_region}

# Return region ID
def get_region_id(selectedRegion):
    if selectedRegion in {"Virginia", "virginia", "Northern Virginia", "northern virginia", "northern Virginia"}:
        return {"regionId": "us-east-1"}
    elif selectedRegion in {"Ohio", "ohio"}:
        return {"regionId": "us-east-2"}
    elif selectedRegion in {"Frankfurt", "frankfurt"}:
        return {"regionId": "eu-central-1"}
    elif selectedRegion in {"California", "california", "Northern California", "northern california", "northern California"}:
        return {"regionId": "us-west-1"}
    elif selectedRegion in {"Oregon", "oregon"}:
        return {"regionId": "us-west-2"}
    elif selectedRegion in {"London", "london"}:
        return {"regionId": "eu-west-2"}
    elif selectedRegion in {"Ireland", "ireland"}:
        return {"regionId": "eu-west-1"}
    elif selectedRegion in {"Singapore", "singapore"}:
        return {"regionId": "ap-southeast-1"}
    elif selectedRegion in {"Sydney", "sydney"}:
        return {"regionId": "ap-southeast-2"}
    elif selectedRegion in {"Canada", "canada", "Central", "central"}:
        return {"regionId": "ca-central-1"}
    elif selectedRegion in {"Sao Paulo", "sao paulo", "sao Paulo"}:
        return {"regionId": "sa-east-1"}
    elif selectedRegion in {"Seoul", "seoul"}:
        return {"regionId": "ap-northeast-2"}
    elif selectedRegion in {"Mumbai", "mumbai"}:
        return {"regionId": "ap-south-1"}
    elif selectedRegion in {"Tokyo", "tokyo"}:
        return {"regionId": "ap-northeast-1"}
    else:
        return {"regionId": "Unknown"}

# Return region friendly name
def get_region_name(region_id):
    if region_id == "us-east-1":
        return {"regionName": "Virginia"}
    elif region_id == "us-east-2":
        return {"regionName": "Ohio"}
    elif region_id == "us-west-1":
        return {"regionName": "California"}
    elif region_id == "eu-central-1":
        return {"regionName": "Frankfurt"}
    elif region_id == "us-west-2":
        return {"regionName": "Oregon"}
    elif region_id == "eu-west-2":
        return {"regionName": "London"}
    elif region_id == "ap-southeast-1":
        return {"regionName": "Singapore"}
    elif region_id == "ap-southeast-2":
        return {"regionName": "Sydney"}
    elif region_id == "eu-west-1":
        return {"regionName": "Ireland"}
    elif region_id == "ca-central-1":
        return {"regionName": "Canada"}
    elif region_id == "sa-east-1":
        return {"regionName": "Sao Paulo"}
    elif region_id == "ap-northeast-2":
        return {"regionName": "Seoul"}
    elif region_id == "ap-south-1":
        return {"regionName": "Mumbai"}
    elif region_id == "ap-northeast-1":
        return {"regionName": "Tokyo"}
    else:
        return {"regionName": ""}

# Get GuardDuty Flash Briefing
def get_flash_briefing(intent, session):
    session_attributes = {}
    card_title = "Ask GuardDuty Flash Briefing"
    should_end_session = False
    flashglobal = getflashbrief()[0]
    flashregion = getflashbrief()[1]

    if flashglobal:
        speech_output = "<speak> Here is your GuardDuty flash briefing." \
                        " <break time='.3s'/>Globally, there are, " + str(flashglobal) + " findings." \
                        " <break time='.5s'/>Here are the regional finding statistics: " + str(flashregion) + ".</speak>"
    else:
        speech_output = "<speak>There are no current GuardDuty findings for the selected AWS regions." \
                        " <break time='.2s'/>  You can generate samples in the console and GuardDuty will" \
                        " populate your current list with one sample finding for each supported type. </speak>"

    reprompt_text = "<speak>Are you still there? For regional statistics, you can say for example, get statistics for Virginia." \
                    " Or, get high severity findings for Oregon." \
                    " For additional information, you can say, Help.</speak>"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# Get finding details for region X and severity Y
def list_findings(intent, session):
    session_attributes = {}
    card_title = "Ask GardDuty Finding Details"
    should_end_session = False
    selected_region = intent['slots']['selectedRegion']['value']
    session_attributes = create_selected_region(selected_region)
    region_name = get_region_id(selected_region)['regionId']

    # Try to catch unknown or unsupported region
    if region_name == 'Unknown':
        speech_output = "<speak>I'm not sure which AWS region you would like me to access." \
                        " Please confirm the selected region is valid and GuardDuty is enabled.</speak>"

        reprompt_text = "<speak>Please confirm the selected region is valid and GuardDuty is enabled.</speak>"

        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    if region_name:
        try:
            sevname = intent['slots']['SevName']['value']
            min_sev = getsevvalue(sevname)['MinSev']
        except KeyError:
            min_sev = '0'

    # In case GD is not enabled for selected region.
    try:
        gdfindings = getfindings(minsev=min_sev, region_name=region_name)['Findings']
    except TypeError:
        gdfindings = [0]

    sgdfindings = []

    if 'selectedRegion' in intent['slots'] and gdfindings != [0]:
        selected_region = intent['slots']['selectedRegion']['value']
        for f in gdfindings:
            sevname = getsevname(str(f['Severity']))['SeverityName']
            description = str(f['Title'])
            sgdfindings.append("Severity, " + sevname + ", <break time='.2s'/>" + "Count, " + str(f['Service']['Count']) + ", <break time='.2s'/>" + description)
            # Clean up output
            findings = scruboutput(inputtxt = str(sgdfindings))

        if gdfindings:
            speech_output = "<speak>Here are up to " + MAXRESP + " GuardDuty findings for, " + selected_region + ", with minimum severity " + str(min_sev) + ". <break time='.5s'/> " + str(findings) + "</speak>"
        else:
            speech_output = "<speak>There are no current GuardDuty findings for, " + selected_region + ", with minimum severity " + str(min_sev) + ".</speak>"

    else:
        speech_output = "<speak>The was a problem retrieving the information. Please confirm GuardDuty" \
                        " is enabled in the " + selected_region + " region.</speak>"

    reprompt_text = "<speak>Are you still there? <break time='.3s'/> You can get GuardDuty" \
                    " finding details by saying for example, get high severity findings for Oregon. You can also get " \
                    " global statistics by saying, <break time='.2s'/> Get flash briefing. For additional information, you can say, Help.</speak>"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# Get statistics by region.
def list_stats(intent, session):
    session_attributes = {}
    card_title = "Ask GuardDuty Finding Statistics"
    should_end_session = False
    selected_region = intent['slots']['selectedRegion']['value']
    session_attributes = create_selected_region(selected_region)
    region_name = get_region_id(selected_region)['regionId']

    if region_name == 'Unknown':
        speech_output = "<speak>I'm not sure which AWS region you would like me to access." \
                        " Please confirm the selected region is valid and GuardDuty is enabled.</speak>"

        reprompt_text = "<speak>Are you still there? <break time='.3s'/> You can get GuardDuty" \
                        " finding details by saying, get high severity findings for Virginia. Or you can get global statistics by saying," \
                        "<break time='.2s'/> Get flash briefing. For additional information, you can say, Help.</speak>"

        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    try:
        gdstats = getstats(region_name=region_name)['FindingStatistics']['CountBySeverity']
    # In case GD is not enabled for selected region.
    except TypeError or KeyError:
        gdstats = [0]

    sgdstats = []
    if 'selectedRegion' in intent['slots'] and gdstats != [0]:
        selected_region = intent['slots']['selectedRegion']['value']
        for key, value in gdstats.items():
            sevname = getsevname(key)['SeverityName']
            sgdstats.append("<break time='.3s'/> " + str(value) + " " + sevname + " severity")
            # Clean up output
            stats = scruboutput(inputtxt = str(sgdstats))
        if sgdstats:
            speech_output = "<speak> In " + selected_region + ", there are currently, " + str(stats) + " findings. <break time='1s'/>  </speak>"
        else:
            speech_output = "<speak>There are no current findings in " + selected_region + "." \
                            " <break time='.2s'/> You can generate samples in the console and GuardDuty will" \
                            " populate your current list with one sample finding for each supported type. </speak>"

    else:
        speech_output = "<speak>The was a problem retrieving the information. Please confirm GuardDuty" \
                        " is enabled in the " + selected_region + " region.</speak>"

    reprompt_text = "<speak>Are you still there? <break time='.3s'/> You can get GuardDuty" \
                    " finding details by saying, get high severity findings for Virginia. Or you can get global statistics by saying," \
                    "<break time='.2s'/> Get flash briefing. For additional information, you can say, Help.</speak>"


    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# Get Help
def get_help():
    session_attributes = {}
    card_title = "Ask GuardDuty Help"
    should_end_session = False

    speech_output = "<speak>Welcome to Ask GardDuty.<break time='.3s'/> Amazon GuardDuty is a managed" \
                    " threat detection service that continuously monitors for" \
                    " malicious or unauthorized behavior to help you protect your AWS accounts and workloads." \
                    " <break time='.3s'/>GuardDuty generates findings when it detects unexpected and potentially malicious activity" \
                    " in your AWS environment.<break time='.3s'/> To get started, you can get" \
                    " global GuardDuty finding statistics by saying, get flash briefing. I am currently configured" \
                    " to return flash briefing information for the following AWS regions: " + getflashregions() + "." \
                    " You can also get finding statistics for a region by saying for example, get statistics for Oregon." \
                    " I can retrieve information for other AWS regions where GuardDuty is enabled." \
                    " You can get GuardDuty finding details by saying for example," \
                    " get high severity findings for California." \
                    " I am currently configured to return up to " + MAXRESP + " findings in a response." \
                    " Each GuardDuty finding has an assigned severity level and value that can help you determine your  " \
                    " response to a potential security issue that is highlighted by a finding. The value of the severity " \
                    " can fall within the 0.1 to 8.9 range. High severity findings fall within the 7.0 to 8.9 range," \
                    " medium severity falls within the 4.0 to 6.9 range and low severity falls within the  0.1 to 3.9 range." \
                    " You can generate samples in the console and GuardDuty will" \
                    " populate your current list with one sample finding for each supported type." \
                    " Finally, make sure GuardDuty is enabled in AWS regions you would like me to access.</speak>"

    reprompt_text = "<speak>Are you still there? To get started, you can say, get statistics for Virginia. You can also get" \
                    " global statistics by saying, get flash briefing. For additional information, you can say, Help.</speak>"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# Return GuardDuty detector Id for region
def getdetectorid(region_name):
    gdclient = boto3.client('guardduty', region_name=region_name)
    try:
        response = gdclient.list_detectors()['DetectorIds'][0]
    except IndexError:
        response = []
    return response

# Return finding severity name based on value
def getsevname(sevlevel):
    if float(sevlevel) < 4:
        return {"SeverityName": "Low"}
    elif 4 < float(sevlevel) < 7:
        return {"SeverityName": "Medium"}
    elif float(sevlevel) > 7:
        return {"SeverityName": "High"}
    else:
        return {"SeverityName": sevlevel}

# Return finding value value based on severity
def getsevvalue(sevname):
    if sevname == "low":
        return {"MinSev": "0", "MaxSev": "3.9"}
    if sevname == "medium":
        return {"MinSev": "4", "MaxSev": "6.9"}
    if sevname == "high":
        return {"MinSev": "7", "MaxSev": "10"}
    else:
        return {"MinSev": "0", "MaxSev": "10"}

# List regions declared in FLASHREGIONS by name
def getflashregions():
    flashregions = []
    try:
        regionids = FLASHREGIONS.split(",")
        for r in regionids:
            flashregions.append(get_region_name(r)['regionName'])
            # Clean up output
            response = scruboutput(inputtxt = str(flashregions))
    except IndexError or NameError:
        response = []
    return response

# Redact stuff from findings and clean up output for card display
def scruboutput(inputtxt):
    response = re.sub('&', 'and', inputtxt)
    response = re.sub(r'[\[\]\"]', '', response)
    response = re.sub(r'instance i-(\w+)', 'instance', response)
    response = re.sub(r'against i-(\w+)', 'against an EC2 instance', response)
    response = re.sub(r'([0-9]+)(?:\.[0-9]+){3}', 'IP host', response)
    return response

# ReturnGuardDuty Flash Briefing
def getflashbrief():
    # set the target regions to aggregate findng stats
    targ_regions = FLASHREGIONS.split(",")
    flashglobal = []
    flashregion = []
    c = Counter()
    for r in targ_regions:
        region_name = r
        rn = get_region_name(r)['regionName']
        response = getstats(region_name=region_name)['FindingStatistics']['CountBySeverity']
        if response:
            flashregion.append("<break time='.5s'/>Findings for " + str(rn) + " region")
            for key, value in response.items():
                sevname = getsevname(key)['SeverityName']
                #Sum total findings across regions declared in FLASHREGIONS
                c[key] += value
                flashregion.append("<break time='.2s'/>" + str(value) + " " + sevname + " severity")
        else:
            flashregion.append("<break time='.5s'/> There are no current findings in the " + str(rn) + " region.")

    t = dict(c)
    totals = t.items()
    for key, value in totals:
        sevname = getsevname(key)['SeverityName']
        flashglobal.append("<break time='.2s'/>" + str(value) + " " + sevname + " severity")

    # Clean up output
    fglobal = scruboutput(inputtxt = str(flashglobal))
    fregion = scruboutput(inputtxt = str(flashregion))
    return fglobal, fregion

# Return statistics for region
def getstats(region_name):
    gdclient = boto3.client('guardduty', region_name=region_name)
    detector_id = getdetectorid(region_name)
    if detector_id:
        response = gdclient.get_findings_statistics(
            DetectorId=detector_id,
            FindingCriteria={
                'Criterion': {
                    'severity': {
                            'Gte':
                                0,
                        }
                    }
                },
                FindingStatisticTypes=[
                    'COUNT_BY_SEVERITY',
                ]
            )
    else:
        response = []
    return response

# Return findings with minimum severity
def listfindings(minsev, region_name):
    gdclient = boto3.client('guardduty', region_name=region_name)
    detector_id = getdetectorid(region_name)
    if detector_id:
        response = gdclient.list_findings(
            DetectorId=detector_id,
            FindingCriteria={
                'Criterion': {
                    'severity': {
                            'Gte':
                                int(minsev),
                            }
                    }
                },
            MaxResults=int(MAXRESP),
            SortCriteria={
                'AttributeName': 'severity',
                'OrderBy': 'ASC'
            }
            )
    else:
        response = []
    return response

# Return finding details
def getfindings(minsev, region_name):
    gdclient = boto3.client('guardduty', region_name=region_name)
    detector_id = getdetectorid(region_name)
    if detector_id:
        gresponse = listfindings(minsev, region_name)
        response = gdclient.get_findings(
        DetectorId=detector_id,
        FindingIds=gresponse['FindingIds'],
        SortCriteria={
            'AttributeName': 'severity',
            'OrderBy': 'ASC'
            }
        )
    else:
        response = []
    return response

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = ""
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    cleanout = re.sub(r'(<([^>]+)>)', '', output)
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Standard',
            'title': title,
            'text': cleanout,
            'image': {
                'smallImageUrl': 'https://s3.amazonaws.com/awsiammedia/public/sample/GuardDutyStatisticsFindings/guarddutysmall.png',
                'largeImageUrl': 'https://s3.amazonaws.com/awsiammedia/public/sample/GuardDutyStatisticsFindings/guarddutylarge.png'
            }
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': reprompt_text
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
