#!/usr/bin/env python3
"""
MCP Server: services-agent
Serveur MCP pour les outils de santé et services administratifs

Compatible avec Azure Voice Live API (MCP natif)

Outils:
- get_health_advice: Conseils santé et symptômes
- search_exercises: Recherche d'exercices fitness
- find_pharmacy: Pharmacies de garde
- get_government_service_info: Démarches administratives
- create_cv: Génération de CV (contextuel)

Auteur: WakaCore Team
Date: 2026-01-30
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, Response, request, jsonify
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# MCP SERVER BASE
# =============================================================================

class MCPServer:
    def __init__(self, name: str, description: str, version: str = "2.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.tools = {}
        self.app = Flask(__name__)
        self._setup_routes()
    
    def tool(self, name: str, description: str, parameters: dict):
        """Décorateur pour enregistrer un outil MCP"""
        def decorator(func):
            self.tools[name] = {
                "name": name,
                "description": description,
                "inputSchema": {
                    "type": "object",
                    "properties": parameters.get("properties", {}),
                    "required": parameters.get("required", [])
                },
                "handler": func
            }
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _setup_routes(self):
        @self.app.route("/mcp", methods=["POST"])
        def mcp_endpoint():
            return self._handle_mcp_request()
        
        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify({
                "status": "ok",
                "server": self.name,
                "version": self.version,
                "tools_count": len(self.tools)
            })
        
        @self.app.route("/tools", methods=["GET"])
        def list_tools():
            tools_list = [{"name": t["name"], "description": t["description"]} for t in self.tools.values()]
            return jsonify({"tools": tools_list, "count": len(tools_list)})
        
        @self.app.route("/", methods=["GET"])
        def index():
            return jsonify({
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "endpoints": {
                    "mcp": "/mcp (POST)",
                    "health": "/health",
                    "tools": "/tools"
                },
                "tools_count": len(self.tools)
            })
    
    def _handle_mcp_request(self):
        data = request.get_json()
        if not data:
            return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), 400
        
        request_id = data.get("id")
        method = data.get("method", "")
        params = data.get("params", {})
        
        if method == "initialize":
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": self.name, "version": self.version},
                    "capabilities": {"tools": {"listChanged": False}}
                }
            })
        
        elif method == "tools/list":
            tools_list = [{
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"]
            } for t in self.tools.values()]
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_list}
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                })
            
            try:
                result = self.tools[tool_name]["handler"](**arguments)
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]
                    }
                })
            except Exception as e:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(e)}
                })
        
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })
    
    def run(self, host="0.0.0.0", port=8000):
        self.app.run(host=host, port=port, threaded=True)


# =============================================================================
# CRÉATION DU SERVEUR
# =============================================================================

server = MCPServer(
    name="services-agent",
    description="Agent de services - Santé, exercices, pharmacies, démarches administratives et CV",
    version="2.0.0"
)

# Import des modules tools
from tools import tool_health_advice, tool_exercises
from tools import tool_pharmacy_locator, tool_government_services
from tools import tool_cv


# =============================================================================
# SANTÉ
# =============================================================================

@server.tool(
    name="get_health_advice",
    description="""Analyse des symptômes et conseils santé, remèdes et recommandations.

SYMPTÔMES SUPPORTÉS:
- Maux de tête, fièvre, toux
- Ballonnement, douleur abdominale
- Fatigue, insomnie
- Douleurs musculaires

⚠️ AVERTISSEMENT: Conseils généraux uniquement. Consulter un médecin pour tout problème sérieux.""",
    parameters={
        "properties": {
            "symptoms": {"type": "string", "description": "Description des symptômes ressentis"},
            "age": {"type": "integer", "description": "Âge de la personne (pour conseils adaptés)"},
            "sex": {"type": "string", "description": "Sexe ('male' ou 'female')"}
        },
        "required": ["symptoms"]
    }
)
def get_health_advice(symptoms: str, age: int = 30, sex: str = "male"):
    return tool_health_advice.get_health_advice(symptoms=symptoms, age=age, sex=sex)


# =============================================================================
# EXERCICES FITNESS
# =============================================================================

@server.tool(
    name="search_exercises",
    description="""Recherche d'exercices de fitness avec filtres.

MUSCLES: biceps, triceps, chest, back, legs, abdominals, calves, glutes
TYPES: cardio, strength, stretching, plyometrics
NIVEAUX: beginner, intermediate, expert

EXEMPLES: muscle="biceps", difficulty="beginner" """,
    parameters={
        "properties": {
            "muscle": {"type": "string", "description": "Muscle ciblé (biceps, chest, legs, etc.)"},
            "type": {"type": "string", "description": "Type d'exercice (cardio, strength, stretching)"},
            "difficulty": {"type": "string", "description": "Niveau (beginner, intermediate, expert)"},
            "name": {"type": "string", "description": "Nom d'exercice (recherche partielle)"},
            "max_results": {"type": "integer", "description": "Nombre maximum de résultats (1-30)"}
        },
        "required": []
    }
)
def search_exercises(muscle: str = None, type: str = None, difficulty: str = None, name: str = None, max_results: int = 10):
    return tool_exercises.search_exercises(muscle=muscle, type=type, difficulty=difficulty, name=name, max_results=max_results)


# =============================================================================
# PHARMACIES DE GARDE
# =============================================================================

@server.tool(
    name="find_pharmacy",
    description="""Trouve les pharmacies de garde (24h/24) et numéros d'urgence au Burkina Faso.

VILLES SUPPORTÉES: Ouagadougou, Bobo-Dioulasso, Koudougou, Ouahigouya, Banfora

NUMÉROS D'URGENCE: Police: 17, Pompiers: 18, SAMU: 112""",
    parameters={
        "properties": {
            "city": {"type": "string", "description": "Ville du Burkina (défaut: Ouagadougou)"},
            "emergency": {"type": "boolean", "description": "Si true, inclut aussi les numéros d'urgence"}
        },
        "required": []
    }
)
def find_pharmacy(city: str = "Ouagadougou", emergency: bool = False):
    return tool_pharmacy_locator.execute({"city": city, "emergency": emergency})


# =============================================================================
# SERVICES GOUVERNEMENTAUX
# =============================================================================

@server.tool(
    name="get_government_service_info",
    description="""Informations sur les démarches administratives au Burkina Faso.

SERVICES DISPONIBLES:
- Passeport
- Carte d'identité nationale (CNIB)
- Permis de conduire
- Acte de naissance
- Certificat de nationalité
- Casier judiciaire

Retourne documents requis, procédure, coûts et délais.""",
    parameters={
        "properties": {
            "service_name": {"type": "string", "description": "Nom du service (ex: 'Passeport', 'CNIB', 'Permis')"}
        },
        "required": ["service_name"]
    }
)
def get_government_service_info(service_name: str):
    return tool_government_services.execute({"service_name": service_name})


# =============================================================================
# GÉNÉRATION DE CV
# =============================================================================

@server.tool(
    name="create_cv",
    description="""Génère un CV professionnel Word à partir de la conversation Voice Live.

⚠️ IMPORTANT: Cet outil nécessite que les informations aient été collectées pendant la conversation:
- Nom complet, Email et téléphone
- Expériences professionnelles
- Formations et Compétences

Le CV est généré depuis l'historique de conversation et envoyé par email.""",
    parameters={
        "properties": {
            "call_id": {"type": "string", "description": "ID de l'appel Voice Live en cours (fourni automatiquement)"},
            "email": {"type": "string", "description": "Adresse email pour envoyer le CV"},
            "style": {"type": "string", "description": "Style visuel (classique, moderne, minimaliste)"},
            "color": {"type": "string", "description": "Couleur principale (bleu, vert, gris, rouge)"}
        },
        "required": ["call_id", "email"]
    }
)
def create_cv(call_id: str, email: str, style: str = "moderne", color: str = "bleu"):
    return tool_cv.create_cv(call_id=call_id, email=email, style=style, color=color)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    print("🏥 Démarrage du serveur MCP services-agent v2.0.0...")
    server.run(host="0.0.0.0", port=8000)
