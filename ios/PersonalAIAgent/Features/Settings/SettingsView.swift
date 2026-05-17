import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appContainer: AppContainer

    var body: some View {
        NavigationStack {
            Form {
                Section("Data") {
                    NavigationLink("Import from Mac") {
                        ImportView(importer: appContainer.bulkImporter)
                    }

                    LabeledContent("Total chunks", value: "\(appContainer.vectorStore.chunkCount)")
                    LabeledContent("Total entities", value: "\(appContainer.graphStore.entityCount)")
                }

                Section("About") {
                    LabeledContent("Version", value: "1.0")
                    LabeledContent("Build", value: "1")
                }
            }
            .navigationTitle("Settings")
        }
    }
}
