import SwiftUI
import UniformTypeIdentifiers

struct ImportView: View {
    @StateObject private var viewModel: ImportViewModel
    @Environment(\.dismiss) private var dismiss

    init(importer: BulkImporter) {
        _viewModel = StateObject(wrappedValue: ImportViewModel(importer: importer))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                if viewModel.isImporting {
                    ProgressView("Importing...")
                        .progressViewStyle(.circular)
                } else if let error = viewModel.error {
                    Text("Error: \(error)")
                        .foregroundColor(.red)
                } else if viewModel.importComplete {
                    VStack(spacing: 16) {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.green)

                        Text("Import Complete!")
                            .font(.headline)

                        Button("Done") {
                            dismiss()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                } else {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Import from Mac Export")
                            .font(.headline)

                        Text("Select the exported .db file from your Mac")
                            .font(.subheadline)
                            .foregroundColor(.secondary)

                        Button("Select Database File") {
                            viewModel.showingFilePicker = true
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding()
                }
            }
            .navigationTitle("Import Data")
            .fileImporter(
                isPresented: $viewModel.showingFilePicker,
                allowedContentTypes: [.database, .json],
                allowsMultipleSelection: false
            ) { result in
                Task {
                    await viewModel.handleFileSelection(result)
                }
            }
        }
    }
}

@MainActor
final class ImportViewModel: ObservableObject {
    @Published var showingFilePicker = false
    @Published var isImporting = false
    @Published var importComplete = false
    @Published var error: String?

    private let importer: BulkImporter

    init(importer: BulkImporter) {
        self.importer = importer
    }

    func handleFileSelection(_ result: Result<[URL], Error>) async {
        do {
            let urls = try result.get()
            guard let dbURL = urls.first else { return }

            isImporting = true
            error = nil

            // For MVP, assume entities.json and relations.json are in same directory
            let directory = dbURL.deletingLastPathComponent()
            let entitiesURL = directory.appendingPathComponent("entities.json")
            let relationsURL = directory.appendingPathComponent("relations.json")

            // Import
            try await importer.importBulkExport(
                databaseURL: dbURL,
                entitiesURL: entitiesURL,
                relationsURL: relationsURL
            )

            isImporting = false
            importComplete = true

        } catch {
            isImporting = false
            self.error = error.localizedDescription
        }
    }
}

extension UTType {
    static var database: UTType {
        UTType(exportedAs: "public.database")
    }
}
