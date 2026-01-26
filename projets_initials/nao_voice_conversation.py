#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de conversation vocale pour le robot NAO V3
Utilise le microphone de NAO pour ecouter, Groq LLM pour generer des reponses,
et la synthese vocale de NAO pour repondre
"""

import sys
import os
import time
from dotenv import load_dotenv
from groq import Groq

# Charger les variables d'environnement
load_dotenv()

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
        self.asr = None  # ALSpeechRecognition
        self.memory = None
        self.audio_device = None
        
        # Client Groq
        self.groq_client = None
        self.llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        
        # Historique de conversation
        self.conversation_history = []
        
    def connect(self):
        """Connexion au robot NAO"""
        print("Connexion au robot NAO a %s:%d..." % (self.nao_ip, self.nao_port))
        try:
            self.tts = ALProxy("ALTextToSpeech", self.nao_ip, self.nao_port)
            self.asr = ALProxy("ALSpeechRecognition", self.nao_ip, self.nao_port)
            self.memory = ALProxy("ALMemory", self.nao_ip, self.nao_port)
            self.audio_device = ALProxy("ALAudioDevice", self.nao_ip, self.nao_port)
            print("OK Connexion etablie avec succes!")
            return True
        except Exception as e:
            print("X Erreur de connexion:", str(e))
            return False
    
    def initialize_groq(self):
        """Initialiser le client Groq"""
        print("Initialisation du client Groq LLM...")
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            print("X Erreur: GROQ_API_KEY non trouve dans .env")
            return False
        
        try:
            self.groq_client = Groq(api_key=api_key)
            print("OK Client Groq initialise (Modele: %s)" % self.llm_model)
            return True
        except Exception as e:
            print("X Erreur d'initialisation Groq:", str(e))
            return False
    
    def configure_speech_recognition(self):
        """Configurer la reconnaissance vocale"""
        print("Configuration de la reconnaissance vocale...")
        
        try:
            # Definir la langue
            self.asr.setLanguage("French")
            
            # Definir un vocabulaire large pour capturer tout
            # Note: NAO V3 a des limitations sur la reconnaissance vocale
            # On utilise un vocabulaire ouvert
            vocabulary = [
                "oui", "non", "bonjour", "salut", "merci", "au revoir",
                "comment", "quoi", "qui", "ou", "quand", "pourquoi",
                "robot", "aide", "question", "reponse"
            ]
            
            self.asr.setVocabulary(vocabulary, False)
            
            print("OK Reconnaissance vocale configuree")
            return True
        except Exception as e:
            print("X Erreur de configuration:", str(e))
            return False
    
    def listen(self, duration=5):
        """Ecouter via le microphone de NAO"""
        print()
        print("Ecoute en cours... (parlez maintenant)")
        print("Duree: %d secondes" % duration)
        
        try:
            # Demarrer la reconnaissance
            self.asr.subscribe("VoiceConversation")
            
            # Attendre que l'utilisateur parle
            start_time = time.time()
            recognized_text = ""
            
            while time.time() - start_time < duration:
                # Lire les donnees de reconnaissance
                try:
                    word_recognized = self.memory.getData("WordRecognized")
                    if word_recognized and len(word_recognized) > 0:
                        word = word_recognized[0]
                        confidence = word_recognized[1]
                        
                        if confidence > 0.3:  # Seuil de confiance
                            recognized_text = word
                            print("Mot detecte: '%s' (confiance: %.2f)" % (word, confidence))
                            break
                except Exception:
                    pass
                
                time.sleep(0.1)
            
            # Arreter la reconnaissance
            self.asr.unsubscribe("VoiceConversation")
            
            if recognized_text:
                print("Texte reconnu: '%s'" % recognized_text)
                return recognized_text
            else:
                print("Aucun texte reconnu")
                return None
                
        except Exception as e:
            print("X Erreur lors de l'ecoute:", str(e))
            try:
                self.asr.unsubscribe("VoiceConversation")
            except:
                pass
            return None
    
    def get_llm_response(self, user_input):
        """Obtenir une reponse du LLM Groq"""
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
                          "Garde tes reponses courtes (2-3 phrases maximum) car elles seront "
                          "prononcees par un robot."
            }
            
            # Preparer les messages pour l'API
            messages = [system_message] + self.conversation_history
            
            # Appeler l'API Groq
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages,
                model=self.llm_model,
                temperature=0.7,
                max_tokens=150
            )
            
            # Extraire la reponse
            response = chat_completion.choices[0].message.content
            
            # Ajouter la reponse a l'historique
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            print("Reponse du LLM: '%s'" % response)
            return response
            
        except Exception as e:
            print("X Erreur lors de l'appel a Groq:", str(e))
            return "Desole, je n'ai pas pu traiter votre demande."
    
    def speak(self, text):
        """Faire parler le robot"""
        print()
        print("NAO dit: '%s'" % text)
        try:
            self.tts.say(text)
        except Exception as e:
            print("X Erreur lors de la synthese vocale:", str(e))
    
    def conversation_loop(self, num_exchanges=3):
        """Boucle de conversation"""
        print()
        print("-" * 60)
        print("Debut de la conversation (Ctrl+C pour arreter)")
        print("-" * 60)
        print()
        
        self.speak("Bonjour! Je suis pret a discuter avec vous.")
        
        for i in range(num_exchanges):
            print()
            print("=" * 60)
            print("Echange %d/%d" % (i + 1, num_exchanges))
            print("=" * 60)
            
            # Ecouter l'utilisateur
            user_input = self.listen(duration=5)
            
            if not user_input:
                self.speak("Je n'ai pas compris. Pouvez-vous repeter?")
                continue
            
            # Obtenir la reponse du LLM
            response = self.get_llm_response(user_input)
            
            # Faire parler le robot
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
    
    # Initialiser Groq
    if not conversation.initialize_groq():
        print("Impossible d'initialiser Groq LLM")
        sys.exit(1)
    
    print()
    
    # Configurer la reconnaissance vocale
    if not conversation.configure_speech_recognition():
        print("Impossible de configurer la reconnaissance vocale")
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
