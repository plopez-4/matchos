"""Optional bounded Azure speech. Text always comes from verified server facts."""
from collections import OrderedDict
from hashlib import sha256
import os
import re
import threading
import time
import httpx
from fastapi import HTTPException
from app.narration_text import recap_parts, spoken_clock
from app.pronunciation import speech_markup

PROFILES = {
    'warm': {'label':'Warm storyteller', 'en':('en-GB-RyanNeural','chat','cheerful'), 'es':('es-MX-DaliaNeural',None,'cheerful')},
    'matchday': {'label':'Matchday narrator', 'en':('en-US-DavisNeural','friendly','excited'), 'es':('es-MX-JorgeNeural','chat','excited')},
}
LOCK = threading.Lock()
CACHE = OrderedDict()
calls = characters = 0
MAX_AUDIO = 512 * 1024

def configuration():
    region = os.getenv('AZURE_SPEECH_REGION','')
    key = os.getenv('AZURE_SPEECH_KEY','')
    if os.getenv('MATCHOS_SPEECH_MODE','off')!='azure' or not re.fullmatch(r'[a-z][a-z0-9]{2,30}',region) or len(key)<16:
        return None
    return region,key


def status():
    return {'available':configuration() is not None, 'provider':'azure-speech',
            'profiles':[{'id':key,'label':value['label']} for key,value in PROFILES.items()]}


def build_ssml(briefing, language, profile):
    voice, calm, energized = PROFILES[profile][language]
    if briefing.get('narrative', {}).get('mode') == 'azure' or briefing.get('audience') == 'advanced' or 'story_plan' in briefing:
        # Read exactly the reviewed paragraph shown on screen, using measured voice style.
        parts = [(briefing['spoken_recap'][language], False)]
    else:
        parts = recap_parts(briefing, language)
    if len(' '.join(text for text, _ in parts)) > 3200:
        raise HTTPException(413, 'Narration is too long')
    paragraphs = []
    for text, energetic in parts:
        paragraph = f'<p>{speech_markup(text, language)}</p>'
        style = energized if energetic else calm
        if style:
            paragraph = f'<mstts:express-as style="{style}" styledegree="1.15">{paragraph}</mstts:express-as>'
        paragraphs.append(paragraph)
    narration = ''.join(paragraphs)
    ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{voice[:5]}"><voice name="{voice}">{narration}</voice></speak>'
    delivery = 'energized' if any(energetic for _, energetic in parts) else 'measured'
    return ssml, voice, delivery


def synthesize(briefing, language, profile):
    config = configuration()
    if not config:raise HTTPException(503,'Azure narration is not configured; a Speech resource is needed')
    ssml,voice,delivery = build_ssml(briefing,language,profile)
    region,key = config
    identity = sha256((region+ssml).encode()).hexdigest()
    if not LOCK.acquire(blocking=False):raise HTTPException(429,'Narration is busy; try again shortly')
    global calls,characters
    try:
        if identity in CACHE:
            CACHE.move_to_end(identity)
            return CACHE[identity],voice,delivery
        if calls>=50 or characters+len(ssml)>50000:
            raise HTTPException(429,'Demo narration budget reached')
        calls+=1; characters+=len(ssml)
        # Regional Azure-only endpoint; browser cannot supply a URL, text or key.
        with httpx.Client(timeout=8,follow_redirects=False) as client:
            with client.stream('POST',f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1',content=ssml.encode(),headers={
                'Ocp-Apim-Subscription-Key':key,'Content-Type':'application/ssml+xml',
                'X-Microsoft-OutputFormat':'audio-16khz-32kbitrate-mono-mp3','User-Agent':'MatchOS'}) as response:
                if response.status_code!=200 or response.headers.get('content-type','').split(';')[0]!='audio/mpeg':
                    raise HTTPException(502,'Azure narration could not be generated; check the Speech resource, region and quota')
                audio=bytearray(); deadline=time.monotonic()+10
                for chunk in response.iter_bytes(chunk_size=8192):
                    audio.extend(chunk)
                    if len(audio)>MAX_AUDIO or time.monotonic()>deadline:raise HTTPException(502,'Narration exceeded the response limit')
                if not audio:raise HTTPException(502,'Azure narration returned no audio')
        CACHE[identity]=bytes(audio)
        while len(CACHE)>8:CACHE.popitem(last=False)
        return bytes(audio),voice,delivery
    except httpx.HTTPError:
        raise HTTPException(502,'Azure narration is temporarily unavailable') from None
    finally:LOCK.release()
