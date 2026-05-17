import Foundation
import SQLite3

enum RelationType: String {
    case KNOWS
    case WORKS_WITH
    case ATTENDS
    case DISCUSSED
    case WORKS_AT
    case LOCATED_AT
    case RELATED_TO
}

struct Person {
    let id: String
    let name: String
    let phoneNumbers: [String]
    let emails: [String]
    let company: String?
    let jobTitle: String?
    let mentionsCount: Int
}

struct Relation {
    let id: String
    let fromEntityID: String
    let toEntityID: String
    let type: RelationType
    let strength: Int
    let lastInteractionTs: Double
}

struct TopContact {
    let name: String
    let platforms: [String]
    let count: Int
}

final class GraphStore {
    private var db: OpaquePointer?
    private let dbPath: String

    init(inMemory: Bool = false) {
        if inMemory {
            dbPath = ":memory:"
        } else {
            let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            dbPath = docs.appendingPathComponent("graph.db").path
        }

        openDatabase()
        createTables()
    }

    deinit {
        sqlite3_close(db)
    }

    // MARK: - Entity Operations

    @discardableResult
    func upsertPerson(
        name: String,
        phoneNumbers: [String] = [],
        emails: [String] = [],
        company: String? = nil,
        jobTitle: String? = nil
    ) -> String {
        let id = "person_\(name.lowercased().replacingOccurrences(of: " ", with: "_"))"

        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        // Check if exists
        sqlite3_prepare_v2(db, "SELECT mentions_count FROM entities WHERE id = ?", -1, &stmt, nil)
        sqlite3_bind_text(stmt, 1, (id as NSString).utf8String, -1, nil)

        if sqlite3_step(stmt) == SQLITE_ROW {
            // Update existing
            let currentCount = sqlite3_column_int(stmt, 0)
            sqlite3_finalize(stmt)

            let updateSQL = "UPDATE entities SET mentions_count = ?, last_updated_ts = unixepoch() WHERE id = ?"
            sqlite3_prepare_v2(db, updateSQL, -1, &stmt, nil)
            sqlite3_bind_int(stmt, 1, currentCount + 1)
            sqlite3_bind_text(stmt, 2, (id as NSString).utf8String, -1, nil)
            sqlite3_step(stmt)
        } else {
            // Insert new
            sqlite3_finalize(stmt)

            let properties = [
                "phone_numbers": phoneNumbers,
                "emails": emails,
                "company": company ?? "",
                "job_title": jobTitle ?? ""
            ]
            let propertiesJSON = try? JSONSerialization.data(withJSONObject: properties)
            let propertiesString = String(data: propertiesJSON ?? Data(), encoding: .utf8) ?? "{}"

            let insertSQL = """
            INSERT INTO entities (id, type, name, properties_json, mentions_count, first_seen_ts, last_updated_ts, origin)
            VALUES (?, 'Person', ?, ?, 1, unixepoch(), unixepoch(), 'realtime')
            """
            sqlite3_prepare_v2(db, insertSQL, -1, &stmt, nil)
            sqlite3_bind_text(stmt, 1, (id as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 2, (name as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 3, (propertiesString as NSString).utf8String, -1, nil)
            sqlite3_step(stmt)
        }

        return id
    }

    @discardableResult
    func upsertTopic(name: String) -> String {
        let id = "topic_\(name.lowercased().replacingOccurrences(of: " ", with: "_"))"

        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        sqlite3_prepare_v2(db, "SELECT mentions_count FROM entities WHERE id = ?", -1, &stmt, nil)
        sqlite3_bind_text(stmt, 1, (id as NSString).utf8String, -1, nil)

        if sqlite3_step(stmt) == SQLITE_ROW {
            let currentCount = sqlite3_column_int(stmt, 0)
            sqlite3_finalize(stmt)

            let updateSQL = "UPDATE entities SET mentions_count = ?, last_updated_ts = unixepoch() WHERE id = ?"
            sqlite3_prepare_v2(db, updateSQL, -1, &stmt, nil)
            sqlite3_bind_int(stmt, 1, currentCount + 1)
            sqlite3_bind_text(stmt, 2, (id as NSString).utf8String, -1, nil)
            sqlite3_step(stmt)
        } else {
            sqlite3_finalize(stmt)

            let insertSQL = """
            INSERT INTO entities (id, type, name, properties_json, mentions_count, first_seen_ts, last_updated_ts, origin)
            VALUES (?, 'Topic', ?, '{}', 1, unixepoch(), unixepoch(), 'realtime')
            """
            sqlite3_prepare_v2(db, insertSQL, -1, &stmt, nil)
            sqlite3_bind_text(stmt, 1, (id as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 2, (name as NSString).utf8String, -1, nil)
            sqlite3_step(stmt)
        }

        return id
    }

    func findPerson(name: String) -> Person? {
        let id = "person_\(name.lowercased().replacingOccurrences(of: " ", with: "_"))"

        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        let sql = "SELECT name, properties_json, mentions_count FROM entities WHERE id = ? AND type = 'Person'"
        sqlite3_prepare_v2(db, sql, -1, &stmt, nil)
        sqlite3_bind_text(stmt, 1, (id as NSString).utf8String, -1, nil)

        guard sqlite3_step(stmt) == SQLITE_ROW else { return nil }

        let name = String(cString: sqlite3_column_text(stmt, 0))
        let propertiesString = String(cString: sqlite3_column_text(stmt, 1))
        let mentionsCount = Int(sqlite3_column_int(stmt, 2))

        // Parse properties JSON
        let properties = (try? JSONSerialization.jsonObject(
            with: propertiesString.data(using: .utf8) ?? Data()
        ) as? [String: Any]) ?? [:]

        return Person(
            id: id,
            name: name,
            phoneNumbers: properties["phone_numbers"] as? [String] ?? [],
            emails: properties["emails"] as? [String] ?? [],
            company: properties["company"] as? String,
            jobTitle: properties["job_title"] as? String,
            mentionsCount: mentionsCount
        )
    }

    // MARK: - Relation Operations

    func upsertRelation(from: String, to: String, type: RelationType) {
        let relationID = "\(from)_\(type.rawValue)_\(to)"

        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        // Check if exists
        sqlite3_prepare_v2(db, "SELECT strength FROM relations WHERE id = ?", -1, &stmt, nil)
        sqlite3_bind_text(stmt, 1, (relationID as NSString).utf8String, -1, nil)

        if sqlite3_step(stmt) == SQLITE_ROW {
            // Update strength
            let currentStrength = sqlite3_column_int(stmt, 0)
            sqlite3_finalize(stmt)

            let updateSQL = "UPDATE relations SET strength = ?, last_interaction_ts = unixepoch() WHERE id = ?"
            sqlite3_prepare_v2(db, updateSQL, -1, &stmt, nil)
            sqlite3_bind_int(stmt, 1, currentStrength + 1)
            sqlite3_bind_text(stmt, 2, (relationID as NSString).utf8String, -1, nil)
            sqlite3_step(stmt)
        } else {
            // Insert new
            sqlite3_finalize(stmt)

            let insertSQL = """
            INSERT INTO relations (id, from_entity_id, to_entity_id, type, properties_json, strength, first_seen_ts, last_interaction_ts, origin)
            VALUES (?, ?, ?, ?, '{}', 1, unixepoch(), unixepoch(), 'realtime')
            """
            sqlite3_prepare_v2(db, insertSQL, -1, &stmt, nil)
            sqlite3_bind_text(stmt, 1, (relationID as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 2, (from as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 3, (to as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 4, (type.rawValue as NSString).utf8String, -1, nil)
            sqlite3_step(stmt)
        }
    }

    func getRelation(from: String, to: String, type: RelationType) -> Relation? {
        let relationID = "\(from)_\(type.rawValue)_\(to)"

        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        let sql = "SELECT strength, last_interaction_ts FROM relations WHERE id = ?"
        sqlite3_prepare_v2(db, sql, -1, &stmt, nil)
        sqlite3_bind_text(stmt, 1, (relationID as NSString).utf8String, -1, nil)

        guard sqlite3_step(stmt) == SQLITE_ROW else { return nil }

        let strength = Int(sqlite3_column_int(stmt, 0))
        let lastTs = sqlite3_column_double(stmt, 1)

        return Relation(
            id: relationID,
            fromEntityID: from,
            toEntityID: to,
            type: type,
            strength: strength,
            lastInteractionTs: lastTs
        )
    }

    // MARK: - Query Operations

    func topContacts(limit: Int = 15) -> [TopContact] {
        var contacts: [String: (platforms: Set<String>, count: Int)] = [:]
        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        // Query relations from user to persons
        let sql = """
        SELECT to_entity_id, strength FROM relations
        WHERE from_entity_id = 'user' AND type = 'KNOWS'
        ORDER BY strength DESC
        LIMIT ?
        """
        sqlite3_prepare_v2(db, sql, -1, &stmt, nil)
        sqlite3_bind_int(stmt, 1, Int32(limit))

        while sqlite3_step(stmt) == SQLITE_ROW {
            let toID = String(cString: sqlite3_column_text(stmt, 0))
            let strength = Int(sqlite3_column_int(stmt, 1))

            // Extract name from ID
            let name = toID.replacingOccurrences(of: "person_", with: "").replacingOccurrences(of: "_", with: " ")

            contacts[name] = (platforms: ["messages"], count: strength)
        }

        return contacts
            .sorted { $0.value.count > $1.value.count }
            .map { TopContact(name: $0.key, platforms: Array($0.value.platforms), count: $0.value.count) }
    }

    // MARK: - Private Helpers

    private func openDatabase() {
        sqlite3_open(dbPath, &db)
    }

    private func createTables() {
        let sql = """
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            properties_json TEXT,
            mentions_count INTEGER DEFAULT 1,
            first_seen_ts REAL,
            last_updated_ts REAL,
            origin TEXT DEFAULT 'realtime'
        );
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name COLLATE NOCASE);

        CREATE TABLE IF NOT EXISTS relations (
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
        CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_entity_id);
        CREATE INDEX IF NOT EXISTS idx_relations_to ON relations(to_entity_id);
        CREATE INDEX IF NOT EXISTS idx_relations_strength ON relations(strength DESC);
        """

        sqlite3_exec(db, sql, nil, nil, nil)
    }
}
