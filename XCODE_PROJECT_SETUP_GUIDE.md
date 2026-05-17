# Xcode Project Setup Guide - Personal AI iOS MVP

## Overview
This guide will walk you through creating the Xcode project for the Personal AI iOS app and adding all 19 Swift source files we've implemented.

**Estimated Time:** 15-30 minutes
**Prerequisites:** Xcode installed (15.0+)

---

## Step 1: Create New Xcode Project

### 1.1 Open Xcode
- Launch Xcode application
- Select **"Create New Project"** (or File → New → Project)

### 1.2 Choose Template
- Select **iOS** tab at the top
- Choose **"App"** template
- Click **Next**

### 1.3 Configure Project Settings

**Fill in the following:**

| Field | Value |
|-------|-------|
| Product Name | `PersonalAIAgent` |
| Team | Select your Apple Developer account |
| Organization Identifier | `com.yourdomain` (or your preferred reverse domain) |
| Bundle Identifier | (auto-populated: `com.yourdomain.PersonalAIAgent`) |
| Interface | **SwiftUI** |
| Language | **Swift** |
| Storage | **None** (we're using SQLite manually) |
| Include Tests | ✅ **Checked** |

Click **Next**

### 1.4 Choose Location

**IMPORTANT:** Save to `/Users/valentin/personal-ai-layer/ios/`

- Navigate to `/Users/valentin/personal-ai-layer/ios/`
- Make sure **"Create Git repository"** is **UNCHECKED** (we already have one)
- Click **Create**

This will create `/Users/valentin/personal-ai-layer/ios/PersonalAIAgent.xcodeproj`

---

## Step 2: Configure Project Settings

### 2.1 General Settings

1. Select the **PersonalAIAgent** project in the navigator (blue icon)
2. Select the **PersonalAIAgent** target
3. Go to **General** tab

**Configure:**
- **Display Name:** `Personal AI Agent`
- **Minimum Deployments:** iOS **17.0** (or later)
- **Supported Destinations:** iPhone only (uncheck iPad if selected)

### 2.2 Signing & Capabilities

1. Go to **Signing & Capabilities** tab
2. **Automatically manage signing:** ✅ Checked
3. **Team:** Select your Apple Developer account

**Add Capability: Keychain Sharing**
- Click **"+ Capability"** button
- Search for **"Keychain Sharing"**
- Add it
- Keep default keychain group

---

## Step 3: Delete Xcode-Generated Files

Xcode created default files we don't need. Delete these:

1. In the **Project Navigator** (left sidebar), find:
   - `ContentView.swift` (if it exists)
   - `PersonalAIAgentApp.swift` (Xcode's default - we have our own)

2. **Right-click** each file → **Delete** → **Move to Trash**

---

## Step 4: Add Our Swift Files

### 4.1 Create Group Structure

In Project Navigator, create this folder structure (Right-click on `PersonalAIAgent` → **New Group**):

```
PersonalAIAgent/
├── App/
├── Core/
│   ├── Embeddings/
│   ├── Import/
│   ├── LLM/
│   ├── RAG/
│   ├── Security/
│   └── Storage/
├── Features/
│   ├── Chat/
│   └── Settings/
└── Tests/
```

### 4.2 Add Files to Each Group

For each group, **drag and drop** the corresponding files from Finder:

**App/ Group:**
1. Right-click **App** group → **Add Files to "PersonalAIAgent"...**
2. Navigate to `/Users/valentin/personal-ai-layer/ios/PersonalAIAgent/App/`
3. Select:
   - `AppContainer.swift`
   - `PersonalAIAgentApp.swift`
   - `RootView.swift`
4. **Options:**
   - ✅ **Copy items if needed:** UNCHECKED (files already in place)
   - ✅ **Create groups:** Selected
   - ✅ **Add to targets:** PersonalAIAgent checked
5. Click **Add**

**Core/Embeddings/ Group:**
- Add: `EmbeddingEngine.swift`

**Core/Import/ Group:**
- Add: `BulkImporter.swift`

**Core/LLM/ Group:**
- Add: `LLMClient.swift`

**Core/RAG/ Group:**
- Add: `HybridRAGPipeline.swift`
- Add: `QueryClassifier.swift`

**Core/Security/ Group:**
- Add: `KeychainManager.swift`

**Core/Storage/ Group:**
- Add: `GraphStore.swift`
- Add: `VectorStore.swift`

**Features/Chat/ Group:**
- Add: `ChatViewModel.swift`

**Features/Settings/ Group:**
- Add: `ImportView.swift`
- Add: `SettingsView.swift`

**Tests/ Group (in PersonalAIAgentTests target):**
1. Right-click **PersonalAIAgentTests** group
2. Add Files:
   - `GraphStoreTests.swift`
   - `QueryClassifierTests.swift`
   - `RAGPipelineTests.swift`
   - `VectorStoreTests.swift`
   - `EmbeddingEngineTests.swift`
3. **Add to targets:** PersonalAIAgentTests checked

### 4.3 Verify All Files Added

Check Project Navigator shows all 19 files:
```
PersonalAIAgent (19 files)
├── App (3 files)
├── Core (9 files)
│   ├── Embeddings (1)
│   ├── Import (1)
│   ├── LLM (1)
│   ├── RAG (2)
│   ├── Security (1)
│   └── Storage (2)
└── Features (3 files)
    ├── Chat (1)
    └── Settings (2)

PersonalAIAgentTests (5 files)
```

---

## Step 5: Configure Info.plist

### 5.1 Add Document Types for File Picker

1. Select **PersonalAIAgent** project → **PersonalAIAgent** target
2. Go to **Info** tab
3. Expand **"Document Types"** section
4. Click **"+"** to add a new document type

**Document Type 1: SQLite Database**
- **Name:** `SQLite Database`
- **Types:** Click **"+"** under "Types"
  - Add: `public.database`
- **Role:** `Viewer`

**Document Type 2: JSON File**
- Click **"+"** for another document type
- **Name:** `JSON File`
- **Types:** Click **"+"** under "Types"
  - Add: `public.json`
- **Role:** `Viewer`

### 5.2 Add Supported Document Types

In **Info** tab:
1. Find **"Imported Type Identifiers"**
2. Click **"+"** to add
3. **Identifier:** `public.database`
4. **Conforms To:** `public.data`

---

## Step 6: Configure Build Settings

### 6.1 Swift Language Version

1. Select **PersonalAIAgent** project
2. **Build Settings** tab
3. Search for **"Swift Language Version"**
4. Set to: **Swift 5** (or **Swift 6** if using Xcode 16+)

### 6.2 Enable Swift Concurrency

1. Search for **"Swift Compiler - Custom Flags"**
2. Under **"Other Swift Flags"**
3. Add: `-enable-actor-data-race-checks` (for debugging, optional)

---

## Step 7: Fix Common Build Issues

### 7.1 Add Missing Imports

Some files might need these at the top:

**AppContainer.swift:**
```swift
import Foundation
import SwiftUI
```

**All files should have:**
- Files using SQLite: `import SQLite3`
- Files using SwiftUI: `import SwiftUI`
- Files using Foundation types: `import Foundation`

### 7.2 Module Availability

If you see `@available` errors, add this to affected files:
```swift
@available(iOS 17.0, *)
```

---

## Step 8: First Build

### 8.1 Select Simulator

1. Click on **scheme selector** (top left, next to Play button)
2. Select **PersonalAIAgent** scheme
3. Choose destination: **iPhone 15** (or any simulator)

### 8.2 Build

1. Press **⌘ + B** (Command + B) to build
2. Watch for errors in the **Issue Navigator** (⚠️ icon in left sidebar)

### 8.3 Common Build Errors & Fixes

**Error: "Cannot find type 'SearchResult' in scope"**
- Solution: SearchResult is defined in VectorStore.swift, make sure it's added to target

**Error: "Cannot find type 'RelationType' in scope"**
- Solution: RelationType is defined in GraphStore.swift as an enum

**Error: "Use of undeclared type 'RAGContext'"**
- Solution: RAGContext is defined in HybridRAGPipeline.swift, ensure file is in target

**Error: "Module compiled with Swift X.X.X cannot be imported"**
- Solution: Clean build folder (⌘ + Shift + K), then rebuild

**Error: SQLite3 not found**
- Solution: Add `libsqlite3.tbd` to Frameworks
  1. Select target → **General** tab
  2. **Frameworks, Libraries, and Embedded Content**
  3. Click **"+"** → Add **libsqlite3.tbd**

---

## Step 9: Run on Simulator

### 9.1 Launch

1. Press **⌘ + R** (Command + R) to build and run
2. Wait for simulator to boot
3. App should launch with RootView showing tabs

### 9.2 Verify Launch

You should see:
- **Chat tab** with empty conversation
- **Settings tab** with "Import from Mac" option
- **Stats showing:** Total chunks: 0, Total entities: 0

---

## Step 10: Import Test Data

### 10.1 Prepare Files

Make sure these exist on your Desktop:
```
~/Desktop/PersonalAI-export.db (32 MB)
~/Desktop/entities.json (2 B)
~/Desktop/relations.json (17 MB)
```

### 10.2 In Simulator

1. Open **Personal AI Agent** app in simulator
2. Go to **Settings** tab
3. Tap **"Import from Mac"**
4. Tap **"Select Database File"**
5. In file picker:
   - Navigate to **Desktop** (may need to enable "Show Hidden Folders")
   - Select `PersonalAI-export.db`
   - Tap **Open**

### 10.3 Wait for Import

- Progress indicator should appear
- Import may take 5-30 seconds depending on data size
- Success message should appear: **"Import Complete!"**

### 10.4 Verify Import

1. Go back to **Settings**
2. Check stats updated:
   - **Total chunks:** Should be > 0 (thousands)
   - **Total entities:** Should match imported count

---

## Step 11: Test Chat with RAG

### 11.1 Add API Key

**First time only:**
1. We need to set the Anthropic API key in Keychain
2. In Xcode, add temporary code to `AppContainer.swift` init:

```swift
init() {
    // Temporary: Set API key on first launch
    try? KeychainManager.setAPIKey("your-anthropic-api-key-here")

    // ... rest of init
}
```

3. Replace `"your-anthropic-api-key-here"` with your actual key
4. Rebuild and run **once**
5. Then **remove** this code and rebuild again

### 11.2 Test Queries

Go to **Chat** tab and try:

**Query 1: Frequency (Graph-based)**
```
Avec qui je parle le plus ?
```

Expected response should include contact names ranked by volume.

**Query 2: Vector Search**
```
Qu'est-ce qu'on a dit sur le projet ?
```

Expected response should include relevant message excerpts.

**Query 3: Calendar** (if calendar data exists)
```
Qu'est-ce que j'ai cette semaine ?
```

### 11.3 Observe Streaming

- LLM response should **stream** character-by-character
- Not all-at-once after waiting
- This confirms SSE streaming works

---

## Troubleshooting

### App Crashes on Launch

**Check:**
1. All 19 files added to target (Build Phases → Compile Sources)
2. @MainActor on AppContainer and ChatViewModel
3. No force unwraps failing (check EmbeddingEngine init)

**Debug:**
```
⌘ + \ (Command + backslash) to set breakpoint
⌘ + Y to toggle breakpoints on/off
```

### Import Fails

**Check:**
1. File picker shows .db files (document types configured)
2. BulkImporter can access files (no sandboxing issues)
3. Check console for error messages

**Debug in Xcode Console:**
```
Look for error messages from BulkImporter or ImportViewModel
```

### LLM Streaming Doesn't Work

**Check:**
1. API key set correctly in Keychain
2. Internet connection active
3. Anthropic API not rate-limited

**Debug:**
```swift
// Add to LLMClient.stream() method
print("API Key exists: \(apiKey != nil)")
print("HTTP Status: \(httpResponse.statusCode)")
```

### Import Shows Empty Stats

**Possible causes:**
1. Database file corrupt
2. SQLite version mismatch
3. Wrong file selected

**Verify:**
```bash
# On Mac terminal
sqlite3 ~/Desktop/PersonalAI-export.db "SELECT COUNT(*) FROM chunks;"
```

Should return count > 0

---

## Next Steps After Setup

Once the app builds and runs successfully:

1. **Complete Smoke Test**
   - Import your data
   - Test all query types
   - Measure performance
   - Document results

2. **Commit Project File**
```bash
cd /Users/valentin/personal-ai-layer
git add ios/PersonalAIAgent.xcodeproj
git add ios/PersonalAIAgent/Info.plist
git commit -m "feat(ios): add Xcode project configuration

- Create iOS App project with SwiftUI
- Add all 19 Swift source files to target
- Configure document types for .db and .json import
- Enable Keychain Sharing capability
- Set iOS 17.0 minimum deployment target

Ready for build and smoke testing.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push origin main
```

3. **Run Full Smoke Test**
   - Follow SMOKE_TEST_RESULTS.md
   - Complete Steps 3-7
   - Update results document

---

## Quick Reference

**Build:** ⌘ + B
**Run:** ⌘ + R
**Clean:** ⌘ + Shift + K
**Stop:** ⌘ + .
**Show Console:** ⌘ + Shift + Y
**Navigate to file:** ⌘ + Shift + O

**Simulator Controls:**
- **Home:** ⌘ + Shift + H
- **Lock:** ⌘ + L
- **Rotate:** ⌘ + Left/Right Arrow
- **Screenshot:** ⌘ + S

---

## Success Criteria

✅ Xcode project created
✅ All 19 Swift files in target
✅ App builds without errors
✅ App launches in simulator
✅ Import UI accessible
✅ Data import completes
✅ Chat interface responds
✅ LLM streaming works

**When all checked, MVP is fully operational! 🎉**
