import Foundation

enum LLMError: Error {
    case noAPIKey
    case invalidResponse
    case httpError(Int)
}

final class LLMClient {
    private let session: URLSession

    init() {
        let config = URLSessionConfiguration.default
        config.tlsMinimumSupportedProtocolVersion = .TLSv13
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)
    }

    /// Stream Claude response using Server-Sent Events
    func stream(
        messages: [(role: String, content: String)],
        systemPrompt: String
    ) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    // Get API key from Keychain
                    guard let apiKey = try? KeychainManager.getAPIKey() else {
                        continuation.finish(throwing: LLMError.noAPIKey)
                        return
                    }

                    // Build request
                    var request = URLRequest(url: URL(string: "https://api.anthropic.com/v1/messages")!)
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
                    request.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")

                    let body: [String: Any] = [
                        "model": "claude-haiku-4-5",
                        "max_tokens": 2048,
                        "system": systemPrompt,
                        "messages": messages.map { ["role": $0.role, "content": $0.content] },
                        "stream": true
                    ]

                    request.httpBody = try JSONSerialization.data(withJSONObject: body)

                    // Start streaming
                    let (bytes, response) = try await session.bytes(for: request)

                    guard let httpResponse = response as? HTTPURLResponse else {
                        continuation.finish(throwing: LLMError.invalidResponse)
                        return
                    }

                    guard httpResponse.statusCode == 200 else {
                        continuation.finish(throwing: LLMError.httpError(httpResponse.statusCode))
                        return
                    }

                    // Parse SSE stream
                    var buffer = ""
                    for try await byte in bytes {
                        buffer.append(Character(UnicodeScalar(byte)))

                        // Check for complete event (double newline)
                        if buffer.hasSuffix("\n\n") {
                            let event = buffer.trimmingCharacters(in: .whitespacesAndNewlines)
                            buffer = ""

                            // Parse event
                            if let chunk = parseSSEEvent(event) {
                                continuation.yield(chunk)
                            }
                        }
                    }

                    continuation.finish()

                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    private func parseSSEEvent(_ event: String) -> String? {
        // Parse SSE format: "data: {...}"
        let lines = event.components(separatedBy: "\n")
        for line in lines {
            if line.hasPrefix("data: ") {
                let jsonString = String(line.dropFirst(6))
                guard let data = jsonString.data(using: .utf8),
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let type = json["type"] as? String else {
                    continue
                }

                if type == "content_block_delta",
                   let delta = json["delta"] as? [String: Any],
                   let text = delta["text"] as? String {
                    return text
                }
            }
        }
        return nil
    }
}
