import Foundation

enum QueryType {
    case frequency      // "Avec qui je parle le plus ?"
    case calendar       // "Qu'est-ce que j'ai cette semaine ?"
    case contactLookup  // "Qui est Alexandre ?"
    case general        // Everything else
}

struct QueryClassifier {
    func classify(_ query: String) -> QueryType {
        let lower = query.lowercased()

        // Frequency patterns
        let frequencyPatterns = [
            "le plus", "le moins", "souvent", "fréquent", "beaucoup",
            "avec qui", "plus souvent", "most", "frequent"
        ]
        if frequencyPatterns.contains(where: { lower.contains($0) }) {
            return .frequency
        }

        // Calendar patterns
        let calendarPatterns = [
            "calendrier", "agenda", "prévu", "réunion", "rendez-vous", "rdv",
            "semaine", "aujourd'hui", "demain", "cette semaine", "prochain",
            "prochaine", "schedule", "meeting", "calendar", "événement", "event"
        ]
        if calendarPatterns.contains(where: { lower.contains($0) }) {
            return .calendar
        }

        // Contact lookup patterns
        let contactPatterns = [
            "qui est", "c'est qui", "connais", "contact", "qui c'est"
        ]
        if contactPatterns.contains(where: { lower.contains($0) }) {
            return .contactLookup
        }

        return .general
    }
}
