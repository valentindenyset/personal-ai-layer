import XCTest
@testable import PersonalAIAgent

final class RAGPipelineTests: XCTestCase {
    var pipeline: HybridRAGPipeline!
    var vectorStore: VectorStore!
    var graphStore: GraphStore!
    var embeddingEngine: EmbeddingEngine!

    override func setUp() async throws {
        vectorStore = VectorStore(inMemory: true)
        graphStore = GraphStore(inMemory: true)
        embeddingEngine = try EmbeddingEngine()
        pipeline = HybridRAGPipeline(
            vectorStore: vectorStore,
            graphStore: graphStore,
            embeddingEngine: embeddingEngine
        )
    }

    func testRetrieveContextForFrequencyQuery() async throws {
        // Setup test data
        let alex = graphStore.upsertPerson(name: "Alexandre")
        graphStore.upsertRelation(from: "user", to: alex, type: .KNOWS)

        let embedding = try embeddingEngine.embed("Alexandre message")
        vectorStore.insert(text: "Message from Alexandre", embedding: embedding, source: "messages/alexandre/1", dateTs: 0)

        // Query
        let context = try await pipeline.retrieveContext(for: "Avec qui je parle le plus ?", topK: 5)

        XCTAssertFalse(context.blocks.isEmpty)
        XCTAssertTrue(context.fullContext.contains("Alexandre"))
    }

    func testRRFFusion() throws {
        let vectorResults = [
            SearchResult(text: "A", score: 0.9, source: "s1", dateTs: 0)
        ]
        let graphResults = [
            SearchResult(text: "B", score: 0.8, source: "s2", dateTs: 0)
        ]

        let fused = pipeline.reciprocalRankFusion(vectorResults: vectorResults, graphResults: graphResults)

        XCTAssertEqual(fused.count, 2)
        // First result should have higher RRF score (lower rank)
    }
}
