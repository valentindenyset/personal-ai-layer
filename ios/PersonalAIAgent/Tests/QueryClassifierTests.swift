import XCTest
@testable import PersonalAIAgent

final class QueryClassifierTests: XCTestCase {
    let classifier = QueryClassifier()

    func testFrequencyQuery() {
        XCTAssertEqual(classifier.classify("Avec qui je parle le plus ?"), .frequency)
        XCTAssertEqual(classifier.classify("Mes contacts les plus fréquents"), .frequency)
    }

    func testCalendarQuery() {
        XCTAssertEqual(classifier.classify("Qu'est-ce que j'ai cette semaine ?"), .calendar)
        XCTAssertEqual(classifier.classify("Mon agenda demain"), .calendar)
    }

    func testContactLookupQuery() {
        XCTAssertEqual(classifier.classify("Qui est Alexandre Guedj ?"), .contactLookup)
        XCTAssertEqual(classifier.classify("C'est qui Marie ?"), .contactLookup)
    }

    func testGeneralQuery() {
        XCTAssertEqual(classifier.classify("Parle-moi de crypto"), .general)
        XCTAssertEqual(classifier.classify("What did we discuss about AI?"), .general)
    }
}
