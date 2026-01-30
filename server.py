#!/usr/bin/env python3
"""
MCP Server: services-agent
Serveur MCP pour les outils de santé et services administratifs

Outils:
- get_health_advice: Conseils santé et symptômes
- search_exercises: Recherche d'exercices fitness
- find_pharmacy: Pharmacies de garde
- get_government_service_info: Démarches administratives
- create_cv: Génération de CV (contextuel)

Auteur: WakaCore Team
Date: 2026-01-29
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le chemin parent pour importer les tools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP

# Import des modules tools
from tools import tool_health_advice, tool_exercises
from tools import tool_pharmacy_locator, tool_government_services
from tools import tool_cv

# Créer le serveur MCP
mcp = FastMCP(
    "services-agent",
    instructions="Agent de services - Santé, exercices, pharmacies, démarches administratives et CV",
    host="0.0.0.0",
    port=8000
)


# =============================================================================
# SANTÉ
# =============================================================================

@mcp.tool()
def get_health_advice(
    symptoms: str,
    age: int = 30,
    sex: str = "male"
) -> dict:
    """
    Analyse des symptômes et conseils santé, remèdes et recommandations.

    SYMPTÔMES SUPPORTÉS:
    - Maux de tête, fièvre, toux
    - Ballonnement, douleur abdominale
    - Fatigue, insomnie
    - Douleurs musculaires

    ⚠️ AVERTISSEMENT: Conseils généraux uniquement. Consulter un médecin pour tout problème sérieux.

    Args:
        symptoms: Description des symptômes ressentis (OBLIGATOIRE, minimum 3 caractères). Exemples: "mal de tête", "fièvre depuis 2 jours", "toux sèche"
        age: Âge de la personne (pour conseils adaptés)
        sex: Sexe ("male" ou "female")

    Returns:
        dict: Conseils santé, remèdes naturels et indication de consultation
    """
    # Validation: symptoms obligatoire et non vide
    if not symptoms or len(symptoms.strip()) < 3:
        return {
            "status": "error",
            "message": "Veuillez décrire vos symptômes (minimum 3 caractères). Exemple: 'mal de tête', 'fièvre'"
        }

    return tool_health_advice.get_health_advice(
        symptoms=symptoms,
        age=age,
        sex=sex
    )


# =============================================================================
# EXERCICES FITNESS
# =============================================================================

@mcp.tool()
def search_exercises(
    muscle: str = None,
    type: str = None,
    difficulty: str = None,
    name: str = None,
    max_results: int = 10
) -> dict:
    """
    Recherche d'exercices de fitness avec filtres.
    
    MUSCLES: biceps, triceps, chest, back, legs, abdominals, calves, glutes
    TYPES: cardio, strength, stretching, plyometrics
    NIVEAUX: beginner, intermediate, expert
    
    EXEMPLES:
    - muscle="biceps", difficulty="beginner"
    - type="cardio"
    - name="push" (pour push-ups)
    
    Args:
        muscle: Muscle ciblé (biceps, chest, legs, etc.)
        type: Type d'exercice (cardio, strength, stretching)
        difficulty: Niveau (beginner, intermediate, expert)
        name: Nom d'exercice (recherche partielle)
        max_results: Nombre maximum de résultats (1-30)
    
    Returns:
        dict: Liste d'exercices avec instructions et équipement
    """
    return tool_exercises.search_exercises(
        muscle=muscle,
        type=type,
        difficulty=difficulty,
        name=name,
        max_results=max_results
    )


# =============================================================================
# PHARMACIES DE GARDE
# =============================================================================

@mcp.tool()
def find_pharmacy(
    city: str = "Ouagadougou",
    emergency: bool = False
) -> dict:
    """
    Trouve les pharmacies de garde (24h/24) et numéros d'urgence au Burkina Faso.
    
    VILLES SUPPORTÉES:
    - Ouagadougou
    - Bobo-Dioulasso
    - Koudougou
    - Ouahigouya
    - Banfora
    - Fada N'Gourma
    
    NUMÉROS D'URGENCE:
    - Police: 17
    - Pompiers: 18
    - SAMU: 112
    
    Args:
        city: Ville du Burkina (défaut: Ouagadougou)
        emergency: Si true, inclut aussi les numéros d'urgence
    
    Returns:
        dict: Liste des pharmacies avec adresses et téléphones
    """
    return tool_pharmacy_locator.execute({
        "city": city,
        "emergency": emergency
    })


# =============================================================================
# SERVICES GOUVERNEMENTAUX
# =============================================================================

@mcp.tool()
def get_government_service_info(
    service_name: str
) -> dict:
    """
    Informations sur les démarches administratives au Burkina Faso.

    SERVICES DISPONIBLES:
    - Passeport
    - Carte d'identité nationale (CNIB)
    - Permis de conduire
    - Acte de naissance
    - Certificat de nationalité
    - Casier judiciaire
    - Carte grise
    - Visa

    INFORMATIONS FOURNIES:
    - Documents requis
    - Procédure étape par étape
    - Coûts et délais
    - Adresses et contacts

    Args:
        service_name: Nom du service OBLIGATOIRE. Valeurs acceptées: "Passeport", "CNIB", "Permis de conduire", "Acte de naissance", "Certificat de nationalité", "Casier judiciaire", "Carte grise", "Visa"

    Returns:
        dict: Procédure complète avec documents, coûts et délais
    """
    # Validation: service_name obligatoire
    if not service_name or len(service_name.strip()) < 2:
        return {
            "status": "error",
            "message": "Veuillez préciser le service recherché. Services disponibles: Passeport, CNIB, Permis de conduire, Acte de naissance, Certificat de nationalité, Casier judiciaire, Carte grise, Visa"
        }

    return tool_government_services.execute({
        "service_name": service_name
    })


# =============================================================================
# GÉNÉRATION DE CV
# =============================================================================

@mcp.tool()
def create_cv(
    call_id: str,
    email: str,
    style: str = "moderne",
    color: str = "bleu"
) -> dict:
    """
    Génère un CV professionnel Word à partir de la conversation Voice Live.
    
    ⚠️ IMPORTANT: Cet outil nécessite que les informations aient été collectées pendant la conversation:
    - Nom complet
    - Email et téléphone
    - Expériences professionnelles
    - Formations
    - Compétences
    
    Le CV est généré depuis l'historique de conversation stocké dans Cosmos DB.
    
    Args:
        call_id: ID de l'appel Voice Live en cours (fourni automatiquement)
        email: Adresse email pour envoyer le CV
        style: Style visuel (classique, moderne, minimaliste)
        color: Couleur principale (bleu, vert, gris, rouge)
    
    Returns:
        dict: Confirmation d'envoi du CV par email
    """
    return tool_cv.create_cv(
        call_id=call_id,
        email=email,
        style=style,
        color=color
    )


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    print("🏥 Démarrage du serveur MCP services-agent...")
    # Mode HTTP/SSE pour Container Apps
    mcp.run(transport="sse")
