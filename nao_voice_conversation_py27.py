#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de conversation vocale pour le robot NAO V3 (Python 2.7 compatible)
Utilise le microphone de NAO pour ecouter, Groq LLM pour generer des reponses,
et la synthese vocale de NAO pour repondre
"""

import sys
import os
import time
import json
import requests

# Charger les variables d'environnement manuellement
def load_env():
    """Charger le fichier .env manuellement"""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
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

print("=" * 60)
print("   CONVERSATION VOCALE NAO V3 avec Groq LLM")
print("=" * 60)
print()

try:
    from naoqi import ALProxy, ALBroker, ALModule
    print("OK SDK NAOqi charge avec succes!")
except ImportError as e:
    print("X Erreur: Impossible de charger le SDK NAOqi")
    print("Erreur:", str(e))
    sys.exit(1)

print()


class VoiceConversation:
    """Classe pour la conversation vocale avec NAO et Groq LLM"""
    
    def __init__(self, nao_ip, nao_port=9559):
        """Initialisation"""
        self.nao_ip = nao_ip
        self.nao_port = nao_port
        
        # Proxies NAOqi
        self.tts = None
        self.audio_recorder = None
        self.memory = None
        self.audio_device = None
        self.motion = None
        self.leds = None
        self.tracker = None
        self.face_detection = None
        self.audio_player = None
        
        # Configuration Groq
        self.groq_api_key = env_vars.get("GROQ_API_KEY", "")
        self.llm_model = env_vars.get("LLM_MODEL", "llama-3.3-70b-versatile")
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Historique de conversation
        self.conversation_history = []
        
        # Etat du suivi facial
        self.tracking_active = False
        
    def connect(self):
        """Connexion au robot NAO"""
        print("Connexion au robot NAO a %s:%d..." % (self.nao_ip, self.nao_port))
        try:
            self.tts = ALProxy("ALTextToSpeech", self.nao_ip, self.nao_port)
            self.audio_recorder = ALProxy("ALAudioRecorder", self.nao_ip, self.nao_port)
            self.memory = ALProxy("ALMemory", self.nao_ip, self.nao_port)
            self.audio_device = ALProxy("ALAudioDevice", self.nao_ip, self.nao_port)
            self.motion = ALProxy("ALMotion", self.nao_ip, self.nao_port)
            self.leds = ALProxy("ALLeds", self.nao_ip, self.nao_port)
            self.tracker = ALProxy("ALTracker", self.nao_ip, self.nao_port)
            self.face_detection = ALProxy("ALFaceDetection", self.nao_ip, self.nao_port)
            self.audio_player = ALProxy("ALAudioPlayer", self.nao_ip, self.nao_port)
            print("OK Connexion etablie avec succes!")
            return True
        except Exception as e:
            print("X Erreur de connexion:", str(e))
            return False
    
    def check_groq_config(self):
        """Verifier la configuration Groq"""
        print("Verification de la configuration Groq LLM...")
        
        if not self.groq_api_key:
            print("X Erreur: GROQ_API_KEY non trouve dans .env")
            return False
        
        print("OK Configuration Groq valide (Modele: %s)" % self.llm_model)
        return True
    
    def configure_audio_recorder(self):
        """Configurer l'enregistreur audio"""
        print("Configuration de l'enregistreur audio...")
        
        try:
            # Pas de configuration speciale necessaire
            print("OK Enregistreur audio pret")
            return True
        except Exception as e:
            print("X Erreur de configuration:", str(e))
            return False
    
    def start_face_tracking(self):
        """Demarrer le suivi facial pendant l'ecoute"""
        try:
            if self.tracking_active:
                return
            
            print(">>> Activation du suivi facial...")
            
            # Activer les moteurs de la tete pour le suivi
            self.motion.setStiffnesses("Head", 1.0)
            time.sleep(0.2)
            
            # Position initiale
            self.motion.setAngles("HeadYaw", 0.0, 0.3)
            self.motion.setAngles("HeadPitch", 0.0, 0.3)
            time.sleep(0.3)
            
            # Configurer la detection de visages
            self.face_detection.setParameter("Period", 500)
            self.face_detection.enableTracking(True)
            
            # Configurer le tracker pour suivre avec la tete
            self.tracker.setMode("Head")
            self.tracker.registerTarget("Face", 0.1)
            
            # Demarrer le suivi
            self.tracker.track("Face")
            
            self.tracking_active = True
            print(">>> Suivi facial active - le robot vous suit du regard")
            
        except Exception as e:
            print("X Erreur suivi facial:", str(e))
            import traceback
            traceback.print_exc()
    
    def stop_face_tracking(self):
        """Arreter le suivi facial"""
        try:
            if not self.tracking_active:
                return
            
            print(">>> Arret du suivi facial...")
            
            # Arreter le tracker
            self.tracker.stopTracker()
            self.tracker.unregisterAllTargets()
            
            # Remettre la tete en position initiale
            self.motion.setAngles("HeadYaw", 0.0, 0.3)
            self.motion.setAngles("HeadPitch", 0.0, 0.3)
            time.sleep(0.5)
            
            # Desactiver les moteurs de la tete
            self.motion.setStiffnesses("Head", 0.0)
            
            self.tracking_active = False
            print(">>> Suivi facial desactive")
            
        except Exception as e:
            print("X Erreur arret suivi:", str(e))
            import traceback
            traceback.print_exc()
    
    def set_listening_eyes(self):
        """Effet lumineux des yeux pendant l'ecoute (comme reconnaissance vocale)"""
        try:
            # Effet de rotation des LEDs comme dans la reconnaissance vocale NAOqi
            # Utilise un effet rotatif bleu/cyan
            self.leds.post.fadeRGB("FaceLeds", 0x0000FF, 0.5)  # Bleu
            time.sleep(0.1)
            self.leds.post.fadeRGB("FaceLeds", 0x00FFFF, 0.5)  # Cyan
        except Exception as e:
            print("X Erreur LEDs:", str(e))
    
    def reset_eyes(self):
        """Remettre les yeux en blanc (normal)"""
        try:
            self.leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)  # Blanc
        except Exception as e:
            print("X Erreur reset LEDs:", str(e))
    
    def play_beep(self, frequency=800, duration=0.2):
        """Jouer un son bip avec une frequence donnee"""
        try:
            # Utiliser ALAudioDevice pour generer un ton
            # Frequence en Hz, duree en secondes
            self.audio_device.playWebStream("http://www.soundjay.com/button/beep-07.wav", 0.5, 0, 0)
        except:
            # Si ca ne marche pas, utiliser les LEDs comme feedback visuel
            try:
                self.leds.fadeRGB("EarLeds", 0x00FF00, 0.1)
                time.sleep(duration)
                self.leds.fadeRGB("EarLeds", 0x000000, 0.1)
            except:
                pass
    
    def thinking_animation(self):
        """Animation de reflexion: gratter la tete avec mouvement et son"""
        print()
        print(">>> Animation de reflexion...")
        
        try:
            import thread
            import math
            
            # Activer les moteurs du bras droit et de la tete
            self.motion.setStiffnesses("RArm", 1.0)
            self.motion.setStiffnesses("Head", 1.0)
            time.sleep(0.2)
                        
            # Lever le bras vers la tete
            names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            angles_up = [-1.22, -0.43, 0.22, 1.39, 0.52, 0.2]
            self.motion.setAngles(names, angles_up, 0.2)
            time.sleep(1.0)

            # Incliner legerement la tete sur le cote
            self.motion.setAngles("HeadPitch", 0.2, 0.3)
            self.motion.setAngles("HeadYaw", -0.3, 0.3)
            time.sleep(0.5)
            
            # Lancer le son en thread non-bloquant
            try:
                thread.start_new_thread(self.tts.say, ("Heummmmmmmmmmmm",))
            except:
                pass

            # Mouvement de grattage avec doigts (5 fois pour effet realiste)
            for _ in range(5):
                self.motion.setAngles("RWristYaw", 0.52, 0.8)
                self.motion.setAngles("RHand", 0.3, 0.9)
                time.sleep(0.2)
                self.motion.setAngles("RWristYaw", 0.8, 0.52)
                self.motion.setAngles("RHand", 0.5, 0.9)
                time.sleep(0.2)
            
            # Remettre le poignet au centre
            self.motion.setAngles("RWristYaw", 0.0, 0.3)
            time.sleep(0.2)
            
            # Remettre la tete droite
            self.motion.setAngles("HeadPitch", 0.0, 0.3)
            self.motion.setAngles("HeadYaw", 0.0, 0.3)
            time.sleep(0.3)
            
            # Ramener le bras en position repos specifiee
            angles_rest = [
                60.4 * math.pi / 180,   # RShoulderPitch = 60.4°
                -17.0 * math.pi / 180,  # RShoulderRoll = -17.0°
                32.8 * math.pi / 180,   # RElbowYaw = 32.8°
                88.5 * math.pi / 180,   # RElbowRoll = 88.5°
                31.6 * math.pi / 180,   # RWristYaw = 31.6°
                0.22                     # RHand = 0.22
            ]
            self.motion.setAngles(names, angles_rest, 0.8)
            
            # Attendre que le mouvement soit termine
            time.sleep(1.0)
            
            # Desactiver les moteurs
            self.motion.setStiffnesses("RArm", 0.0)
            self.motion.setStiffnesses("Head", 0.0)
            
            print(">>> Animation terminee - pret a parler")
            
        except Exception as e:
            print("X Erreur lors de l'animation:", str(e))
            try:
                self.motion.setStiffnesses("RArm", 0.0)
                self.motion.setStiffnesses("Head", 0.0)
            except:
                pass
    
    def listen(self, duration=5):
        """Ecouter via le microphone de NAO et transcrire avec Whisper
        
        Args:
            duration: Duree d'enregistrement en secondes
        """
        print()
        print("=" * 60)
        print("ENREGISTREMENT EN COURS - Parlez maintenant!")
        print("=" * 60)
        print("Duree: %d secondes" % duration)
        print()
        
        # Fichier audio temporaire (utiliser /tmp qui existe toujours)
        audio_file = "/tmp/temp_audio.wav"
        local_audio_file = "temp_audio.wav"
        
        try:
            # Arreter tout enregistrement en cours (au cas ou)
            try:
                self.audio_recorder.stopMicrophonesRecording()
            except:
                pass  # Pas grave si rien n'etait en cours
            
            # Effet sonore de debut d'enregistrement (bip court)
            print(">>> Bip - Debut d'enregistrement")
            try:
                # Utiliser un ton simple avec ALAudioDevice
                # Jouer un son systeme ou utiliser les LEDs des yeux
                self.leds.fadeRGB("FaceLeds", 0x00FF00, 0.1)
                time.sleep(0.2)
            except:
                pass
            
            # Activer le suivi facial pendant l'ecoute
            self.start_face_tracking()
            
            # Effet lumineux des yeux (comme reconnaissance vocale)
            self.set_listening_eyes()
            
            # Demarrer l'enregistrement
            # Format: 16000 Hz, 16 bits, mono, WAV
            channels = [0, 0, 1, 0]  # Front microphone
            self.audio_recorder.startMicrophonesRecording(audio_file, "wav", 16000, channels)
            
            print(">>> Enregistrement en cours...")
            print(">>> Suivi facial actif - le robot vous regarde")
            
            # Barre de progression avec effet LED alternatif
            for i in range(duration):
                # Alterner les couleurs des yeux pendant l'ecoute
                try:
                    if i % 2 == 0:
                        self.leds.post.fadeRGB("FaceLeds", 0x0000FF, 0.3)  # Bleu
                    else:
                        self.leds.post.fadeRGB("FaceLeds", 0x00FFFF, 0.3)  # Cyan
                except:
                    pass
                
                time.sleep(1)
                remaining = duration - i - 1
                if remaining > 0:
                    print(">>> %d secondes restantes..." % remaining)
            
            # Arreter le suivi facial
            self.stop_face_tracking()
            
            # Remettre les yeux en blanc
            self.reset_eyes()
            
            # Arreter l'enregistrement
            self.audio_recorder.stopMicrophonesRecording()
            
            # Effet sonore de fin d'enregistrement (double bip)
            print(">>> Bip bip - Fin d'enregistrement")
            try:
                # Double flash LED yeux en vert pour effet bip bip
                self.leds.fadeRGB("FaceLeds", 0x00FF00, 0.1)
                time.sleep(0.15)
                self.leds.fadeRGB("FaceLeds", 0x000000, 0.1)
                time.sleep(0.15)
                self.leds.fadeRGB("FaceLeds", 0x00FF00, 0.1)
                time.sleep(0.15)
            except:
                pass
            
            print()
            print("=" * 60)
            print("ENREGISTREMENT TERMINE")
            print("=" * 60)
            print()
            
            # Telecharger le fichier audio depuis NAO
            print("Telechargement de l'audio...")
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.nao_ip, username='nao', password='nao')
            
            sftp = ssh.open_sftp()
            sftp.get(audio_file, local_audio_file)
            sftp.close()
            ssh.close()
            
            print("Audio telecharge: %s" % local_audio_file)
            
            # Transcrire avec Groq Whisper
            transcription = self.transcribe_audio(local_audio_file)
            
            # Nettoyer le fichier temporaire
            try:
                os.remove(local_audio_file)
            except:
                pass
            
            if transcription:
                print("Texte reconnu: '%s'" % transcription)
                return transcription
            else:
                print("Aucun texte reconnu")
                return None
                
        except Exception as e:
            print("X Erreur lors de l'ecoute:", str(e))
            return None
    
    def transcribe_audio(self, audio_file_path):
        """Transcrire un fichier audio avec Groq Whisper API"""
        print("Transcription avec Groq Whisper...")
        
        try:
            # Preparer la requete multipart
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            
            headers = {
                "Authorization": "Bearer %s" % self.groq_api_key
            }
            
            # Lire le fichier audio
            with open(audio_file_path, 'rb') as f:
                files = {
                    'file': ('audio.wav', f, 'audio/wav'),
                    'model': (None, 'whisper-large-v3'),
                    'language': (None, 'fr')
                }
                
                response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get('text', '')
                return transcription
            else:
                print("X Erreur Whisper API (code %d): %s" % (response.status_code, response.text))
                return None
                
        except Exception as e:
            print("X Erreur lors de la transcription:", str(e))
            return None
    
    def get_llm_response(self, user_input):
        """Obtenir une reponse du LLM Groq via API HTTP"""
        print()
        print("Envoi a Groq LLM: '%s'" % user_input)
        
        try:
            # Ajouter le message utilisateur a l'historique
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Creer le contexte systeme
            system_message = {
                "role": "system",
                "content": "Tu es NAO, un robot assistant sympathique et serviable. "
                          "Reponds de maniere concise et naturelle en francais. "
                          "Garde tes reponses relativement courtes car elles seront "
                          "prononcees par un robot."
            }
            
            # Preparer les messages pour l'API
            messages = [system_message] + self.conversation_history
            
            # Preparer la requete
            headers = {
                "Authorization": "Bearer %s" % self.groq_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.llm_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 350
            }
            
            # Appeler l'API Groq
            response = requests.post(
                self.groq_api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                
                # Ajouter la reponse a l'historique
                self.conversation_history.append({
                    "role": "assistant",
                    "content": llm_response
                })
                
                print("Reponse du LLM: '%s'" % llm_response)
                return llm_response
            else:
                print("X Erreur API Groq (code %d): %s" % (response.status_code, response.text))
                return "Desole, je n'ai pas pu traiter votre demande."
            
        except Exception as e:
            print("X Erreur lors de l'appel a Groq:", str(e))
            return "Desole, je n'ai pas pu traiter votre demande."
    
    def speak(self, text):
        """Faire parler le robot"""
        print()
        print("NAO dit: '%s'" % text)
        try:
            # Convertir en unicode si necessaire pour Python 2.7
            if isinstance(text, str):
                text = text.decode('utf-8')
            # Convertir en UTF-8 pour NAO (preserve les accents francais)
            text_utf8 = text.encode('utf-8')
            self.tts.say(text_utf8)
        except Exception as e:
            print("X Erreur lors de la synthese vocale:", str(e))
    
    def conversation_loop(self, num_exchanges=3):
        """Boucle de conversation"""
        print()
        print("-" * 60)
        print("Debut de la conversation (Ctrl+C pour arreter)")
        print("-" * 60)
        print()
        
        self.speak("Bonjour! je suis NAO, un robot assistant. Enchanté ! Comment puis-je t'aider ?")
        
        for i in range(num_exchanges):
            print()
            print("=" * 60)
            print("Echange %d/%d" % (i + 1, num_exchanges))
            print("=" * 60)
            
            # Ecouter l'utilisateur (4 secondes)
            user_input = self.listen(duration=5)
            
            if not user_input:
                self.speak("Je n'ai pas compris. Pouvez-vous repeter?")
                continue
            
            # Animation de reflexion apres l'enregistrement (bloquante)
            self.thinking_animation()
            
            # Obtenir la reponse du LLM (bloquant - appel API)
            response = self.get_llm_response(user_input)
            
            # Faire parler le robot (bloquant - attend la fin de la parole)
            self.speak(response)
            
            time.sleep(1)
        
        self.speak("Merci pour cette conversation! A bientot!")


def main():
    """Fonction principale"""
    NAO_IP = "169.254.201.219"
    NAO_PORT = 9559
    
    # Creer l'instance de conversation
    conversation = VoiceConversation(NAO_IP, NAO_PORT)
    
    # Connexion au robot
    if not conversation.connect():
        print("Impossible de se connecter au robot NAO")
        sys.exit(1)
    
    print()
    
    # Verifier la configuration Groq
    if not conversation.check_groq_config():
        print("Impossible de configurer Groq LLM")
        sys.exit(1)
    
    print()
    
    # Configurer l'enregistreur audio
    if not conversation.configure_audio_recorder():
        print("Impossible de configurer l'enregistreur audio")
        sys.exit(1)
    
    print()
    
    # Configurer la langue et le volume
    conversation.tts.setLanguage("French")
    conversation.tts.setVolume(0.8)
    
    try:
        # Lancer la boucle de conversation
        conversation.conversation_loop(num_exchanges=5)
    
    except KeyboardInterrupt:
        print()
        print("Interruption clavier")
    
    except Exception as e:
        print()
        print("X Erreur:", str(e))
    
    finally:
        print()
        print("-" * 60)
        print("OK Programme termine avec succes!")
        print("=" * 60)


if __name__ == "__main__":
    main()
