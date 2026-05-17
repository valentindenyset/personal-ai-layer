// Core/Embeddings/EmbeddingEngine.swift
import Foundation
import CryptoKit

enum EmbeddingError: Error {
    case modelLoadFailed
    case tokenizationFailed
    case inferenceFailed
}

final class EmbeddingEngine {
    private let maxTokens = 128
    private let embeddingDim = 384

    init() throws {
        // For MVP: Verify model file exists
        guard let modelURL = Bundle.main.url(
            forResource: "MiniLM-L6-v2.mlmodelc/model",
            withExtension: "onnx"
        ) else {
            throw EmbeddingError.modelLoadFailed
        }

        // Model loaded successfully (actual ONNX inference will be added when ONNX Runtime is integrated)
    }

    /// Generate 384-dimensional embedding for text
    /// NOTE: This is a simplified MVP implementation using deterministic hash-based embeddings.
    /// Production version will use actual ONNX Runtime inference.
    func embed(_ text: String) throws -> [Float] {
        // 1. Tokenize
        let tokens = tokenize(text)

        // 2. Generate deterministic embedding based on tokens
        // This creates embeddings that have the key property: similar texts → similar embeddings
        let embedding = generateDeterministicEmbedding(tokens: tokens)

        // 3. L2 normalize
        return normalize(embedding)
    }

    // MARK: - Private Helpers

    private func tokenize(_ text: String) -> [String] {
        // Simplified tokenization for MVP
        let words = text.lowercased()
            .components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }

        return Array(words.prefix(maxTokens - 2))
    }

    private func generateDeterministicEmbedding(tokens: [String]) -> [Float] {
        // Create a deterministic embedding based on token hashes
        // This ensures same text → same embedding, and similar texts → similar embeddings
        var embedding = [Float](repeating: 0.0, count: embeddingDim)

        // Use each token to influence the embedding vector
        for (index, token) in tokens.enumerated() {
            // Hash the token to get deterministic values
            let hash = SHA256.hash(data: Data(token.utf8))
            let bytes = Array(hash)

            // Spread hash values across embedding dimensions
            for i in 0..<embeddingDim {
                let byteIndex = i % bytes.count
                let value = Float(bytes[byteIndex]) / 255.0 - 0.5

                // Position-weighted contribution (earlier tokens matter more)
                let positionWeight = 1.0 / Float(index + 1)
                embedding[i] += value * positionWeight
            }
        }

        // Add token count information (helps distinguish longer/shorter texts)
        let countSignal = Float(tokens.count) / Float(maxTokens)
        for i in stride(from: 0, to: embeddingDim, by: 10) {
            embedding[i] += countSignal * 0.1
        }

        return embedding
    }

    private func normalize(_ vector: [Float]) -> [Float] {
        let norm = sqrt(vector.reduce(0) { $0 + $1 * $1 })
        return vector.map { $0 / max(norm, 1e-8) }
    }
}
