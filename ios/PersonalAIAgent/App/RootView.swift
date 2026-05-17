import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appContainer: AppContainer

    var body: some View {
        TabView {
            // Chat Tab
            NavigationStack {
                ChatView(viewModel: appContainer.chatViewModel)
            }
            .tabItem {
                Label("Chat", systemImage: "bubble.right.fill")
            }

            // Settings Tab
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
        }
    }
}

struct ChatView: View {
    @ObservedObject var viewModel: ChatViewModel

    @State private var inputText = ""

    var body: some View {
        VStack(spacing: 0) {
            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            HStack {
                                if message.role == .user {
                                    Spacer()
                                }

                                Text(message.content)
                                    .padding(12)
                                    .background(message.role == .user ? Color.blue : Color.gray.opacity(0.2))
                                    .foregroundColor(message.role == .user ? .white : .black)
                                    .cornerRadius(12)

                                if message.role == .assistant {
                                    Spacer()
                                }
                            }
                            .id(message.id)
                        }
                    }
                    .padding()
                    .onChange(of: viewModel.messages.count) { _, _ in
                        if let lastID = viewModel.messages.last?.id {
                            proxy.scrollTo(lastID)
                        }
                    }
                }
            }

            Divider()

            // Input
            HStack(spacing: 12) {
                TextField("Ask me something...", text: $inputText)
                    .textFieldStyle(.roundedBorder)
                    .disabled(viewModel.isStreaming)

                Button(action: {
                    guard !inputText.isEmpty else { return }
                    let text = inputText
                    inputText = ""
                    Task {
                        await viewModel.sendMessage(text)
                    }
                }) {
                    Image(systemName: "paperplane.fill")
                }
                .disabled(inputText.isEmpty || viewModel.isStreaming)
            }
            .padding()
        }
        .navigationTitle("Chat")
    }
}
