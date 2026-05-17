import Foundation

struct RAGContext {
    let blocks: [String]
    let sources: [String]
    let queryType: QueryType

    var fullContext: String {
        blocks.joined(separator: "\n\n")
    }
}

@MainActor
final class HybridRAGPipeline {
    private let vectorStore: VectorStore
    private let graphStore: GraphStore
    private let embeddingEngine: EmbeddingEngine
    private let classifier = QueryClassifier()

    init(vectorStore: VectorStore, graphStore: GraphStore, embeddingEngine: EmbeddingEngine) {
        self.vectorStore = vectorStore
        self.graphStore = graphStore
        self.embeddingEngine = embeddingEngine
    }

    // MARK: - Main Entry Point

    func retrieveContext(for query: String, topK: Int = 10) async throws -> RAGContext {
        // 1. Classify query
        let queryType = classifier.classify(query)

        // 2. Parallel retrieval
        async let vectorResults = vectorSearch(query: query, topK: topK * 2)
        async let graphResults = graphSearch(query: query, queryType: queryType)

        let (vResults, gResults) = try await (vectorResults, graphResults)

        // 3. RRF Fusion
        let fusedResults = reciprocalRankFusion(vectorResults: vResults, graphResults: gResults)

        // 4. Reranking
        let reranked = rerank(results: fusedResults, topK: topK)

        // 5. Assemble context
        return assembleContext(results: reranked, queryType: queryType, query: query)
    }

    // MARK: - Vector Search

    private func vectorSearch(query: String, topK: Int) async throws -> [SearchResult] {
        let queryEmbedding = try embeddingEngine.embed(query)
        return vectorStore.search(queryEmbedding: queryEmbedding, topK: topK)
    }

    // MARK: - Graph Search

    private func graphSearch(query: String, queryType: QueryType) async -> [SearchResult] {
        var results: [SearchResult] = []

        switch queryType {
        case .frequency:
            // Get top contacts
            let topContacts = graphStore.topContacts(limit: 10)
            // For MVP, just return empty - full implementation would fetch chunks for these contacts

        case .calendar:
            // For MVP, skip calendar-specific retrieval
            break

        case .contactLookup:
            // Extract person name from query
            let name = extractPersonName(from: query)
            if let person = graphStore.findPerson(name: name) {
                // For MVP, just mark that we found the person
                // Full implementation would fetch related chunks
            }

        case .general:
            // No special graph handling for general queries in MVP
            break
        }

        return results
    }

    // MARK: - RRF Fusion

    func reciprocalRankFusion(vectorResults: [SearchResult], graphResults: [SearchResult]) -> [SearchResult] {
        let k: Float = 60.0
        var scoreMap: [String: (result: SearchResult, score: Float)] = [:]

        // Score vector results
        for (rank, result) in vectorResults.enumerated() {
            let rrfScore = 1.0 / (k + Float(rank + 1))
            scoreMap[result.source] = (result, rrfScore)
        }

        // Add graph results scores
        for (rank, result) in graphResults.enumerated() {
            let rrfScore = 1.0 / (k + Float(rank + 1))
            if var existing = scoreMap[result.source] {
                existing.score += rrfScore
                scoreMap[result.source] = existing
            } else {
                scoreMap[result.source] = (result, rrfScore)
            }
        }

        // Sort by RRF score
        return scoreMap.values
            .sorted { $0.score > $1.score }
            .map { var r = $0.result; r.score = $0.score; return r }
    }

    // MARK: - Reranking

    private func rerank(results: [SearchResult], topK: Int) -> [SearchResult] {
        let now = Date().timeIntervalSince1970

        return results
            .map { result in
                var r = result

                // Composite score: 70% RRF + 30% recency
                let recencyDays = (now - result.dateTs) / (24 * 3600)
                let recencyScore = max(0, 1.0 - Float(recencyDays) / 365.0)

                r.score = (result.score * 0.7) + (recencyScore * 0.3)
                return r
            }
            .sorted { $0.score > $1.score }
            .prefix(topK)
            .map { $0 }
    }

    // MARK: - Context Assembly

    private func assembleContext(results: [SearchResult], queryType: QueryType, query: String) -> RAGContext {
        var blocks: [String] = []

        // Type-specific blocks
        switch queryType {
        case .frequency:
            let topContacts = graphStore.topContacts(limit: 10)
            if !topContacts.isEmpty {
                let contactsList = topContacts.enumerated().map { i, c in
                    "- \(i + 1). **\(c.name)** (\(c.count) échanges)"
                }.joined(separator: "\n")

                blocks.append("""
                <contacts_par_volume>
                Top contacts par volume d'échanges :
                \(contactsList)
                </contacts_par_volume>
                """)
            }

        case .calendar, .contactLookup, .general:
            break  // No special blocks for MVP
        }

        // Retrieved chunks (sanitized)
        let phoneMap = vectorStore.phoneContactMap()
        let sanitizedChunks = results.map { result in
            let sanitized = sanitizePhones(in: result.text, phoneMap: phoneMap)
            return "---\n\(sanitized)\nSource: \(result.source)"
        }.joined(separator: "\n\n")

        if !sanitizedChunks.isEmpty {
            blocks.append("""
            <context>
            \(sanitizedChunks)
            </context>
            """)
        }

        return RAGContext(
            blocks: blocks,
            sources: results.map { $0.source },
            queryType: queryType
        )
    }

    // MARK: - Helpers

    private func extractPersonName(from query: String) -> String {
        // Simple extraction: look for capitalized words after "qui est" or "c'est qui"
        let patterns = ["qui est ", "c'est qui "]
        for pattern in patterns {
            if let range = query.lowercased().range(of: pattern) {
                let afterPattern = String(query[range.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines)
                return afterPattern.components(separatedBy: " ").first ?? ""
            }
        }
        return ""
    }

    private func sanitizePhones(in text: String, phoneMap: [String: String]) -> String {
        var result = text

        // Replace known numbers with names
        for (suffix, name) in phoneMap {
            result = result.replacingOccurrences(of: "+33\(suffix)", with: name)
            result = result.replacingOccurrences(of: "0\(suffix)", with: name)
        }

        // Replace unknown numbers with "un contact"
        result = result.replacing(#/\+33\d{9}/#, with: "un contact")
        result = result.replacing(#/\b0[67]\d{8}\b/#, with: "un contact")

        return result
    }
}
