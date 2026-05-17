// Tests/VectorStoreTests.swift
import XCTest
@testable import PersonalAIAgent

final class VectorStoreTests: XCTestCase {
    var vectorStore: VectorStore!

    override func setUp() {
        super.setUp()
        vectorStore = VectorStore(inMemory: true)
    }

    func testInsertAndRetrieve() throws {
        let embedding = [Float](repeating: 0.5, count: 384)

        vectorStore.insert(
            text: "Hello world",
            embedding: embedding,
            source: "test/chunk_1",
            dateTs: 1715875200.0
        )

        let results = vectorStore.search(queryEmbedding: embedding, topK: 1)

        XCTAssertEqual(results.count, 1)
        XCTAssertEqual(results[0].text, "Hello world")
        XCTAssertEqual(results[0].source, "test/chunk_1")
    }

    func testCosineSimilarityRanking() throws {
        let query = [Float](repeating: 1.0, count: 384)
        let similar = normalize([Float](repeating: 0.9, count: 384))
        let dissimilar = normalize([Float](repeating: -0.5, count: 384))

        vectorStore.insert(text: "Similar", embedding: similar, source: "s1", dateTs: 0)
        vectorStore.insert(text: "Dissimilar", embedding: dissimilar, source: "s2", dateTs: 0)

        let results = vectorStore.search(queryEmbedding: query, topK: 2)

        XCTAssertEqual(results[0].text, "Similar")
        XCTAssertGreaterThan(results[0].score, results[1].score)
    }

    func testPhoneContactMapping() throws {
        vectorStore.upsertContact(phoneSuffix: "612345678", name: "Alexandre Guedj")

        let map = vectorStore.phoneContactMap()

        XCTAssertEqual(map["612345678"], "Alexandre Guedj")
    }

    private func normalize(_ vector: [Float]) -> [Float] {
        let norm = sqrt(vector.reduce(0) { $0 + $1 * $1 })
        return vector.map { $0 / norm }
    }
}
