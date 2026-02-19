# Agent de Scraping BTP avec Agno

## 🎯 Qu'est-ce qu'Agno ?

**Agno** (anciennement Phidata) est un framework Python pour créer des **agents IA autonomes** avec :
- 🧠 **Raisonnement** : L'agent décide quels outils utiliser
- 🛠️ **Outils** : WebsiteTools, FileTools, API calls, etc.
- 🔄 **Itération** : L'agent peut réessayer si ça échoue
- 📝 **Mémoire** : Garde le contexte des actions précédentes

## 🆚 Différence avec Selenium/BeautifulSoup

| Méthode | Comment ça marche | Avantages | Inconvénients |
|---------|-------------------|-----------|---------------|
| **Selenium** | Navigate → Find element → Extract | Contrôle précis | Code rigide, casse si HTML change |
| **BeautifulSoup** | Parse HTML → Query DOM | Simple, rapide | Pas de JS, selectors codés en dur |
| **Agno Agent** | AI décide comment extraire | S'adapte aux changements | Coût API, plus lent |

## 🏗️ Architecture du script `scrape_agno_agent.py`

```
┌─────────────────────────────────────┐
│  BTPScraperAgent                    │
├─────────────────────────────────────┤
│  1. Agent Agno avec WebsiteTools    │
│     ↓                                │
│  2. Prompt: "Extrait les PDFs"      │
│     ↓                                │
│  3. Agent navigue + analyse         │
│     ↓                                │
│  4. Retourne JSON structuré         │
│     ↓                                │
│  5. Téléchargement des PDFs         │
└─────────────────────────────────────┘
```

## 🔧 Comment ça fonctionne

### 1. **Initialisation de l'agent**
```python
self.agent = Agent(
    name="BTP Web Scraper",
    model=OpenAIChat(id="gpt-4o-mini"),  # Modèle LLM
    tools=[WebsiteTools()],               # Outils de navigation web
    instructions=[...]                    # Rôle et règles
)
```

### 2. **L'agent reçoit un prompt**
```python
prompt = """Analyse cette page et extrait les PDFs.
URL: https://www.btp-cours.com/...
Retourne un JSON: {"articles": [{"title": "...", "pdf_url": "..."}]}
"""
response = self.agent.run(prompt)
```

### 3. **L'agent agit de manière autonome**
L'agent utilise automatiquement `WebsiteTools` pour :
- Faire un GET HTTP de la page
- Lire le HTML
- Analyser les liens `<a href="*.pdf">`
- Extraire les titres et URLs
- Structurer en JSON

### 4. **Résultat structuré**
```json
{
  "articles": [
    {"title": "Guide isolation thermique", "pdf_url": "https://...pdf"},
    {"title": "Normes DTU 2024", "pdf_url": "https://...pdf"}
  ]
}
```

## 📦 Installation

```bash
# Active l'environnement virtuel
agno-env\Scripts\activate

# Installe Agno
pip install agno openai requests

# Configure la clé API
$env:OPENAI_API_KEY = "sk-..."
```

## 🚀 Utilisation

```bash
# Lance le scraping (limite à 5 PDFs pour test)
python scrapping/scrape_agno_agent.py
```

## 🎓 Pourquoi utiliser Agno pour le scraping ?

### ✅ **Avantages**
1. **Robustesse** : Si le HTML change, l'IA s'adapte
2. **Multi-sites** : Même agent pour différents sites
3. **Intelligent** : Comprend le contexte (ignore pub, navbars)
4. **Moins de code** : Pas besoin de sélecteurs CSS complexes

### ⚠️ **Inconvénients**
1. **Coût** : Appels API OpenAI (~$0.001/requête)
2. **Lenteur** : 2-5s par page vs <1s pour Selenium
3. **Dépendance** : Nécessite une connexion API

## 🔄 Comparaison des agents dans votre projet

Votre projet a déjà **3 agents "classiques"** :

| Agent | Type | Framework | Rôle |
|-------|------|-----------|------|
| `KnowledgeRetrieverAgent` | RAG | LLM custom | Génère queries + retrieval |
| `KnowledgeEnhancerAgent` | RAG | LLM custom | Améliore les résultats |
| `CourseGeneratorAgent` | RAG | LLM custom | Crée cours structurés |
| **`BTPScraperAgent`** | **Scraping** | **Agno** | **Extrait PDFs du web** |

## 💡 Cas d'usage idéaux pour Agno

- ✅ Sites avec structure variable
- ✅ Scraping exploratoire ("trouve des ressources sur X")
- ✅ Extraction sémantique complexe
- ❌ Scraping haute fréquence (trop cher)
- ❌ Sites avec anti-bot strict

## 📚 Ressources

- [Agno Docs](https://docs.agno.dev)
- [Agent Patterns](https://docs.agno.dev/agents/introduction)
- [WebsiteTools API](https://docs.agno.dev/tools/website)
