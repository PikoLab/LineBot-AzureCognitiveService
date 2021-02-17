import http.client, urllib.request, urllib.parse, urllib.error, base64
import requests, uuid, json
import time
import re
from random import sample
import azure.cognitiveservices.speech as speechsdk
from apiclient.discovery import build
import os



def image_to_text(img_data):
    #connect API: Computer Vision(detect text and language on the picture)
    #local img file: 'Content-Type': 'application/octet-stream'
    #img URL:'Content-Type': 'application/json'
    headers_cv = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': 'subscription_key',
    }

    params_cv = urllib.parse.urlencode({
        'language': 'unk', #AutoDetect language
        'detectOrientation ': 'true',
    })

    conn = http.client.HTTPSConnection('endpoint')
    
    
    # photo = "{'url':'%s'}"%(image_url)
    photo = img_data
    conn.request("POST", "/vision/v1.0/ocr?%s" % params_cv, photo, headers_cv)
    response = conn.getresponse()
    data = response.read()
    parsed = json.loads(data)
    lang=parsed['language'] 
    
    #connect API: Translate(translate English to Chinese)
    subscription_key = "subscription_key"
    endpoint = "endpoint"
    location = "global"
    path = '/translate'
    constructed_url = endpoint + path
    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': 'zh-Hant'
    }
    constructed_url = endpoint + path
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Code:translate English to Chinese and there is no service for other languages       
    if lang == 'en':
        ocr_text=" "
        for sentence in parsed['regions'][0]['lines']:
            for words in sentence['words']: 
                ocr_text+=words['text']+" "
        body = [{'text': ocr_text}] 
        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        response = request.json()
        ocr_text=response[0]['translations'][0]['text']
        print(ocr_text)

    elif lang == 'zh-Hant' or 'zh-Hans': #Traditional Chinese(zh-Hant)/(Simplified Chinese)zh-Hans
        ocr_text=" "
        for sentence in parsed['regions'][0]['lines']:
            for words in sentence['words']: 
                ocr_text+=words['text']
        print(ocr_text)
                
    else:
        print('Sorry, We only provide speech service for English and Chinese.')

    conn.close()    
    
    return ocr_text

def text_to_speech(ocr_text,filename):    
    #connect API: Text-to-Speech
    speech_key, service_region = "subscription_key", "service_region"
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region,speech_recognition_language='zh-TW')
    speech_config.speech_synthesis_language = 'zh-TW' #set language of speech
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    
    #Code: Text-to-Speech(save as wave file)
    if not os.path.exists('./static/audio/'):
        os.makedirs('./static/audio/')
    audio_filename = "./static/audio/%s.wav"%(filename)
    audio_output = speechsdk.audio.AudioOutputConfig(filename=audio_filename)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
    audio_result = speech_synthesizer.speak_text_async(ocr_text).get()#create an audio file
    
def text_to_ytsearch(ocr_text):   
    #connect API: Youtube Data API v3
    api_key='subscription_key'
    youtube=build('youtube','v3',developerKey=api_key)
    
    #Regular Expression: preprocessing keywords for YT search
    r1 = '[a-zA-Z0-9’!"#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}~]+'
    paragraph=re.sub(r1, '', ocr_text) 
    
    #Split string in a certain length
    keywords=[]
    x = 10
    for i in range(0, len(paragraph), x):
        keywords.append(paragraph[i: i + x]) 

    #Code: Connect Youtube Search Engine   
    results = list()
    if len(keywords) == 1:
        for keyword in keywords:
            req=youtube.search().list(q=keyword,part='snippet',type='video',maxResults=3) 
            res=req.execute()
            for item in res['items']:
                vid_obj = dict()
                vid_obj['video_thumbnails']=item['snippet']['thumbnails']['medium']['url']  
                vid_obj['video_url']='https://www.youtube.com/watch?v='+item['id']['videoId']
                results.append(vid_obj)
    
    elif len(keywords) == 2:
        for keyword in keywords:
            req=youtube.search().list(q=keyword,part='snippet',type='video',maxResults=1) 
            res=req.execute()
            for item in res['items']:
                vid_obj = dict()
                vid_obj['video_thumbnails']=item['snippet']['thumbnails']['medium']['url']  
                vid_obj['video_url']='https://www.youtube.com/watch?v='+item['id']['videoId']
                results.append(vid_obj)
    else:
        for keyword in sample(keywords, 3): #Random Sampling without replacement
            req=youtube.search().list(q=keyword,part='snippet',type='video',maxResults=1) 
            res=req.execute()
            for item in res['items']:
                vid_obj = dict()
                vid_obj['video_thumbnails']=item['snippet']['thumbnails']['medium']['url']  
                vid_obj['video_url']='https://www.youtube.com/watch?v='+item['id']['videoId']
                results.append(vid_obj)
    return results
        
        
        