// Core/Storage/VectorStore.swift
import Foundation
import SQLite3

struct SearchResult {
    let text: String
    let score: Float
    let source: String
    let dateTs: Double
}

final class VectorStore {
    private var db: OpaquePointer?
    private let dbPath: String

    init(inMemory: Bool = false) {
        if inMemory {
            dbPath = ":memory:"
        } else {
            let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            dbPath = docs.appendingPathComponent("knowledge.db").path
        }

        openDatabase()
        createTables()
    }

    deinit {
        sqlite3_close(db)
    }

    // MARK: - Chunk Operations

    func insert(text: String, embedding: [Float]?, source: String, dateTs: Double) {
        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        // Convert embedding to BLOB
        var embeddingBlob: Data? = nil
        if let emb = embedding {
            embeddingBlob = Data(bytes: emb, count: emb.count * MemoryLayout<Float>.size)
        }

        let sql = "INSERT INTO chunks (text, embedding, source, date_ts, origin) VALUES (?, ?, ?, ?, 'realtime')"
        sqlite3_prepare_v2(db, sql, -1, &stmt, nil)

        sqlite3_bind_text(stmt, 1, (text as NSString).utf8String, -1, nil)
        if let blob = embeddingBlob {
            blob.withUnsafeBytes { ptr in
                sqlite3_bind_blob(stmt, 2, ptr.baseAddress, Int32(blob.count), nil)
            }
        } else {
            sqlite3_bind_null(stmt, 2)
        }
        sqlite3_bind_text(stmt, 3, (source as NSString).utf8String, -1, nil)
        sqlite3_bind_double(stmt, 4, dateTs)

        sqlite3_step(stmt)
    }

    func search(queryEmbedding: [Float], topK: Int = 10) -> [SearchResult] {
        var results: [SearchResult] = []
        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        // Fetch all chunks with embeddings
        let sql = "SELECT text, embedding, source, date_ts FROM chunks WHERE embedding IS NOT NULL"
        sqlite3_prepare_v2(db, sql, -1, &stmt, nil)

        while sqlite3_step(stmt) == SQLITE_ROW {
            let text = String(cString: sqlite3_column_text(stmt, 0))
            let source = String(cString: sqlite3_column_text(stmt, 2))
            let dateTs = sqlite3_column_double(stmt, 3)

            // Extract embedding BLOB
            if let blobPtr = sqlite3_column_blob(stmt, 1) {
                let blobSize = sqlite3_column_bytes(stmt, 1)
                let floatCount = Int(blobSize) / MemoryLayout<Float>.size

                let embedding = Array(UnsafeBufferPointer(
                    start: blobPtr.assumingMemoryBound(to: Float.self),
                    count: floatCount
                ))

                // Calculate cosine similarity
                let score = cosineSimilarity(queryEmbedding, embedding)

                results.append(SearchResult(
                    text: text,
                    score: score,
                    source: source,
                    dateTs: dateTs
                ))
            }
        }

        // Sort by score descending and take top K
        return results
            .sorted { $0.score > $1.score }
            .prefix(topK)
            .map { $0 }
    }

    // MARK: - Contact Operations

    func upsertContact(phoneSuffix: String, name: String) {
        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        let sql = "INSERT OR REPLACE INTO contacts (phone_suffix, name) VALUES (?, ?)"
        sqlite3_prepare_v2(db, sql, -1, &stmt, nil)
        sqlite3_bind_text(stmt, 1, (phoneSuffix as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 2, (name as NSString).utf8String, -1, nil)
        sqlite3_step(stmt)
    }

    func phoneContactMap() -> [String: String] {
        var map: [String: String] = [:]
        var stmt: OpaquePointer?
        defer { sqlite3_finalize(stmt) }

        sqlite3_prepare_v2(db, "SELECT phone_suffix, name FROM contacts", -1, &stmt, nil)

        while sqlite3_step(stmt) == SQLITE_ROW {
            let suffix = String(cString: sqlite3_column_text(stmt, 0))
            let name = String(cString: sqlite3_column_text(stmt, 1))
            map[suffix] = name
        }

        return map
    }

    // MARK: - Private Helpers

    private func openDatabase() {
        sqlite3_open(dbPath, &db)
    }

    private func createTables() {
        let sql = """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            embedding BLOB,
            source TEXT NOT NULL,
            date_ts REAL DEFAULT 0,
            metadata_json TEXT,
            origin TEXT DEFAULT 'realtime',
            created_at INTEGER DEFAULT (unixepoch())
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source);
        CREATE INDEX IF NOT EXISTS idx_chunks_date ON chunks(date_ts DESC);

        CREATE TABLE IF NOT EXISTS contacts (
            phone_suffix TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            full_phone TEXT,
            email TEXT
        );
        """

        sqlite3_exec(db, sql, nil, nil, nil)
    }

    private func cosineSimilarity(_ a: [Float], _ b: [Float]) -> Float {
        guard a.count == b.count else { return 0.0 }

        // Since embeddings are already normalized, dot product = cosine similarity
        let dot = zip(a, b).reduce(0.0) { result, pair in result + pair.0 * pair.1 }
        return dot
    }
}
