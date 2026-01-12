#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de suivi facial pour le robot NAO V3
Utilise la camera embarquee de NAO et le module ALFaceDetection
pour detecter et suivre les visages
"""

import sys
import os
import time

lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, lib_path)

print("=" * 60)
print("   SUIVI FACIAL NAO V3 (Camera embarquee)")
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


class FaceTracker(ALModule):
    """Module pour le suivi facial avec ALFaceDetection"""
    
    def __init__(self, name, nao_ip, nao_port):
        ALModule.__init__(self, name)
        
        self.nao_ip = nao_ip
        self.nao_port = nao_port
        
        # Proxies NAOqi
        self.memory = None
        self.motion = None
        self.tts = None
        self.face_detection = None
        self.tracker = None
        
        # Etat
        self.face_detected = False
        self.tracking_enabled = True
        
    def initialize(self):
        """Initialiser les proxies et modules"""
        print("Initialisation des modules NAOqi...")
        
        try:
            self.memory = ALProxy("ALMemory", self.nao_ip, self.nao_port)
            self.motion = ALProxy("ALMotion", self.nao_ip, self.nao_port)
            self.tts = ALProxy("ALTextToSpeech", self.nao_ip, self.nao_port)
            self.face_detection = ALProxy("ALFaceDetection", self.nao_ip, self.nao_port)
            self.tracker = ALProxy("ALTracker", self.nao_ip, self.nao_port)
            
            print("OK Tous les modules initialises")
            return True
        except Exception as e:
            print("X Erreur d'initialisation:", str(e))
            return False
    
    def configure_face_detection(self):
        """Configurer la detection de visages"""
        print("Configuration de la detection de visages...")
        
        # Configurer les parametres de detection
        # Period: periode de detection en ms (500ms = 2 fois par seconde)
        self.face_detection.setParameter("Period", 500)
        
        # Activer le suivi des visages
        self.face_detection.enableTracking(True)
        
        print("OK Detection configuree")
    
    def start_tracking(self):
        """Demarrer le suivi facial"""
        print("Demarrage du suivi facial...")
        
        # Activer les moteurs de la tete
        self.motion.setStiffnesses("Head", 1.0)
        time.sleep(0.3)
        
        # Position initiale
        self.motion.setAngles("HeadYaw", 0.0, 0.3)
        self.motion.setAngles("HeadPitch", 0.0, 0.3)
        time.sleep(1.0)
        
        # Configurer le tracker pour suivre les visages
        # Mode: "Head" = suivre avec la tete uniquement
        self.tracker.setMode("Head")
        
        # Definir la cible: "Face" pour suivre les visages
        self.tracker.registerTarget("Face", 0.1)
        
        # Demarrer le suivi
        self.tracker.track("Face")
        
        print("OK Suivi demarre")
        print()
        print("-" * 60)
        print("Le robot suit maintenant les visages detectes")
        print("Appuyez sur Ctrl+C pour arreter")
        print("-" * 60)
        print()
    
    def monitor_tracking(self):
        """Surveiller le suivi et afficher les informations"""
        try:
            while self.tracking_enabled:
                # Lire les donnees de detection de visages
                faces = self.memory.getData("FaceDetected")
                
                if faces and len(faces) >= 2:
                    # faces[1] contient la liste des visages detectes
                    face_info_array = faces[1]
                    
                    if len(face_info_array) > 0:
                        if not self.face_detected:
                            print("Visage detecte! Suivi en cours...")
                            self.face_detected = True
                        
                        # Afficher le nombre de visages
                        nb_faces = len(face_info_array)
                        if nb_faces > 1:
                            print("  -> %d visages detectes" % nb_faces)
                else:
                    if self.face_detected:
                        print("Visage perdu... Recherche en cours...")
                        self.face_detected = False
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print()
            print("Interruption clavier")
            self.tracking_enabled = False
    
    def stop_tracking(self):
        """Arreter le suivi"""
        print()
        print("Arret du suivi...")
        
        # Arreter le tracker
        self.tracker.stopTracker()
        self.tracker.unregisterAllTargets()
        
        # Remettre la tete en position initiale
        print("Remise en position initiale...")
        self.motion.setAngles("HeadYaw", 0.0, 0.3)
        self.motion.setAngles("HeadPitch", 0.0, 0.3)
        time.sleep(1.0)
        
        # Desactiver les moteurs
        self.motion.setStiffnesses("Head", 0.0)
        
        print("OK Suivi arrete")


def main():
    """Fonction principale"""
    NAO_IP = "169.254.201.219"
    NAO_PORT = 9559
    
    # Creer un broker pour le module ALModule
    broker = ALBroker("myBroker", "0.0.0.0", 0, NAO_IP, NAO_PORT)
    
    # Creer le tracker
    tracker = FaceTracker("FaceTracker", NAO_IP, NAO_PORT)
    
    # Initialiser
    if not tracker.initialize():
        print("Impossible d'initialiser les modules")
        broker.shutdown()
        sys.exit(1)
    
    print()
    
    # Configurer la langue
    tracker.tts.setLanguage("French")
    tracker.tts.setVolume(0.8)
    
    # Message de bienvenue
    tracker.tts.say("Je vais maintenant suivre votre visage avec ma camera embarquee")
    
    print()
    
    try:
        # Configurer la detection
        tracker.configure_face_detection()
        
        print()
        
        # Demarrer le suivi
        tracker.start_tracking()
        
        # Surveiller le suivi
        tracker.monitor_tracking()
    
    except Exception as e:
        print()
        print("X Erreur:", str(e))
    
    finally:
        # Arreter le suivi
        tracker.stop_tracking()
        
        # Fermer le broker
        broker.shutdown()
        
        print()
        print("-" * 60)
        print("OK Programme termine avec succes!")
        print("=" * 60)


if __name__ == "__main__":
    main()
