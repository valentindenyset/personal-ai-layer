// Tests/EmbeddingEngineTests.swift
import XCTest
@testable import PersonalAIAgent

final class EmbeddingEngineTests: XCTestCase {
    var engine: EmbeddingEngine!

    override func setUp() {
        super.setUp()
        engine = try! EmbeddingEngine()
    }

    func testEmbeddingDimension() throws {
        let embedding = try engine.embed("Test text")
        XCTAssertEqual(embedding.count, 384, "Embedding should be 384-dimensional")
    }

    func testEmbeddingNormalization() throws {
        let embedding = try engine.embed("Test text")

        // Should be L2 normalized (norm = 1.0)
        let norm = sqrt(embedding.reduce(0.0) { $0 + $1 * $1 })
        XCTAssertEqual(norm, 1.0, accuracy: 0.01, "Embedding should be L2 normalized")
    }

    func testSimilarTextsSimilarEmbeddings() throws {
        let e1 = try engine.embed("I love soccer")
        let e2 = try engine.embed("I enjoy football")
        let e3 = try engine.embed("Pizza is delicious")

        let sim12 = cosineSimilarity(e1, e2)
        let sim13 = cosineSimilarity(e1, e3)

        XCTAssertGreaterThan(sim12, sim13, "Similar texts should have higher similarity")
    }

    private func cosineSimilarity(_ a: [Float], _ b: [Float]) -> Float {
        let dot = zip(a, b).reduce(0.0) { result, pair in result + pair.0 * pair.1 }
        return dot  // Already normalized, so dot product = cosine similarity
    }
}
