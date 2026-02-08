#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bridge Python 2.7 pour communiquer entre Streamlit (Python 3) et NAOqi SDK
Communication via JSON sur stdin/stdout
"""

import sys
import os
import time
import json
import threading

# Charger les variables d'environnement
def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.example')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

env_vars = load_env()

lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, lib_path)

# Rediriger stderr pour capturer les logs NAOqi
import StringIO
log_buffer = []

class LogCapture:
    """Capture les print() et les envoie comme logs JSON"""
    def __init__(self, original):
        self.original = original
    
    def write(self, text):
        if text.strip():
            log_buffer.append(text.strip())
        self.original.write(text)
    
    def flush(self):
        self.original.flush()

# Ne PAS rediriger stdout car on l'utilise pour JSON
# On capture stderr pour les logs NAOqi
original_stderr = sys.stderr

def send_response(action, success, data=None, logs=None):
    """Envoyer une reponse JSON sur stdout"""
    response = {
        "action": action,
        "success": success,
        "data": data or {},
        "logs": logs or []
    }
    line = json.dumps(response)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def send_log(message):
    """Envoyer un log en temps reel"""
    response = {
        "action": "log",
        "success": True,
        "data": {"message": message},
        "logs": [message]
    }
    line = json.dumps(response)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


# Variable globale pour l'instance de conversation
conversation = None
naoqi_available = False

try:
    from naoqi import ALProxy, ALBroker, ALModule
    naoqi_available = True
except ImportError:
    naoqi_available = False


def handle_connect(params):
    """Gerer la connexion au robot"""
    global conversation
    
    nao_ip = str(params.get("nao_ip", "169.254.201.219"))
    nao_port = int(params.get("nao_port", 9559))
    
    if not naoqi_available:
        send_response("connect", False, {"error": "NAOqi SDK non disponible"})
        return
    
    try:
        send_log("Connexion au robot NAO a %s:%d..." % (nao_ip, nao_port))
        
        conversation = {
            "nao_ip": nao_ip,
            "nao_port": nao_port,
            "tts": ALProxy(str("ALTextToSpeech"), nao_ip, nao_port),
            "audio_recorder": ALProxy(str("ALAudioRecorder"), nao_ip, nao_port),
            "memory": ALProxy(str("ALMemory"), nao_ip, nao_port),
            "audio_device": ALProxy(str("ALAudioDevice"), nao_ip, nao_port),
            "motion": ALProxy(str("ALMotion"), nao_ip, nao_port),
            "leds": ALProxy(str("ALLeds"), nao_ip, nao_port),
            "tracker": ALProxy(str("ALTracker"), nao_ip, nao_port),
            "face_detection": ALProxy(str("ALFaceDetection"), nao_ip, nao_port),
            "audio_player": ALProxy(str("ALAudioPlayer"), nao_ip, nao_port),
            "groq_api_key": env_vars.get("GROQ_API_KEY", ""),
            "llm_model": env_vars.get("LLM_MODEL", "llama-3.3-70b-versatile"),
            "groq_api_url": "https://api.groq.com/openai/v1/chat/completions",
            "conversation_history": [],
            "tracking_active": False,
            "use_expressive_gestures": True,
            "silence_threshold": 1100,
            "silence_duration": 1.5,
            "language": str(params.get("language", env_vars.get("NAO_LANGUAGE", "fr"))),
            "system_prompt_fr": env_vars.get("SYSTEM_PROMPT_FR", "Tu es NAO, un robot assistant sympathique et serviable. Reponds de maniere concise et naturelle en francais. Garde tes reponses pas trop longues mais avec quelques explications car elles seront prononcees par un robot."),
            "system_prompt_en": env_vars.get("SYSTEM_PROMPT_EN", "You are NAO, a friendly and helpful robot assistant. Respond concisely and naturally in English. Keep your answers not too long but with some explanations as they will be spoken by a robot."),
            "greeting_fr": env_vars.get("GREETING_FR", "Bonjour! Je suis NAO, un robot assistant. Enchante! Comment puis-je t'aider?"),
            "greeting_en": env_vars.get("GREETING_EN", "Hello! I am NAO, a robot assistant. Nice to meet you! How can I help you?"),
        }
        
        # Configurer la langue du TTS
        lang = conversation["language"]
        tts_lang = "French" if lang == "fr" else "English"
        conversation["tts"].setLanguage(str(tts_lang))
        conversation["tts"].setVolume(0.8)
        send_log("OK Langue configuree: %s" % tts_lang)
        
        send_log("OK Connexion etablie avec succes!")
        
        # Verifier Groq
        if not conversation["groq_api_key"]:
            send_log("ATTENTION: GROQ_API_KEY non trouve dans .env")
        else:
            send_log("OK Configuration Groq valide (Modele: %s)" % conversation["llm_model"])
        
        send_response("connect", True, {"message": "Connecte a NAO"})
        
    except Exception as e:
        send_log("X Erreur de connexion: %s" % str(e))
        send_response("connect", False, {"error": str(e)})


def handle_listen(params):
    """Gerer l'ecoute et la transcription"""
    global conversation
    import requests
    
    if not conversation:
        send_response("listen", False, {"error": "Non connecte"})
        return
    
    max_duration = params.get("max_duration", 10)
    audio_file = "/tmp/temp_audio.wav"
    local_audio_file = "temp_audio.wav"
    
    try:
        # Arreter tout enregistrement en cours
        try:
            conversation["audio_recorder"].stopMicrophonesRecording()
        except:
            pass
        
        send_log(">>> Debut d'enregistrement")
        
        # Effet visuel
        try:
            conversation["leds"].fadeRGB("FaceLeds", 0x00FF00, 0.1)
            time.sleep(0.2)
        except:
            pass
        
        # Face tracking
        try:
            conversation["motion"].setStiffnesses("Head", 1.0)
            time.sleep(0.2)
            conversation["face_detection"].setParameter("Period", 500)
            conversation["face_detection"].enableTracking(True)
            conversation["tracker"].setMode("Head")
            conversation["tracker"].registerTarget("Face", 0.1)
            conversation["tracker"].track("Face")
            conversation["tracking_active"] = True
            send_log(">>> Suivi facial active")
        except Exception as e:
            send_log("X Erreur suivi facial: %s" % str(e))
        
        # LEDs ecoute
        try:
            conversation["leds"].post.fadeRGB("FaceLeds", 0x0000FF, 0.5)
        except:
            pass
        
        # Bip
        try:
            conversation["audio_device"].playSine(1200, 50, -1, 0.2)
            conversation["audio_device"].playSine(1500, 50, -1, 0.2)
        except:
            pass
        
        # Demarrer l'enregistrement
        channels = [0, 0, 1, 0]
        conversation["audio_recorder"].startMicrophonesRecording(audio_file, "wav", 16000, channels)
        send_log(">>> Enregistrement en cours...")
        
        # Detection de silence
        start_time = time.time()
        last_sound_time = start_time
        silence_start_time = None
        
        while True:
            elapsed = time.time() - start_time
            if elapsed >= max_duration:
                send_log(">>> Duree maximale atteinte")
                break
            
            try:
                conversation["audio_device"].enableEnergyComputation()
                audio_level = conversation["audio_device"].getFrontMicEnergy()
                
                if int(elapsed * 10) % 2 == 0:
                    conversation["leds"].post.fadeRGB("FaceLeds", 0x0000FF, 0.3)
                else:
                    conversation["leds"].post.fadeRGB("FaceLeds", 0x00FFFF, 0.3)
                
                if audio_level > conversation["silence_threshold"]:
                    last_sound_time = time.time()
                    silence_start_time = None
                    if int(elapsed * 10) % 5 == 0:
                        send_log(">>> Parole detectee (niveau: %d)" % audio_level)
                else:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    silence_elapsed = time.time() - silence_start_time
                    if silence_elapsed >= conversation["silence_duration"] and (last_sound_time - start_time) > 0.5:
                        send_log(">>> Silence detecte - arret automatique")
                        break
            except:
                pass
            
            time.sleep(0.1)
        
        # Arreter le suivi facial
        try:
            conversation["tracker"].stopTracker()
            conversation["tracker"].unregisterAllTargets()
            conversation["motion"].setAngles("HeadYaw", 0.0, 0.3)
            conversation["motion"].setAngles("HeadPitch", 0.0, 0.3)
            time.sleep(0.3)
            conversation["motion"].setStiffnesses("Head", 0.0)
            conversation["tracking_active"] = False
        except:
            pass
        
        # Remettre les yeux en blanc
        try:
            conversation["leds"].fadeRGB("FaceLeds", 0xFFFFFF, 0.5)
        except:
            pass
        
        # Arreter l'enregistrement
        conversation["audio_recorder"].stopMicrophonesRecording()
        send_log(">>> Enregistrement termine")
        
        # Telecharger le fichier audio
        send_log(">>> Telechargement de l'audio...")
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(conversation["nao_ip"], username='nao', password='nao')
        sftp = ssh.open_sftp()
        sftp.get(audio_file, local_audio_file)
        sftp.close()
        ssh.close()
        
        # Transcrire avec Groq Whisper
        send_log(">>> Transcription avec Groq Whisper...")
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": "Bearer %s" % conversation["groq_api_key"]}
        
        whisper_lang = str(conversation.get("language", "fr"))
        with open(local_audio_file, 'rb') as f:
            files = {
                'file': ('audio.wav', f, 'audio/wav'),
                'model': (None, 'whisper-large-v3'),
                'language': (None, whisper_lang)
            }
            response = requests.post(url, headers=headers, files=files, timeout=30)
        
        # Nettoyer
        try:
            os.remove(local_audio_file)
        except:
            pass
        
        if response.status_code == 200:
            result = response.json()
            transcription = result.get('text', '')
            send_log(">>> Texte reconnu: '%s'" % transcription)
            send_response("listen", True, {"transcription": transcription})
        else:
            send_log("X Erreur Whisper API (code %d)" % response.status_code)
            send_response("listen", False, {"error": "Erreur transcription"})
        
    except Exception as e:
        send_log("X Erreur ecoute: %s" % str(e))
        send_response("listen", False, {"error": str(e)})


def handle_think(params):
    """Animation de reflexion"""
    global conversation
    
    if not conversation:
        send_response("think", False, {"error": "Non connecte"})
        return
    
    try:
        import math
        import thread
        
        send_log(">>> Animation de reflexion...")
        
        conversation["motion"].setStiffnesses("RArm", 1.0)
        conversation["motion"].setStiffnesses("Head", 1.0)
        time.sleep(0.2)
        
        names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
        angles_up = [-1.22, -0.43, 0.22, 1.39, 0.52, 0.2]
        conversation["motion"].setAngles(names, angles_up, 0.2)
        time.sleep(1.0)
        
        conversation["motion"].setAngles("HeadPitch", 0.2, 0.3)
        conversation["motion"].setAngles("HeadYaw", -0.3, 0.3)
        time.sleep(0.5)
        
        try:
            thread.start_new_thread(conversation["tts"].say, ("Heummmmmmmmmmmm",))
        except:
            pass
        
        for _ in range(5):
            conversation["motion"].setAngles("RWristYaw", 0.52, 0.8)
            conversation["motion"].setAngles("RHand", 0.3, 0.9)
            time.sleep(0.2)
            conversation["motion"].setAngles("RWristYaw", 0.8, 0.52)
            conversation["motion"].setAngles("RHand", 0.5, 0.9)
            time.sleep(0.2)
        
        conversation["motion"].setAngles("RWristYaw", 0.0, 0.3)
        time.sleep(0.2)
        conversation["motion"].setAngles("HeadPitch", 0.0, 0.3)
        conversation["motion"].setAngles("HeadYaw", 0.0, 0.3)
        time.sleep(0.3)
        
        angles_rest = [
            60.4 * math.pi / 180,
            -17.0 * math.pi / 180,
            32.8 * math.pi / 180,
            88.5 * math.pi / 180,
            31.6 * math.pi / 180,
            0.22
        ]
        conversation["motion"].setAngles(names, angles_rest, 0.8)
        time.sleep(1.0)
        
        conversation["motion"].setStiffnesses("RArm", 0.0)
        conversation["motion"].setStiffnesses("Head", 0.0)
        
        send_log(">>> Animation terminee")
        send_response("think", True)
        
    except Exception as e:
        send_log("X Erreur animation: %s" % str(e))
        try:
            conversation["motion"].setStiffnesses("RArm", 0.0)
            conversation["motion"].setStiffnesses("Head", 0.0)
        except:
            pass
        send_response("think", True)


def handle_get_response(params):
    """Obtenir une reponse du LLM"""
    global conversation
    import requests
    
    if not conversation:
        send_response("get_response", False, {"error": "Non connecte"})
        return
    
    user_input = params.get("text", "")
    
    try:
        # Encoder le texte correctement pour Python 2.7
        if isinstance(user_input, unicode):
            user_input_str = user_input.encode('utf-8')
        else:
            user_input_str = user_input
        
        send_log(">>> Envoi a Groq LLM: '%s'" % user_input_str)
        send_log(">>> Langue: %s" % conversation.get("language", "fr"))
        
        conversation["conversation_history"].append({
            "role": "user",
            "content": user_input
        })
        
        lang = conversation.get("language", "fr")
        prompt_key = "system_prompt_fr" if lang == "fr" else "system_prompt_en"
        system_prompt = conversation[prompt_key]
        send_log(">>> Prompt: %s" % prompt_key)
        
        system_message = {
            "role": "system",
            "content": system_prompt
        }
        
        messages = [system_message] + conversation["conversation_history"]
        
        headers = {
            "Authorization": "Bearer %s" % str(conversation["groq_api_key"]),
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": str(conversation["llm_model"]),
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 350
        }
        
        payload_json = json.dumps(payload, ensure_ascii=False)
        if isinstance(payload_json, unicode):
            payload_json = payload_json.encode('utf-8')
        
        response = requests.post(
            str(conversation["groq_api_url"]),
            headers=headers,
            data=payload_json,
            timeout=30
        )
        
        send_log(">>> API status: %d" % response.status_code)
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result["choices"][0]["message"]["content"]
            
            conversation["conversation_history"].append({
                "role": "assistant",
                "content": llm_response
            })
            
            send_log(">>> Reponse LLM recue")
            send_response("get_response", True, {"response": llm_response})
        else:
            send_log("X Erreur API Groq (code %d): %s" % (response.status_code, response.text[:200]))
            send_response("get_response", False, {"error": "Erreur API Groq code %d" % response.status_code})
        
    except Exception as e:
        import traceback
        send_log("X Erreur LLM: %s" % str(e))
        send_log("X Traceback: %s" % traceback.format_exc())
        send_response("get_response", False, {"error": str(e)})


def handle_speak(params):
    """Faire parler le robot avec gestes"""
    global conversation
    
    if not conversation:
        send_response("speak", False, {"error": "Non connecte"})
        return
    
    text = params.get("text", "")
    
    try:
        import random
        import re
        
        send_log(">>> NAO dit: '%s'" % text)
        
        # Convertir en unicode si necessaire
        if isinstance(text, str):
            text = text.decode('utf-8')
        
        # Gestes expressifs
        if conversation["use_expressive_gestures"]:
            _speak_with_gestures(text)
        else:
            conversation["tts"].say(text.encode('utf-8'))
        
        # Reset bras
        if conversation["use_expressive_gestures"]:
            _reset_arms_to_rest()
        
        send_response("speak", True)
        
    except Exception as e:
        send_log("X Erreur parole: %s" % str(e))
        send_response("speak", True)


def _detect_gesture_type(text):
    """Detecter le type de geste"""
    import random
    
    text_lower = text.lower() if isinstance(text, unicode) else text.decode('utf-8').lower()
    
    question_words = [u'pourquoi', u'comment', u'quoi', u'qui', u'o\xf9', u'quand', u'quel', u'quelle', u'?']
    emphasis_words = [u'important', u'attention', u'!', u'vraiment', u'absolument', u'certainement',
                     u'tr\xe8s', u'super', u'magnifique', u'incroyable', u'g\xe9nial', u'excellent']
    explain_words = [u'parce que', u'donc', u'ainsi', u'par exemple', u'c\'est-\xe0-dire', u'en effet',
                    u'voici', u'voil\xe0', u'regardez', u'comme', u'si', u'alors']
    
    for word in emphasis_words:
        if word in text_lower:
            return "emphasis"
    for word in question_words:
        if word in text_lower:
            return "question"
    for word in explain_words:
        if word in text_lower:
            return "explain"
    
    if random.random() < 0.7:
        return "neutral"
    return None


def _perform_gesture(gesture_type):
    """Effectuer un geste expressif"""
    global conversation
    import random
    
    try:
        conversation["motion"].setStiffnesses("LArm", 0.8)
        conversation["motion"].setStiffnesses("RArm", 0.8)
        conversation["motion"].setStiffnesses("Head", 0.6)
        conversation["motion"].setStiffnesses("LLeg", 1.0)
        conversation["motion"].setStiffnesses("RLeg", 1.0)
        time.sleep(0.1)
        
        if gesture_type == "explain":
            names = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw",
                    "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw",
                    "HeadPitch", "HeadYaw"]
            angles_mid = [0.0, 0.3, -0.2, -0.4, 0.0, -0.3, 0.2, 0.4, -0.05, 0.0]
            conversation["motion"].setAngles(names, angles_mid, 0.12)
            time.sleep(0.5)
            angles = [-0.2, 0.6, -0.4, -0.8, -0.2, -0.6, 0.4, 0.8, -0.1, 0.0]
            conversation["motion"].post.setAngles(names, angles, 0.12)
            
        elif gesture_type == "question":
            side = random.choice(["L", "R"])
            if side == "L":
                names = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw",
                        "HeadPitch", "HeadYaw"]
                angles_mid = [-0.1, 0.3, -0.6, -0.3, 0.05, 0.1]
                conversation["motion"].setAngles(names, angles_mid, 0.12)
                time.sleep(0.4)
                angles = [-0.4, 0.5, -1.2, -0.5, 0.1, 0.2]
            else:
                names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw",
                        "HeadPitch", "HeadYaw"]
                angles_mid = [-0.1, -0.3, 0.6, 0.3, 0.05, -0.1]
                conversation["motion"].setAngles(names, angles_mid, 0.12)
                time.sleep(0.4)
                angles = [-0.4, -0.5, 1.2, 0.5, 0.1, -0.2]
            conversation["motion"].post.setAngles(names, angles, 0.12)
            
        elif gesture_type == "emphasis":
            names = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll",
                    "RShoulderPitch", "RShoulderRoll", "RElbowRoll",
                    "HeadPitch", "HeadYaw"]
            angles = [0.0, 0.3, -0.3, 0.0, -0.3, 0.3, -0.08, 0.0]
            conversation["motion"].setAngles(names, angles, 0.08)
            time.sleep(0.5)
            angles = [-0.2, 0.5, -0.5, -0.2, -0.5, 0.5, -0.15, 0.0]
            conversation["motion"].setAngles(names, angles, 0.08)
            time.sleep(0.5)
            angles = [-0.3, 0.4, -0.6, -0.3, -0.4, 0.6, 0.0, 0.0]
            conversation["motion"].post.setAngles(names, angles, 0.12)
            
        else:  # neutral
            side = random.choice(["L", "R"])
            head_yaw = random.choice([-0.15, 0.15])
            if side == "L":
                names = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "HeadYaw"]
                angles_mid = [0.0, 0.2, -0.3, head_yaw * 0.5]
                conversation["motion"].setAngles(names, angles_mid, 0.08)
                time.sleep(0.4)
                angles = [-0.2, 0.4, -0.5, head_yaw]
            else:
                names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "HeadYaw"]
                angles_mid = [0.0, -0.2, 0.3, head_yaw * 0.5]
                conversation["motion"].setAngles(names, angles_mid, 0.08)
                time.sleep(0.4)
                angles = [-0.2, -0.4, 0.5, head_yaw]
            conversation["motion"].post.setAngles(names, angles, 0.08)
    except:
        pass


def _reset_arms_to_rest():
    """Remettre les bras en position repos"""
    global conversation
    try:
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw",
                "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw",
                "HeadPitch", "HeadYaw"]
        
        angles_mid = [0.3, 0.05, -0.5, -0.3, 0.3, -0.05, 0.5, 0.3, 0.0, 0.0]
        conversation["motion"].setAngles(names, angles_mid, 0.12)
        time.sleep(0.5)
        
        angles = [1.0, 0.1, -1.0, -0.5, 1.0, -0.1, 1.0, 0.5, 0.0, 0.0]
        conversation["motion"].setAngles(names, angles, 0.12)
        time.sleep(0.8)
        
        conversation["motion"].setStiffnesses("LArm", 0.0)
        conversation["motion"].setStiffnesses("RArm", 0.0)
        conversation["motion"].setStiffnesses("Head", 0.0)
        conversation["motion"].setStiffnesses("LLeg", 0.0)
        conversation["motion"].setStiffnesses("RLeg", 0.0)
    except:
        pass


def _speak_with_gestures(text):
    """Parler avec gestes aux phrases completes"""
    global conversation
    import re
    
    sentences = re.split(r'([.!?])', text)
    
    for i, segment in enumerate(sentences):
        segment = segment.strip()
        if not segment:
            continue
        
        if segment in ['.', '!', '?']:
            _reset_arms_to_rest()
            time.sleep(0.4)
            continue
        
        gesture_type = _detect_gesture_type(segment)
        if gesture_type:
            send_log(">>> Geste: %s" % gesture_type)
            _perform_gesture(gesture_type)
        else:
            send_log(">>> Geste: neutral")
            _perform_gesture("neutral")
        
        segment_utf8 = segment.encode('utf-8')
        conversation["tts"].say(segment_utf8)


def handle_disconnect(params):
    """Deconnecter le robot"""
    global conversation
    
    if conversation:
        try:
            if conversation.get("tracking_active"):
                conversation["tracker"].stopTracker()
                conversation["tracker"].unregisterAllTargets()
                conversation["motion"].setStiffnesses("Head", 0.0)
        except:
            pass
        
        try:
            conversation["motion"].setStiffnesses("LArm", 0.0)
            conversation["motion"].setStiffnesses("RArm", 0.0)
            conversation["motion"].setStiffnesses("Head", 0.0)
        except:
            pass
        
        conversation = None
    
    send_log(">>> Deconnecte du robot")
    send_response("disconnect", True)


def handle_set_language(params):
    """Changer la langue dynamiquement"""
    global conversation
    
    if not conversation:
        send_response("set_language", False, {"error": "Non connecte"})
        return
    
    lang = str(params.get("language", "fr"))
    conversation["language"] = lang
    
    tts_lang = "French" if lang == "fr" else "English"
    try:
        conversation["tts"].setLanguage(str(tts_lang))
    except:
        pass
    
    send_log("OK Langue changee: %s" % tts_lang)
    send_response("set_language", True)


def handle_say_greeting(params):
    """Faire dire le message d'accueil"""
    global conversation
    
    if not conversation:
        send_response("say_greeting", False, {"error": "Non connecte"})
        return
    
    try:
        lang = params.get("language", conversation.get("language", "fr"))
        if lang == "fr":
            text = conversation.get("greeting_fr", u"Bonjour! Je suis NAO, un robot assistant. Enchant\xe9! Comment puis-je t'aider?")
        else:
            text = conversation.get("greeting_en", u"Hello! I am NAO, a robot assistant. Nice to meet you! How can I help you?")
        
        if isinstance(text, str):
            text = text.decode('utf-8', 'ignore')
        
        if conversation["use_expressive_gestures"]:
            _speak_with_gestures(text)
            _reset_arms_to_rest()
        else:
            conversation["tts"].say(text.encode('utf-8'))
        
        send_response("say_greeting", True, {"text": text})
    except Exception as e:
        send_log("X Erreur accueil: %s" % str(e))
        send_response("say_greeting", False, {"error": str(e)})


# Boucle principale - lecture des commandes JSON sur stdin
def main():
    handlers = {
        "connect": handle_connect,
        "listen": handle_listen,
        "think": handle_think,
        "get_response": handle_get_response,
        "speak": handle_speak,
        "disconnect": handle_disconnect,
        "say_greeting": handle_say_greeting,
        "set_language": handle_set_language,
    }
    
    send_response("ready", True, {"message": "Bridge NAO pret"})
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                command = json.loads(line)
            except ValueError:
                send_response("error", False, {"error": "JSON invalide"})
                continue
            
            action = command.get("action", "")
            params = command.get("params", {})
            
            if action == "quit":
                handle_disconnect({})
                break
            
            handler = handlers.get(action)
            if handler:
                handler(params)
            else:
                send_response("error", False, {"error": "Action inconnue: %s" % action})
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            send_response("error", False, {"error": str(e)})


if __name__ == "__main__":
    main()
