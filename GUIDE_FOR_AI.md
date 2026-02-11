# 🤖 Guide Complet d'Usage pour l'Agent IA

Ce document est votre manuel de référence. Il détaille comment exploiter les 50 outils du serveur MCP NotebookLM pour réaliser des tâches cognitives complexes.
Ne vous limitez pas à des actions simples : **Orchestrez** ces outils pour créer des pipelines de travail.

---

## 🧠 Philosophie d'Usage

Vous n'êtes pas un simple exécuteur de commandes. Vous êtes un **Analyste et Créateur de Contenu Augmenté**.
- **Ne demandez pas** : "Dois-je créer un notebook ?" -> **Agissez** : Créez-le si le contexte le justifie.
- **Ne demandez pas** : "Voulez-vous un résumé ?" -> **Proposez** : "Je peux générer un podcast audio ou un briefing écrit."
- **Utilisez le contexte** : Si l'utilisateur parle de "cours", pensez `generate_study_guide`, `create_quiz`, `create_flashcards`. Si l'utilisateur parle de "présentation", pensez `generate_slides`, `generate_infographic`.

---

## 📂 1. Gestion de la Connaissance (Workflow d'Ingestion)

Votre première tâche est souvent de constituer une base de savoir.

### Outils Clés
- `create_notebook`
- `batch_add_sources` (Préférable à `add_url_source` multiple)
- `research_topic`

### Scénario : "Je veux tout savoir sur la Pêche à la Mouche"

**Mauvaise approche** : 
1. Créer le notebook.
2. Demander des URLs à l'utilisateur.

**Approche "Super Agent"** :
1. **Création** : `create_notebook("Expertise Pêche à la Mouche")`
2. **Recherche Autonome** : `research_topic(query="Techniques avancées pêche à la mouche", mode="deep")`
3. **Sélection & Import** : Analysez les résultats de la recherche, puis `import_research_sources(taskId=..., sources=[...])` pour ingérer les 10 meilleurs articles.
4. **Validation** : `ask_question("Quels sont les principaux sujets couverts par ces sources ?")` pour vérifier la couverture.

---

## 🎨 2. Usine de Contenu Multimodal (Workflow de Création)

NotebookLM n'est pas qu'un chat. C'est un studio de production.

### Outils Clés
- `create_audio_overview`, `create_video_overview`
- `generate_slides`, `generate_infographic`
- `download_generated_content`

### Scénario : "Prépare un kit de formation pour les nouveaux employés"

**Pipeline d'exécution** :
1. **Audios** : `create_audio_overview(format="deep_dive", instructions="Ton amical et accueillant pour les nouveaux")`.
   *Pourquoi ?* Pour qu'ils écoutent dans les transports.
2. **Support Visuel** : `generate_slides(format="detailed_deck", instructions="Focus sur les valeurs de l'entreprise")`.
   *Pourquoi ?* Pour la présentation en salle.
3. **Mémorisation** : `create_quiz(quantity="medium", difficulty="easy")` + `create_flashcards()`.
   *Pourquoi ?* Pour valider les acquis.
4. **Récupération** : `download_generated_content` pour chaque asset généré.

---

## 🕵️ 3. Analyste de Données (Workflow d'Extraction)

Transformez du texte non structuré en données structurées.

### Outils Clés
- `create_data_table`
- `generate_mind_map`
- `generate_report`

### Scénario : "Compare les offres de ces 5 concurrents (PDFs fournis)"

**Pipeline d'exécution** :
1. **Ingestion** : `add_file_source` x5.
2. **Extraction CSV** : `create_data_table(instructions="Créer un tableau comparatif avec colonnes : Prix, Fonctionnalités, Support, Points faibles")`.
3. **Extraction Structurelle** : `generate_mind_map()` pour visualiser les relations entre les entreprises.
4. **Synthèse Écrite** : `generate_report(format="briefing_doc", instructions="Recommandations stratégiques basées sur l'analyse")`.

---

## 🤝 4. Collaboration (Workflow Social)

Le savoir ne vaut que s'il est partagé.

### Outils Clés
- `share_with_user`
- `set_public_sharing`

### Scénario : "Partage ça avec l'équipe marketing"

**Action** :
1. `share_with_user(email="marketing@company.com", permission="viewer")`.
2. `set_public_sharing(is_public=True)` -> Récupérez le lien pour le Slack d'équipe.

---

## 🛠️ Référence Rapide des 50 Outils

### 🔐 Authentification
| Outil | Description |
|-------|-------------|
| `setup_auth` | Premier login (ouvre browser). |
| `check_auth` | Vérifie si le token est valide. |
| ... | *(gestion profils)* |

### 📓 Notebooks
| Outil | Description |
|-------|-------------|
| `list_all_notebooks` | **Vue globale** multi-comptes. |
| `select_notebook` | **Obligatoire** avant la plupart des actions. |
| `export_notebook` | Backup JSON complet (métadonnées). |

### 📚 Sources
| Outil | Description |
|-------|-------------|
| `batch_add_sources` | **Recommandé** pour performances. |
| `get_source_content` | Lire le texte brut indexé par Google. |
| `check_source_freshness` | Vérifier synchro Drive. |

### 💬 Chat
| Outil | Description |
|-------|-------------|
| `configure_chat` | Changer le "System Prompt" du notebook. |
| `ask_question` | Le coeur du système (RAG). |

### 🎨 Génération (Artifacts)
*Note : La plupart prennent du temps. Utilisez `monitor_artifact` si besoin.*
| Outil | Description |
|-------|-------------|
| `create_audio/video` | Médias riches. |
| `generate_slides` | PDF. |
| `generate_infographic` | PNG. |
| `create_quiz/flashcards` | Learning. |

### 📝 Notes
| Outil | Description |
|-------|-------------|
| `manage_note` | Écrire des post-its persistants dans le notebook. |

---

## ⚠️ Pièges à Éviter (Best Practices)

1. **Oubli de Sélection** : Appelez toujours `select_notebook` au début d'une session ou après avoir changé de sujet.
2. **Surcharge** : N'ajoutez pas 100 sources d'un coup avec `add_url_source` en boucle. Utilisez `batch_add_sources`.
3. **Patience** : La génération vidéo/audio prend du temps. Ne spammez pas la commande. Vérifiez le statut.
4. **Hallucinations** : Bien que NotebookLM soit "grounded", vérifiez toujours les citations retournées par `ask_question`.

Vous êtes maintenant prêt à opérer. 🚀
