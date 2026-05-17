# Guide Rapide - Configuration Xcode (Version Simplifiée)

## Situation Actuelle
✅ Projet Xcode copié : `/Users/valentin/personal-ai-layer/ios/PersonalAIAgent.xcodeproj`
✅ 19 fichiers Swift prêts dans `/Users/valentin/personal-ai-layer/ios/PersonalAIAgent/`
✅ Export backend prêt : `~/Desktop/PersonalAI-export.db` (32 MB)

---

## Étape 1 : Ouvrir le Projet

### Dans le Terminal :
```bash
open /Users/valentin/personal-ai-layer/ios/PersonalAIAgent.xcodeproj
```

Ou double-cliquez sur le fichier `.xcodeproj` dans Finder.

---

## Étape 2 : Nettoyer les Anciennes Références

Dans Xcode, **Project Navigator** (barre latérale gauche) :

1. Sélectionner **tout** sauf :
   - PersonalAIAgent (le dossier racine bleu)
   - PersonalAIAgentTests

2. **Clic droit** → **Delete** → **Remove References** (PAS "Move to Trash")
   - Cela supprime juste les références, pas les fichiers

Vous devriez avoir une structure vide :
```
PersonalAIAgent/
└── PersonalAIAgentTests/
```

---

## Étape 3 : Ajouter Nos Nouveaux Fichiers

### 3.1 Créer les Groupes (Dossiers)

**Clic droit** sur `PersonalAIAgent` → **New Group** (répéter pour chaque) :

```
PersonalAIAgent/
├── App
├── Core
│   ├── Embeddings
│   ├── Import
│   ├── LLM
│   ├── RAG
│   ├── Security
│   └── Storage
└── Features
    ├── Chat
    └── Settings
```

### 3.2 Ajouter les Fichiers par Groupe

Pour **chaque groupe**, faites glisser les fichiers depuis Finder :

**App/ :**
- Faites glisser depuis Finder : `/Users/valentin/personal-ai-layer/ios/PersonalAIAgent/App/`
  - `AppContainer.swift`
  - `PersonalAIAgentApp.swift`
  - `RootView.swift`
- Quand la fenêtre s'ouvre :
  - ❌ **Décocher** "Copy items if needed"
  - ✅ **Cocher** "PersonalAIAgent" sous "Add to targets"
  - Cliquer **Finish**

**Core/Embeddings/ :**
- `EmbeddingEngine.swift`

**Core/Import/ :**
- `BulkImporter.swift`

**Core/LLM/ :**
- `LLMClient.swift`

**Core/RAG/ :**
- `HybridRAGPipeline.swift`
- `QueryClassifier.swift`

**Core/Security/ :**
- `KeychainManager.swift`

**Core/Storage/ :**
- `GraphStore.swift`
- `VectorStore.swift`

**Features/Chat/ :**
- `ChatViewModel.swift`

**Features/Settings/ :**
- `ImportView.swift`
- `SettingsView.swift`

### 3.3 Ajouter les Tests

**Clic droit** sur `PersonalAIAgentTests` → **Add Files...**

Sélectionner depuis `/Users/valentin/personal-ai-layer/ios/PersonalAIAgent/Tests/` :
- `GraphStoreTests.swift`
- `QueryClassifierTests.swift`
- `RAGPipelineTests.swift`
- `VectorStoreTests.swift`
- `EmbeddingEngineTests.swift`

**Options :**
- ❌ **Décocher** "Copy items if needed"
- ✅ **Cocher** "PersonalAIAgentTests" sous "Add to targets"

---

## Étape 4 : Vérifier le Target

1. Sélectionner **PersonalAIAgent** (icône bleue en haut)
2. **Build Phases** → **Compile Sources**
3. Vérifier que vous voyez **19 fichiers** Swift

Si des fichiers manquent :
- Clic **+** → Ajouter le fichier manquant

---

## Étape 5 : Configurer Info.plist pour Import

1. Sélectionner **PersonalAIAgent** target
2. **Info** tab
3. **Document Types** → Clic **+**

**Type 1 - Database :**
- Name: `Database`
- Types: `public.database`
- Role: `Viewer`

**Type 2 - JSON :**
- Name: `JSON`
- Types: `public.json`
- Role: `Viewer`

---

## Étape 6 : Build

**Command + B** (⌘ + B)

### Si Erreurs de Build :

**Erreur : "Cannot find 'SQLite3'"**

Solution :
1. Sélectionner **PersonalAIAgent** target
2. **General** tab
3. **Frameworks, Libraries, and Embedded Content**
4. Clic **+**
5. Chercher et ajouter : `libsqlite3.tbd`

**Erreur : "Cannot find type in scope"**

Vérifier que tous les fichiers sont dans **Compile Sources** (Étape 4)

**Erreur : Module Swift version**

1. **Build Settings** tab
2. Chercher "Swift Language Version"
3. Mettre : **Swift 5**

---

## Étape 7 : Run

**Command + R** (⌘ + R)

L'app devrait lancer avec :
- ✅ Onglet **Chat** (vide)
- ✅ Onglet **Settings** avec "Import from Mac"

---

## Étape 8 : Tester l'Import

1. Dans le simulateur, aller à **Settings**
2. Taper **"Import from Mac"**
3. Taper **"Select Database File"**
4. Naviguer vers **Desktop**
5. Sélectionner `PersonalAI-export.db`
6. Attendre l'import (5-30 secondes)
7. ✅ Message "Import Complete!"

Retour à **Settings** → Vérifier stats :
- **Total chunks:** devrait être > 0
- **Total entities:** devrait être > 0

---

## Étape 9 : Configurer API Key

**Méthode Temporaire :**

1. Ouvrir `AppContainer.swift`
2. Dans `init()`, **après** la ligne 18, ajouter :

```swift
// TEMPORARY: Set API key
try? KeychainManager.setAPIKey("sk-ant-votre-clé-ici")
```

3. Remplacer `"sk-ant-votre-clé-ici"` par votre vraie clé Anthropic
4. **Build + Run** une fois
5. **Supprimer** ces 2 lignes
6. **Build + Run** à nouveau

---

## Étape 10 : Tester le Chat

Aller à **Chat** tab, essayer :

**Query 1 :**
```
Avec qui je parle le plus ?
```
Réponse attendue : Liste de contacts avec volumes

**Query 2 :**
```
Qu'est-ce qu'on a dit sur le projet ?
```
Réponse attendue : Extraits de messages pertinents

Observer :
- ✅ Réponse **stream** caractère par caractère (pas tout d'un coup)
- ✅ Contexte personnalisé basé sur vos données
- ✅ Pas de numéros de téléphone bruts (remplacés par noms)

---

## Résolution de Problèmes Rapides

### App crash au lancement
- Vérifier que **tous** les fichiers sont en **Compile Sources**
- Vérifier `@MainActor` sur AppContainer et ChatViewModel

### Import ne fonctionne pas
- Vérifier document types dans Info.plist
- Console Xcode (⌘ + Shift + Y) pour voir erreurs

### Chat ne répond pas
- Vérifier API key dans Keychain
- Vérifier connexion internet
- Console pour erreurs LLM

---

## Commandes Rapides Xcode

- **Build:** ⌘ + B
- **Run:** ⌘ + R
- **Stop:** ⌘ + .
- **Clean:** ⌘ + Shift + K
- **Console:** ⌘ + Shift + Y
- **Navigator:** ⌘ + 0

---

## ✅ Checklist Succès

- [ ] Projet s'ouvre dans Xcode
- [ ] 19 fichiers Swift visibles
- [ ] Build sans erreurs
- [ ] App lance dans simulateur
- [ ] Import complète avec succès
- [ ] Stats montrent données importées
- [ ] Chat répond avec contexte
- [ ] LLM stream fonctionne

**Quand tout est ✅ → MVP opérationnel ! 🎉**

---

## Commit Final

Quand tout fonctionne :

```bash
cd /Users/valentin/personal-ai-layer
git add ios/PersonalAIAgent.xcodeproj
git commit -m "feat(ios): add Xcode project configuration for MVP

- Configured iOS app project with SwiftUI
- Added all 19 Swift source files
- Configured document types for file import
- Added SQLite3 framework dependency
- Ready for deployment and testing

Smoke test: Import and chat both functional ✅

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push origin main
```

---

**C'est parti ! 🚀**
