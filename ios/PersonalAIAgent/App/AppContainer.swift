import Foundation

@MainActor
final class AppContainer: ObservableObject {
    // Storage
    let vectorStore: VectorStore
    let graphStore: GraphStore

    // Core services
    let embeddingEngine: EmbeddingEngine
    let ragPipeline: HybridRAGPipeline
    let llmClient: LLMClient
    let bulkImporter: BulkImporter

    // View models
    let chatViewModel: ChatViewModel

    init() {
        // Initialize storage
        self.vectorStore = VectorStore()
        self.graphStore = GraphStore()

        // Initialize services
        self.embeddingEngine = try! EmbeddingEngine()
        self.llmClient = LLMClient()

        self.ragPipeline = HybridRAGPipeline(
            vectorStore: vectorStore,
            graphStore: graphStore,
            embeddingEngine: embeddingEngine
        )

        self.bulkImporter = BulkImporter(
            vectorStore: vectorStore,
            graphStore: graphStore
        )

        // Initialize view models
        self.chatViewModel = ChatViewModel(
            ragPipeline: ragPipeline,
            llmClient: llmClient
        )
    }
}
