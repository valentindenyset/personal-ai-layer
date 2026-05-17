import SwiftUI

@main
struct PersonalAIAgentApp: App {
    @StateObject private var appContainer = AppContainer()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appContainer)
        }
    }
}
