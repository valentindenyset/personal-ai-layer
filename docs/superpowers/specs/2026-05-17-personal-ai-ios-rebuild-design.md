# Personal AI Agent iOS — Design Specification v1.0

**Date:** 2026-05-17
**Status:** Approved for implementation
**Author:** Claude (with Valentin)

---

## Executive Summary

Rebuild of the Personal AI Agent iOS application with a hybrid architecture that combines high-quality backend processing (Python) with real-time on-device capabilities (Swift/iOS). The goal is to achieve superior RAG (Retrieval-Augmented Generation) quality through genuine vector embeddings and graph-based entity linking, while maintaining offline operation and real-time data ingestion.

**Core principle:** Backend Python generates high-quality embeddings and graph structure once (bulk import), then iOS app handles real-time ingestion with on-device embeddings and incremental graph updates.

---

## Problem Statement

The current iOS app (`personal-ai-agent-ios`) suffers from poor retrieval quality because it uses basic SQL LIKE searches instead of semantic vector search. The existing Python backend (`personal-ai-layer`) demonstrates much better results using:
- Real embeddings (sentence-transformers)
- Graph store with entity linking (Neo4j)
- Hybrid retrieval with RRF fusion and reranking

**User requirements:**
- Real-time ingestion for iMessage, Contacts, Calendar
- Offline-capable (no cloud dependency)
- Low cost (no server fees initially)
- Secure (data stays on-device)
- Scalable (can evolve to cloud architecture later)

---

## Architecture Overview

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    MAC (Bulk Ingestion)                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  personal-ai-layer (Python Backend)                           │
│  ├── Ingestion: Messages, Contacts, Calendar, Email, etc.    │
│  ├── Embeddings: sentence-transformers (high quality)        │
│  ├── Entity Extraction: spaCy NER (fr_core_news_lg)          │
│  ├── Storage: Qdrant (vectors) + Neo4j (graph)               │
│  │                                                             │
│  └── Export Engine (NEW)                                      │
│      ├── SQLite export (chunks + embeddings + metadata)       │
│      └── Graph JSON export (entities + relations)             │
│                                                               │
│                          ↓ Transfer                           │
│              (AirDrop, iCloud Drive, or HTTP local)           │
│                          ↓                                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                 iPhone (Real-time + Offline)                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  PersonalAIAgent (SwiftUI)                                    │
│                                                               │
│  ├── Import Engine (ONE-TIME)                                 │
│  │   └── Merge bulk export (historical data)                 │
│  │                                                             │
│  ├── Real-time Monitors                                       │
│  │   ├── iMessage (notification interception)                │
│  │   ├── Contacts (CNContactStore observer)                  │
│  │   ├── Calendar (EventKit observer)                        │
│  │   └── WhatsApp (manual periodic export)                   │
│  │                                                             │
│  ├── Embedding Engine (CoreML on-device)                      │
│  │   ├── Model: all-MiniLM-L6-v2 (22MB, 384D)                │
│  │   └── Generate embeddings for new data                    │
│  │                                                             │
│  ├── Entity Extraction (Simple, no ML)                        │
│  │   └── Pattern-based + contact matching                    │
│  │                                                             │
│  ├── Knowledge Store (SQLite on-device)                       │
│  │   ├── Vector Store (chunks + embeddings)                  │
│  │   └── Graph Store (entities + relations)                  │
│  │                                                             │
│  ├── Hybrid RAG Pipeline                                      │
│  │   ├── Vector search (cosine similarity)                   │
│  │   ├── Graph traversal (entity → relations)                │
│  │   ├── Reciprocal Rank Fusion                              │
│  │   └── Reranking (score + recency)                         │
│  │                                                             │
│  ├── LLM Client (Anthropic Claude API)                        │
│  │   └── SSE streaming                                        │
│  │                                                             │
│  └── UI (SwiftUI MVVM)                                        │
│      ├── Chat + streaming responses                           │
│      ├── Knowledge gauge (sources status)                     │
│      └── Settings (API key, data sources)                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

**1. Hybrid Embeddings**
- **Bulk import (Mac):** High-quality sentence-transformers embeddings
- **Real-time (iPhone):** CoreML on-device embeddings (all-MiniLM-L6-v2)
- Both coexist in the same database, marked by `origin` field
- Optional periodic Mac sync to upgrade real-time embeddings to high-quality

**2. Two-Tier Entity Extraction**
- **Bulk import:** spaCy NER (fr_core_news_lg) for high accuracy
- **Real-time:** Simple pattern matching + contact name resolution
- Trade-off: Speed and battery preservation vs. precision

**3. Graph Store Growth Strategy**
- Graph never reset, only grows incrementally
- Relations strengthen with each interaction (strength counter)
- Entity deduplication via name normalization
- Optional pruning of weak/old relations after months

**4. Transfer Mechanism**
- **v1:** File transfer (AirDrop, iCloud Drive) — simple, works immediately
- **v2+:** HTTP API — scalable, same data format, minimal code change

---

## Component Specifications

### 1. Backend Python — Export Engine

**New module:** `exports/ios_export.py`

**Responsibilities:**
- Export SQLite database with chunks, embeddings, and metadata
- Export graph as JSON (entities + relations)
- Support incremental exports (delta since last sync)
- Compression and optimization for mobile transfer

**SQLite Export Schema:**

```sql
CREATE TABLE chunks_export (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    embedding BLOB,              -- 384 floats as bytes (1536 bytes)
    source TEXT NOT NULL,        -- "messages/Alexandre/chunk_123"
    date_ts REAL,
    metadata_json TEXT,
    origin TEXT                  -- "bulk_import"
);

CREATE TABLE contacts_export (
    phone_suffix TEXT PRIMARY KEY,  -- Last 9 digits
    name TEXT NOT NULL,
    full_phone TEXT,
    email TEXT
);
```

**Graph Export Format:**

`entities.json`:
```json
[
  {
    "id": "person_alexandre_guedj",
    "type": "Person",
    "name": "Alexandre Guedj",
    "properties": {
      "phone_numbers": ["+33612345678"],
      "emails": ["alex@startup.com"],
      "company": "Startup XYZ",
      "job_title": "CEO",
      "birthday": "1990-05-28",
      "mentions_count": 247
    }
  }
]
```

`relations.json`:
```json
[
  {
    "from": "person_alexandre_guedj",
    "to": "person_marie_dupont",
    "type": "KNOWS",
    "properties": {
      "strength": 8,
      "via": ["messages", "calendar"],
      "since_ts": 1640995200.0
    }
  }
]
```

**CLI Commands:**

```bash
# Full export (first time)
pai export-ios --output ~/Desktop/PersonalAI-initial.db

# Incremental export (WhatsApp updates)
pai export-ios --incremental --source whatsapp --since 1715875200 --output ~/Desktop/PersonalAI-delta.db
```

---

### 2. iOS App — Embedding Engine

**Model:** `all-MiniLM-L6-v2` converted to CoreML

**Specifications:**
- **Size:** 22 MB (quantized FP16)
- **Dimensions:** 384
- **Performance:** ~50ms per embedding on iPhone 12+
- **Language:** Multilingual (FR + EN)
- **License:** Apache 2.0

**Conversion Pipeline:**

```bash
# 1. Export ONNX
python scripts/export_onnx.py --model sentence-transformers/all-MiniLM-L6-v2

# 2. Convert to CoreML
python scripts/convert_to_coreml.py \
  --input models/all-MiniLM-L6-v2.onnx \
  --output ios/PersonalAIAgent/Resources/MiniLM-L6-v2.mlmodelc
```

**Swift Implementation:**

```swift
final class EmbeddingEngine {
    private let model: MLModel
    private let tokenizer: BPETokenizer

    func embed(_ text: String) throws -> [Float] {
        // 1. Tokenize (max 128 tokens)
        let tokens = tokenizer.encode(text, maxLength: 128)

        // 2. CoreML inference
        let output = try model.prediction(from: input)

        // 3. Mean pooling + L2 normalization
        return normalize(meanPool(output))
    }
}
```

**Fallback Strategy:**
- If CoreML fails (old device), use TF-IDF hash trick (degraded but functional)
- Minimum requirement: iOS 15+

---

### 3. iOS App — Graph Store

**Entity Types:**

| Type | Properties | Purpose |
|------|-----------|---------|
| **Person** | name, phone_numbers[], emails[], company, job_title, birthday | Contacts and conversation participants |
| **Event** | title, start_date, end_date, location, calendar_source | Calendar events |
| **Topic** | name, category, mentions_count | Subjects discussed in conversations |
| **Place** | name, type, visits_count | Locations mentioned |
| **Organization** | name, type | Companies, universities, associations |

**Relation Types:**

| Relation | From → To | Properties | Meaning |
|----------|-----------|-----------|---------|
| KNOWS | Person → Person | strength, via[], since_ts | Social connection |
| WORKS_WITH | Person → Person | company, since | Professional relation |
| ATTENDS | Person → Event | status | Event participation |
| DISCUSSED | Person → Topic | count, last_ts | Topic mentioned in conversations |
| WORKS_AT | Person → Organization | job_title, since | Employment |
| LOCATED_AT | Event → Place | — | Event location |
| RELATED_TO | Topic → Topic | co_occurrence_count | Topics frequently co-mentioned |

**Incremental Growth:**

```swift
// Person mention increment
if let person = graphStore.findPerson(name: "Alexandre") {
    person.mentions_count += 1
} else {
    graphStore.createPerson(name: "Alexandre")
}

// Relation strength increment
if let relation = graphStore.findRelation(from: alex, to: marie, type: .KNOWS) {
    relation.strength += 1
    relation.last_interaction_ts = Date().timeIntervalSince1970
} else {
    graphStore.createRelation(from: alex, to: marie, type: .KNOWS, strength: 1)
}
```

**SQLite Schema:**

```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties_json TEXT,
    mentions_count INTEGER DEFAULT 1,
    first_seen_ts REAL,
    last_updated_ts REAL,
    origin TEXT DEFAULT 'realtime'
);

CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    from_entity_id TEXT NOT NULL,
    to_entity_id TEXT NOT NULL,
    type TEXT NOT NULL,
    properties_json TEXT,
    strength INTEGER DEFAULT 1,
    first_seen_ts REAL,
    last_interaction_ts REAL,
    origin TEXT DEFAULT 'realtime',
    FOREIGN KEY(from_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY(to_entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_relations_from ON relations(from_entity_id);
CREATE INDEX idx_relations_to ON relations(to_entity_id);
CREATE INDEX idx_relations_strength ON relations(strength DESC);
```

---

### 4. iOS App — Hybrid RAG Pipeline

**6-Stage Retrieval Process:**

```
User Query
    ↓
1. Query Analysis
   - Classify: frequency / calendar / contact lookup / general
   - Extract entities (persons, topics, places)
    ↓
2. Parallel Retrieval
   ├─ Vector Search (cosine similarity on embeddings)
   └─ Graph Traversal (entity → related documents)
    ↓
3. Reciprocal Rank Fusion
   - Merge results from both sources
   - RRF score = Σ 1/(k + rank_i), k=60
    ↓
4. Reranking
   - Composite score: 70% RRF + 30% recency
   - Sort and take top K (default: 10)
    ↓
5. Context Assembly
   - Sanitize phone numbers → names
   - Format for LLM prompt
   - Add graph metadata (relations, profiles)
    ↓
6. LLM Call
   - System prompt + context → Anthropic Claude
   - Stream response
```

**Query Classification:**

```swift
enum QueryType {
    case frequency      // "Avec qui je parle le plus ?"
    case calendar       // "Qu'est-ce que j'ai cette semaine ?"
    case contactLookup  // "Qui est Alexandre Guedj ?"
    case general        // Everything else
}

func classifyQuery(_ query: String) -> QueryType {
    let lower = query.lowercased()

    if ["le plus", "souvent", "fréquent"].contains(where: { lower.contains($0) }) {
        return .frequency
    }
    if ["calendrier", "agenda", "prévu", "semaine"].contains(where: { lower.contains($0) }) {
        return .calendar
    }
    if ["qui est", "c'est qui", "connais"].contains(where: { lower.contains($0) }) {
        return .contactLookup
    }
    return .general
}
```

**Vector Search:**

```swift
func vectorSearch(query: String, topK: Int) async throws -> [SearchResult] {
    // 1. Generate query embedding
    let queryEmbedding = try embeddingEngine.embed(query)

    // 2. Cosine similarity search in SQLite
    return vectorStore.search(queryEmbedding: queryEmbedding, topK: topK)
}
```

**Graph Traversal:**

```swift
func graphSearch(query: String, queryType: QueryType) async -> [SearchResult] {
    var results: [SearchResult] = []

    switch queryType {
    case .frequency:
        // Get top contacts by message volume
        let topContacts = graphStore.topContacts(limit: 15)
        for contact in topContacts {
            let chunks = vectorStore.chunksForContact(contact.name, limit: 2)
            results.append(contentsOf: chunks)
        }

    case .calendar:
        // Get recent/upcoming events
        let events = graphStore.recentEvents(within: .days(30))
        for event in events {
            if let chunk = vectorStore.chunkForEvent(event.id) {
                results.append(chunk)
            }
        }

    case .contactLookup:
        // Deep dive on specific person
        let entities = entityExtractor.extractPersons(from: query)
        if let personName = entities.first,
           let person = graphStore.findPerson(name: personName) {
            let chunks = vectorStore.chunksForPerson(person.id, limit: 5)
            results.append(contentsOf: chunks)
        }

    case .general:
        // Graph expansion via entity linking
        let entities = entityExtractor.extractAll(from: query)
        for entityName in entities.allNames {
            let docs = graphStore.getEntityDocuments(entityName)
            for docId in docs.prefix(3) {
                if let chunk = vectorStore.chunkByDocId(docId) {
                    results.append(chunk)
                }
            }
        }
    }

    return results
}
```

**Context Assembly:**

```swift
func assembleContext(results: [SearchResult], queryType: QueryType) -> RAGContext {
    var blocks: [String] = []

    // Type-specific enrichment
    switch queryType {
    case .frequency:
        let topContacts = graphStore.topContacts(limit: 10)
        blocks.append("<contacts_par_volume>\n\(formatContacts(topContacts))\n</contacts_par_volume>")

    case .calendar:
        let upcoming = graphStore.upcomingEvents(limit: 5)
        blocks.append("<agenda>\n\(formatEvents(upcoming))\n</agenda>")

    case .contactLookup:
        if let person = extractedPerson {
            blocks.append(buildContactProfile(person))
        }

    case .general:
        break
    }

    // Retrieved chunks (phone numbers sanitized)
    let phoneMap = vectorStore.phoneContactMap()
    let sanitized = results.map { sanitizePhones(in: $0.text, phoneMap: phoneMap) }
    blocks.append("<context>\n\(sanitized.joined(separator: "\n\n"))\n</context>")

    return RAGContext(blocks: blocks, sources: results.map(\.source), queryType: queryType)
}
```

**Performance Targets:**

| Stage | Target Latency | Hardware |
|-------|---------------|----------|
| Query embedding | < 50ms | iPhone 12+ |
| Vector search (10k chunks) | < 100ms | SQLite indexed |
| Graph traversal | < 50ms | SQLite indexed |
| RRF fusion | < 10ms | In-memory |
| Reranking | < 5ms | In-memory |
| **Total RAG pipeline** | **< 215ms** | End-to-end |

---

### 5. iOS App — Real-time Ingestion Monitors

**iMessage Monitor:**

```swift
@MainActor
class iMessageMonitor: NSObject, UNUserNotificationCenterDelegate {
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        guard notification.request.identifier.hasPrefix("com.apple.MobileSMS") else {
            return [.banner, .sound]
        }

        let sender = notification.request.content.userInfo["sender"] as? String ?? "Unknown"
        let text = notification.request.content.body

        // Background ingestion
        Task.detached(priority: .background) {
            await self.ingestMessage(text: text, sender: sender, platform: "messages")
        }

        return [.banner, .sound]
    }

    private func ingestMessage(text: String, sender: String, platform: String) async {
        // 1. Generate embedding
        let embedding = try? embeddingEngine.embed(text)

        // 2. Extract entities
        let persons = entityExtractor.extractPersons(from: text)
        let topics = entityExtractor.extractTopics(from: text)

        // 3. Store chunk
        vectorStore.insert(text: text, embedding: embedding, source: "\(platform)/\(sender)/chunk_\(UUID())")

        // 4. Update graph
        for person in persons {
            graphStore.upsertPerson(name: person)
            graphStore.upsertRelation(from: sender, to: person, type: .KNOWS)
        }
        for topic in topics {
            graphStore.upsertTopic(name: topic)
            graphStore.upsertRelation(from: sender, to: topic, type: .DISCUSSED)
        }
    }
}
```

**Contacts Monitor:**

```swift
class ContactsMonitor {
    private let store = CNContactStore()

    func startMonitoring() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(contactsDidChange),
            name: .CNContactStoreDidChange,
            object: nil
        )

        Task.detached { await self.syncAllContacts() }
    }

    @objc private func contactsDidChange() {
        Task.detached { await self.syncAllContacts() }
    }

    private func syncAllContacts() async {
        let keys: [CNKeyDescriptor] = [
            CNContactGivenNameKey, CNContactFamilyNameKey,
            CNContactPhoneNumbersKey, CNContactEmailAddressesKey,
            CNContactJobTitleKey, CNContactOrganizationNameKey,
            CNContactBirthdayKey
        ] as [CNKeyDescriptor]

        let request = CNContactFetchRequest(keysToFetch: keys)

        try? store.enumerateContacts(with: request) { contact, _ in
            self.ingestContact(contact)
        }
    }

    private func ingestContact(_ contact: CNContact) {
        let fullName = "\(contact.givenName) \(contact.familyName)".trimmingCharacters(in: .whitespaces)

        // Create/update Person entity
        graphStore.upsertPerson(
            name: fullName,
            phoneNumbers: contact.phoneNumbers.map { $0.value.stringValue },
            emails: contact.emailAddresses.map { $0.value as String },
            company: contact.organizationName,
            jobTitle: contact.jobTitle,
            birthday: contact.birthday?.date
        )

        // Store phone → name mapping for resolution
        for phoneNumber in contact.phoneNumbers {
            let digits = phoneNumber.value.stringValue.filter { $0.isNumber }
            if digits.count >= 9 {
                let suffix = String(digits.suffix(9))
                vectorStore.upsertContact(phoneSuffix: suffix, name: fullName)
            }
        }
    }
}
```

**Calendar Monitor:**

```swift
class CalendarMonitor {
    private let eventStore = EKEventStore()

    func startMonitoring() {
        Task {
            try await eventStore.requestFullAccessToEvents()

            NotificationCenter.default.addObserver(
                self,
                selector: #selector(calendarDidChange),
                name: .EKEventStoreChanged,
                object: eventStore
            )

            await syncCalendar()
        }
    }

    private func syncCalendar() async {
        let start = Calendar.current.date(byAdding: .month, value: -6, to: Date())!
        let end = Calendar.current.date(byAdding: .month, value: 3, to: Date())!

        let predicate = eventStore.predicateForEvents(withStart: start, end: end, calendars: nil)
        let events = eventStore.events(matching: predicate)

        for event in events {
            await ingestEvent(event)
        }
    }

    private func ingestEvent(_ event: EKEvent) async {
        // Create chunk for vector search
        let chunkText = """
        Événement: \(event.title ?? "")
        Date: \(event.startDate.formatted())
        Lieu: \(event.location ?? "")
        Participants: \(event.attendees?.compactMap { $0.name }.joined(separator: ", ") ?? "")
        """

        let embedding = try? embeddingEngine.embed(chunkText)

        // Source format: calendar/YYYY-WNN
        let week = Calendar.current.component(.weekOfYear, from: event.startDate)
        let year = Calendar.current.component(.year, from: event.startDate)
        let source = "calendar/\(year)-W\(String(format: "%02d", week))"

        vectorStore.insert(text: chunkText, embedding: embedding, source: source)

        // Create Event entity + ATTENDS relations
        let eventEntity = graphStore.upsertEvent(
            title: event.title ?? "",
            startDate: event.startDate,
            endDate: event.endDate,
            location: event.location
        )

        for attendee in event.attendees ?? [] {
            if let name = attendee.name {
                let person = graphStore.upsertPerson(name: name)
                graphStore.upsertRelation(from: person.id, to: eventEntity.id, type: .ATTENDS)
            }
        }
    }
}
```

**WhatsApp Importer (Manual):**

```swift
class WhatsAppImporter {
    func importExport(from url: URL) async throws {
        let content = try String(contentsOf: url, encoding: .utf8)
        let messages = parseWhatsAppExport(content)

        // Batch embedding generation
        for batch in messages.chunked(into: 50) {
            let embeddings = try embeddingEngine.embedBatch(batch.map(\.text))

            for (message, embedding) in zip(batch, embeddings) {
                vectorStore.insert(
                    text: message.text,
                    embedding: embedding,
                    source: "whatsapp/\(message.sender)/chunk_\(UUID())",
                    dateTs: message.timestamp.timeIntervalSince1970
                )

                // Update graph
                graphStore.upsertPerson(name: message.sender)
                let topics = entityExtractor.extractTopics(from: message.text)
                for topic in topics {
                    graphStore.upsertTopic(name: topic)
                    graphStore.upsertRelation(from: message.sender, to: topic, type: .DISCUSSED)
                }
            }
        }
    }

    private func parseWhatsAppExport(_ content: String) -> [WhatsAppMessage] {
        // Parse format: "[DD/MM/YYYY, HH:MM:SS] Sender: Message"
        let pattern = #"\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.+)"#
        // ... regex parsing ...
    }
}
```

---

### 6. iOS App — UI Layer

**Architecture:** MVVM strict with `@MainActor` ViewModels

**Reused Components:**
- ✅ ChatView with streaming display
- ✅ KnowledgeGaugeView (0-100% based on connected sources)
- ✅ DesignSystem (Colors, Typography, GradientButton, MarkdownText)
- ✅ Menu burger navigation
- ✅ Settings screen structure

**New Components:**

**DataSourcesStatusView:**
```swift
struct DataSourcesStatusView: View {
    let sources: [DataSource]

    var body: some View {
        VStack(alignment: .leading) {
            Text("Sources de données").font(.headline)

            ForEach(sources) { source in
                HStack {
                    Image(systemName: source.icon)
                        .foregroundColor(source.isActive ? .green : .gray)

                    VStack(alignment: .leading) {
                        Text(source.name).font(.subheadline)
                        Text(source.statusText).font(.caption).foregroundColor(.secondary)
                    }

                    Spacer()

                    if source.isActive {
                        Text("\(source.itemCount)")
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(8)
                    }
                }
            }
        }
    }
}
```

**MessageSourcesView (NEW):**
```swift
struct MessageSourcesView: View {
    let sources: [String]
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading) {
            Button {
                withAnimation { isExpanded.toggle() }
            } label: {
                HStack {
                    Image(systemName: "doc.text.magnifyingglass")
                    Text("\(sources.count) source(s)")
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }

            if isExpanded {
                ForEach(sources, id: \.self) { source in
                    Text("• \(formatSource(source))").font(.caption2)
                }
            }
        }
        .padding(8)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}
```

**ChatViewModel Integration:**
```swift
@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isStreaming = false
    @Published var sourcesUsed: [String] = []  // NEW

    func sendMessage(_ text: String) async {
        messages.append(ChatMessage(role: .user, content: text))
        isStreaming = true

        // RAG retrieval
        let context = try await ragPipeline.retrieveContext(for: text, topK: 10)
        sourcesUsed = context.sources  // Track sources for display

        // Build system prompt with context
        let systemPrompt = buildSystemPrompt(context: context)

        // Stream LLM response
        var assistantContent = ""
        messages.append(ChatMessage(role: .assistant, content: ""))

        for try await chunk in llmClient.stream(messages: messages.dropLast(), systemPrompt: systemPrompt) {
            assistantContent += chunk
            messages[messages.count - 1].content = assistantContent
        }

        isStreaming = false
    }
}
```

---

## Security & Privacy

### Threat Model

**Protected Assets:**
- Private messages (iMessage, WhatsApp)
- Contact information (names, phones, emails)
- Calendar events
- Relationship graph
- Anthropic API key

**Attack Vectors:**
- Device theft/loss
- iOS malware
- Network interception
- Unencrypted backups
- Export file compromise

### Security Measures

**1. Database Encryption**
```swift
class SecureDatabase {
    func openWithEncryption() throws {
        // SQLCipher AES-256
        let key = try getOrCreateDatabaseKey()
        sqlite3_key(db, key, Int32(key.count))

        // iOS Data Protection
        let attributes = [
            FileAttributeKey.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication
        ]
        try FileManager.default.setAttributes(attributes, ofItemAtPath: dbPath)
    }

    private func getOrCreateDatabaseKey() throws -> Data {
        // Stored in Keychain (hardware-encrypted)
        // 32-byte random key generated on first launch
    }
}
```

**2. API Key Protection**
```swift
class KeychainManager {
    static func saveAPIKey(_ key: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "anthropic-api-key",
            kSecValueData as String: key.data(using: .utf8)!,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]

        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
}
```

**3. Network Security**
- TLS 1.3 minimum
- Certificate pinning for Anthropic API (optional)
- No logging of sensitive context in production

**4. Privacy Controls**
```swift
enum PrivacyLevel {
    case full          // Send full context (best quality)
    case anonymized    // Replace names with pseudonyms
    case metadataOnly  // Stats only, no content
}

class ContextSanitizer {
    func sanitize(_ context: RAGContext, level: PrivacyLevel) -> RAGContext {
        // User-configurable privacy level in Settings
    }
}
```

**5. Data Minimization**
- Embeddings never leave device
- Full graph never sent to LLM
- Only top K relevant chunks sent (default: 10)
- No telemetry/analytics without explicit consent

**GDPR Compliance:**
- ✅ Data stored locally (no cross-border transfer)
- ✅ Right to erasure (delete all data button)
- ✅ Data portability (SQLite export)
- ✅ Transparency (show sources per response)

---

## Testing Strategy

### Unit Tests (70% coverage target)

**Core logic:**
```swift
// VectorStoreTests.swift
- testInsertAndRetrieve()
- testCosineSimilarity()
- testPhoneNumberResolution()

// GraphStoreTests.swift
- testEntityCreationAndLookup()
- testRelationStrengthIncrement()
- testGraphTraversal()

// RAGPipelineTests.swift
- testQueryClassification()
- testRRFFusion()
- testReranking()

// EmbeddingEngineTests.swift
- testEmbeddingDimension()
- testEmbeddingNormalization()
- testSimilarTextsSimilarEmbeddings()
```

### Integration Tests (20%)

```swift
// IngestionIntegrationTests.swift
- testFullIngestionPipeline()  // Message → embedding → graph → retrieval

// RAGEndToEndTests.swift
- testQueryRetrievesRelevantContext()
- testContactProfileEnrichment()
```

### Performance Tests

```swift
// PerformanceTests.swift
- testVectorSearchPerformance()  // Target: < 200ms for 10k chunks
- testEmbeddingGenerationPerformance()  // Target: < 100ms per text
- testGraphTraversalPerformance()  // Target: < 50ms
```

### UI Tests (10%)

```swift
// ChatFlowTests.swift
- testSendMessageAndReceiveResponse()
- testStreamingDisplay()
- testSourcesExpansion()
```

---

## Implementation Plan

**Target:** MVP functional v1.0 in 1 day (aggressive timeline)

### Day 1: Rapid MVP Implementation

**Priority 1 — Core Storage & RAG (Morning, 4 hours):**
- [ ] Backend: Implement `exports/ios_export.py` (SQLite + Graph JSON)
- [ ] Backend: CLI command `pai export-ios` with real data export
- [ ] iOS: Convert embedding model ONNX → CoreML (use pre-made script)
- [ ] iOS: Implement `VectorStore.swift` (chunks + embeddings + cosine search)
- [ ] iOS: Implement `GraphStore.swift` (entities + relations, basic queries)
- [ ] iOS: Implement `EmbeddingEngine.swift` (CoreML wrapper)

**Priority 2 — RAG Pipeline (Afternoon, 3 hours):**
- [ ] iOS: Implement `HybridRAGPipeline.swift`
  - Query classification (basic patterns)
  - Vector search (cosine similarity)
  - Graph traversal (simple entity lookup)
  - RRF fusion (basic implementation)
  - Context assembly with phone sanitization
- [ ] iOS: Implement `LLMClient.swift` (Anthropic streaming, reuse existing code)

**Priority 3 — UI Integration (Evening, 2 hours):**
- [ ] iOS: Update `ChatViewModel` to use new RAG pipeline
- [ ] iOS: Reuse existing ChatView with minimal changes
- [ ] iOS: Basic import flow (file picker for bulk export)
- [ ] iOS: Keychain for API key (reuse existing code)

**Deferred to v1.1 (post-MVP):**
- Real-time monitors (iMessage, Contacts, Calendar) — v1 uses bulk import only
- Advanced entity extraction — v1 uses simple patterns
- Security hardening (SQLCipher) — v1 uses iOS Data Protection only
- UI polish and new components — v1 reuses existing UI
- Comprehensive testing — v1 has smoke tests only

**MVP v1.0 Scope:**
- ✅ Bulk import from Mac export
- ✅ On-device embeddings (CoreML)
- ✅ Hybrid RAG (vector + graph)
- ✅ Chat with streaming
- ✅ Basic UI (reused from existing app)
- ❌ No real-time ingestion (v1.1)
- ❌ No SQLCipher (v1.1)
- ❌ No comprehensive tests (v1.1)

**Milestone:** Functional app that demonstrates improved RAG quality vs. current version

---

## Deployment Checklist

### Pre-TestFlight

**Backend:**
- [ ] Export engine tested with real data (> 10k chunks)
- [ ] Delta exports functional
- [ ] CLI documentation complete

**iOS:**
- [ ] All tests passing (unit + integration)
- [ ] Performance targets met (RAG < 300ms)
- [ ] Zero memory leaks (Instruments validated)
- [ ] Crash-free rate > 99% on simulator
- [ ] Privacy manifest complete
- [ ] API key stored in Keychain only

**Security:**
- [ ] Database encrypted (SQLCipher)
- [ ] No sensitive data logged in production
- [ ] TLS 1.3 enforced

**UX:**
- [ ] Onboarding flow tested
- [ ] Bulk import < 5 min for 2 years of data
- [ ] Error messages clear and actionable

### TestFlight Beta (v0.9)

- [ ] Distribute to 10-20 beta testers
- [ ] Collect feedback on RAG quality
- [ ] Monitor crashes and performance
- [ ] Iterate for 2-3 weeks

### App Store Release (v1.0)

- [ ] Apple Review Guidelines compliance
- [ ] RGPD compliance validated
- [ ] App Store Connect metadata complete
- [ ] Support email configured
- [ ] Pricing tier set (if applicable)

---

## Future Evolution

### Phase 2: Cloud Backend (Post-v1)

**Changes required:**
1. Backend API endpoints replace file export
2. iOS app HTTP client replaces file import
3. **Business logic unchanged** (same merge functions)

**Benefits:**
- Multi-device sync (iPhone + iPad)
- Server-side ingestion (Email OAuth)
- Observability (token usage tracking)
- Monetization (RevenueCat subscriptions)

### Additional Data Sources

| Source | Effort | Priority | Notes |
|--------|--------|----------|-------|
| Email (Gmail/iCloud) | Medium | High | OAuth flow + IMAP parsing |
| Photos | Medium | Medium | EXIF metadata + ML recognition |
| HealthKit | Low | Medium | Official iOS API |
| Notes (Apple Notes) | Low | Medium | AppleScript export on Mac |
| Browser history | High | Low | Complex, privacy concerns |

### Agent Mode (Actions)

Beyond read-only queries, enable the agent to take actions:
- Create calendar events
- Send messages
- Log health data
- Set reminders

Requires careful UX for user confirmation and safety.

---

## Success Metrics

**MVP v1.0 Goals (1-day build):**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **RAG Quality** | Responses noticeably better than LIKE-based search | Direct comparison |
| **Performance** | RAG pipeline < 500ms (relaxed for MVP) | Manual testing |
| **Functionality** | Bulk import works, chat responds with context | Smoke testing |
| **Crash-free** | > 95% (relaxed for MVP) | Manual testing |

**v1.1+ Goals (post-MVP):**
- Real-time sync: New data indexed within 1 min
- Performance: RAG pipeline < 300ms
- Comprehensive testing: Coverage > 70%
- Production-ready security (SQLCipher)

---

## Appendix

### A. Data Size Estimates

**Active user (2 years):**
- 50k chunks (messages, calendar, contacts) → ~100 MB
- 5k entities → ~2.5 MB
- 20k relations → ~6 MB
- **Total: ~110 MB** (acceptable for modern iPhones)

### B. Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, Qdrant, Neo4j, spaCy, sentence-transformers |
| **iOS App** | Swift 5.9+, SwiftUI, SQLite3, CoreML |
| **Embeddings** | all-MiniLM-L6-v2 (384D, 22MB) |
| **LLM** | Anthropic Claude (claude-haiku-4-5) via API |
| **Storage** | SQLite on-device (encrypted with SQLCipher) |
| **Min iOS** | iOS 17.0+ |

### C. Key Files

**Backend (Python):**
```
exports/ios_export.py
exports/delta_manager.py
scripts/export_for_ios.py
scripts/convert_embedding_model.py
```

**iOS (Swift):**
```
Core/Embeddings/EmbeddingEngine.swift
Core/Storage/VectorStore.swift
Core/Storage/GraphStore.swift
Core/RAG/HybridRAGPipeline.swift
Core/Ingestion/iMessageMonitor.swift
Core/Ingestion/ContactsMonitor.swift
Core/Ingestion/CalendarMonitor.swift
Core/Ingestion/WhatsAppImporter.swift
Core/LLM/LLMClient.swift
Core/Security/KeychainManager.swift
Features/Chat/ChatViewModel.swift
Features/Settings/DataSourcesView.swift
```

### D. References

- Anthropic API: https://docs.anthropic.com/
- CoreML: https://developer.apple.com/documentation/coreml
- SQLCipher: https://www.zetetic.net/sqlcipher/
- sentence-transformers: https://www.sbert.net/
- Reciprocal Rank Fusion: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

---

**End of specification v1.0**
