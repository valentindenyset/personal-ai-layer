import Foundation

enum ImportError: Error {
    case invalidFormat
    case databaseCorrupted
    case jsonParseFailed
}

final class BulkImporter {
    private let vectorStore: VectorStore
    private let graphStore: GraphStore

    init(vectorStore: VectorStore, graphStore: GraphStore) {
        self.vectorStore = vectorStore
        self.graphStore = graphStore
    }

    /// Import from Mac export (SQLite + JSON files)
    func importBulkExport(databaseURL: URL, entitiesURL: URL, relationsURL: URL) async throws {
        // 1. Import vector database
        try await importVectorDatabase(from: databaseURL)

        // 2. Import graph entities
        try await importEntities(from: entitiesURL)

        // 3. Import graph relations
        try await importRelations(from: relationsURL)
    }

    private func importVectorDatabase(from url: URL) async throws {
        // Copy the database file to app's documents directory
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let destURL = docs.appendingPathComponent("knowledge.db")

        // Remove existing if present
        try? FileManager.default.removeItem(at: destURL)

        // Copy new database
        try FileManager.default.copyItem(at: url, to: destURL)
    }

    private func importEntities(from url: URL) async throws {
        let data = try Data(contentsOf: url)
        guard let entities = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw ImportError.jsonParseFailed
        }

        for entity in entities {
            guard let type = entity["type"] as? String,
                  let name = entity["name"] as? String,
                  let properties = entity["properties"] as? [String: Any] else {
                continue
            }

            switch type {
            case "Person":
                let phoneNumbers = properties["phone_numbers"] as? [String] ?? []
                let emails = properties["emails"] as? [String] ?? []
                let company = properties["company"] as? String
                let jobTitle = properties["job_title"] as? String

                graphStore.upsertPerson(
                    name: name,
                    phoneNumbers: phoneNumbers,
                    emails: emails,
                    company: company,
                    jobTitle: jobTitle
                )

            case "Topic":
                graphStore.upsertTopic(name: name)

            default:
                // For MVP, only handle Person and Topic
                break
            }
        }
    }

    private func importRelations(from url: URL) async throws {
        let data = try Data(contentsOf: url)
        guard let relations = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw ImportError.jsonParseFailed
        }

        for relation in relations {
            guard let from = relation["from"] as? String,
                  let to = relation["to"] as? String,
                  let typeString = relation["type"] as? String,
                  let type = RelationType(rawValue: typeString) else {
                continue
            }

            // Import relation (will set strength from properties if available)
            graphStore.upsertRelation(from: from, to: to, type: type)

            // If relation has strength property, update it
            if let properties = relation["properties"] as? [String: Any],
               let strength = properties["strength"] as? Int {
                // For MVP, we'll just insert once with default strength
                // Full implementation would set the strength directly
            }
        }
    }
}
