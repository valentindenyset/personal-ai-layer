import XCTest
@testable import PersonalAIAgent

final class GraphStoreTests: XCTestCase {
    var graphStore: GraphStore!

    override func setUp() {
        super.setUp()
        graphStore = GraphStore(inMemory: true)
    }

    func testCreateAndFindPerson() throws {
        let personID = graphStore.upsertPerson(
            name: "Alexandre Guedj",
            phoneNumbers: ["+33612345678"],
            emails: ["alex@test.com"]
        )

        let found = graphStore.findPerson(name: "Alexandre Guedj")

        XCTAssertNotNil(found)
        XCTAssertEqual(found?.id, personID)
        XCTAssertEqual(found?.name, "Alexandre Guedj")
    }

    func testRelationStrengthIncrement() throws {
        let alex = graphStore.upsertPerson(name: "Alex")
        let marie = graphStore.upsertPerson(name: "Marie")

        // First interaction
        graphStore.upsertRelation(from: alex, to: marie, type: .KNOWS)
        var relation = graphStore.getRelation(from: alex, to: marie, type: .KNOWS)
        XCTAssertEqual(relation?.strength, 1)

        // Second interaction
        graphStore.upsertRelation(from: alex, to: marie, type: .KNOWS)
        relation = graphStore.getRelation(from: alex, to: marie, type: .KNOWS)
        XCTAssertEqual(relation?.strength, 2)
    }

    func testTopContactsByVolume() throws {
        // Create persons with different message counts
        let alex = graphStore.upsertPerson(name: "Alex")
        let marie = graphStore.upsertPerson(name: "Marie")
        let tom = graphStore.upsertPerson(name: "Tom")

        // Simulate interactions (strength = interaction count)
        for _ in 0..<10 {
            graphStore.upsertRelation(from: "user", to: alex, type: .KNOWS)
        }
        for _ in 0..<5 {
            graphStore.upsertRelation(from: "user", to: marie, type: .KNOWS)
        }
        for _ in 0..<15 {
            graphStore.upsertRelation(from: "user", to: tom, type: .KNOWS)
        }

        let topContacts = graphStore.topContacts(limit: 3)

        XCTAssertEqual(topContacts.count, 3)
        XCTAssertEqual(topContacts[0].name, "Tom")  // 15 interactions
        XCTAssertEqual(topContacts[1].name, "Alex")  // 10 interactions
        XCTAssertEqual(topContacts[2].name, "Marie")  // 5 interactions
    }
}
