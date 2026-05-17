import Foundation

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isStreaming = false
    @Published var error: String?
    @Published var sourcesUsed: [String] = []  // NEW

    private let ragPipeline: HybridRAGPipeline
    private let llmClient: LLMClient

    init(ragPipeline: HybridRAGPipeline, llmClient: LLMClient) {
        self.ragPipeline = ragPipeline
        self.llmClient = llmClient
    }

    func sendMessage(_ text: String) async {
        // Add user message
        let userMessage = ChatMessage(role: .user, content: text)
        messages.append(userMessage)

        isStreaming = true
        error = nil

        do {
            // RAG retrieval
            let context = try await ragPipeline.retrieveContext(for: text, topK: 10)
            sourcesUsed = context.sources

            // Build system prompt
            let systemPrompt = buildSystemPrompt(context: context)

            // Stream LLM response
            var assistantContent = ""
            let assistantMessage = ChatMessage(role: .assistant, content: "")
            messages.append(assistantMessage)

            for try await chunk in llmClient.stream(
                messages: messages.dropLast().map { ($0.role.rawValue, $0.content) },
                systemPrompt: systemPrompt
            ) {
                assistantContent += chunk
                if let lastIndex = messages.indices.last {
                    messages[lastIndex].content = assistantContent
                }
            }

        } catch {
            self.error = "Erreur: \(error.localizedDescription)"
        }

        isStreaming = false
    }

    private func buildSystemPrompt(context: RAGContext) -> String {
        let today = Date().formatted(date: .long, time: .omitted)

        var prompt = """
        Tu es un assistant personnel IA qui connaît intimement l'utilisateur grâce à ses données personnelles.
        Réponds toujours en français sauf si l'utilisateur écrit en anglais.
        Tutoie l'utilisateur. Date d'aujourd'hui : \(today).

        SOURCES DE DONNÉES DISPONIBLES :
        - Conversations (iMessage + WhatsApp)
        - Contacts iOS
        - Calendrier

        RÈGLES DE PRÉSENTATION — OBLIGATOIRES :
        - Structure chaque réponse en sections claires avec des titres en gras (**Titre**)
        - Utilise des listes à puces (- item) pour tout ce qui est énumérable
        - Maximum 2-3 phrases par point — jamais de blocs de texte continu
        - Saute une ligne entre chaque section

        RÈGLE CONTACTS : N'affiche jamais un numéro de téléphone brut. Utilise le prénom ou le nom de la personne.

        Si une information n'est pas dans le contexte fourni, dis "je ne trouve pas cette info dans tes données synchronisées".
        """

        // Add RAG context
        prompt += "\n\n\(context.fullContext)"

        return prompt
    }
}

struct ChatMessage: Identifiable {
    let id = UUID()
    enum Role: String {
        case user
        case assistant
    }
    let role: Role
    var content: String
}
