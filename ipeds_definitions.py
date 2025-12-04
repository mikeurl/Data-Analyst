"""
IPEDS Fall Enrollment Definitions and Documentation

This module provides IPEDS definitions and documentation for simple RAG lookup.
It contains key definitions from the IPEDS Fall Enrollment survey that help
users understand how to correctly classify and report students.

These definitions are based on NCES IPEDS survey materials and instructions.
"""

from typing import Dict, List, Optional
import re

# IPEDS Definitions Dictionary
IPEDS_DEFINITIONS = {
    "first_time_student": {
        "term": "First-time Student",
        "definition": """A first-time student is a student attending any institution for the first
time at the undergraduate level. This includes students enrolled in academic or
occupational programs and also includes students enrolled in the fall term who
attended college for the first time in the prior summer term. Students who
entered with advanced standing (college credits or recognized postsecondary
credential earned before graduation from high school) are also considered
first-time students.""",
        "key_points": [
            "Never attended any postsecondary institution before",
            "Includes students who started in prior summer term",
            "Includes students with dual enrollment credits earned in high school",
            "Does NOT include transfer students from other institutions"
        ],
        "ipeds_part": "Part A, C, E"
    },

    "full_time_student": {
        "term": "Full-time Student",
        "definition": """A full-time undergraduate student is one who is enrolled for 12 or more
semester credits, or 12 or more quarter credits, or 24 or more clock hours
per week each term. For graduate students, institutions define full-time
status based on their own policies.""",
        "key_points": [
            "Undergraduate: 12+ semester/quarter credits",
            "Or 24+ clock hours per week",
            "Status determined at census date",
            "Graduate status defined by institution"
        ],
        "ipeds_part": "Part A, B, E"
    },

    "part_time_student": {
        "term": "Part-time Student",
        "definition": """A part-time undergraduate student is one who is enrolled for fewer than
12 semester credits, or fewer than 12 quarter credits, or fewer than 24
clock hours per week each term.""",
        "key_points": [
            "Undergraduate: fewer than 12 credits",
            "Or fewer than 24 clock hours per week",
            "Includes students taking only 1 course",
            "Status determined at census date"
        ],
        "ipeds_part": "Part A, B, E"
    },

    "transfer_in_student": {
        "term": "Transfer-in Student",
        "definition": """A transfer-in student is a student entering the reporting institution
for the first time but known to have previously attended a postsecondary
institution at the same level (e.g., undergraduate). This includes students
who earned credits while enrolled in high school if those credits were
earned at another postsecondary institution.""",
        "key_points": [
            "Previously attended another postsecondary institution",
            "Entering this institution for the first time",
            "Credits may or may not transfer",
            "Different from students with only dual enrollment credits"
        ],
        "ipeds_part": "Part A"
    },

    "continuing_student": {
        "term": "Continuing Student",
        "definition": """A continuing student is a student who is not entering the institution
for the first time. This includes students returning after a period of
non-enrollment and students who have been continuously enrolled.""",
        "key_points": [
            "Previously enrolled at this institution",
            "Returning students count as continuing",
            "Does not include first-time or transfer students",
            "May include students who stopped out and returned"
        ],
        "ipeds_part": "Part A"
    },

    "degree_seeking": {
        "term": "Degree-seeking Student",
        "definition": """A degree-seeking student is enrolled in courses for credit who is
recognized by the institution as seeking a degree or formal award. This
includes students enrolled in a vocational or occupational program leading
to a certificate, diploma, or degree.""",
        "key_points": [
            "Enrolled in a degree or certificate program",
            "Intent to complete a formal award",
            "Includes vocational/occupational programs",
            "Different from non-degree-seeking students"
        ],
        "ipeds_part": "Part A, E"
    },

    "certificate_seeking": {
        "term": "Certificate-seeking Student",
        "definition": """A certificate-seeking student is enrolled in courses for credit who is
recognized by the institution as seeking a certificate (a formal award
certifying satisfactory completion of a postsecondary education program).
Certificates are less than 1 year, 1-2 years, or 2-4 years in duration.""",
        "key_points": [
            "Seeking formal certificate, not degree",
            "Certificate less than 4 years",
            "Includes vocational certificates",
            "May be classified as undergraduate"
        ],
        "ipeds_part": "Part A"
    },

    "non_degree_seeking": {
        "term": "Non-degree-seeking Student",
        "definition": """A non-degree-seeking student is a student enrolled in courses for credit
who is not recognized by the institution as seeking a degree or formal award.
This may include students taking courses for personal enrichment, professional
development, or to meet requirements for another institution.""",
        "key_points": [
            "Not in a degree or certificate program",
            "May be auditing or personal enrichment",
            "Still counted if for credit",
            "Not included in graduation rate cohorts"
        ],
        "ipeds_part": "Part A"
    },

    "retention_rate": {
        "term": "Retention Rate",
        "definition": """The retention rate is a measure of the rate at which students persist
in their educational program at an institution, expressed as a percentage.
For IPEDS, the retention rate is calculated as the percentage of a cohort
of first-time degree/certificate-seeking students from one fall who either
re-enrolled or successfully completed their program by the following fall.""",
        "key_points": [
            "Cohort: First-time degree-seeking students from prior fall",
            "Numerator: Students enrolled or completed by following fall",
            "Exclusions allowed for death, disability, military, foreign service",
            "Calculated separately for full-time and part-time"
        ],
        "calculation": """
Retention Rate = (Retained + Completed) / Adjusted Cohort × 100

Where:
- Adjusted Cohort = Initial Cohort - Exclusions
- Exclusions = Students who died, became permanently disabled, or
  entered military/foreign service
        """,
        "ipeds_part": "Part E"
    },

    "distance_education": {
        "term": "Distance Education",
        "definition": """Distance education is education that uses one or more technologies
to deliver instruction to students who are separated from the instructor
and to support regular and substantive interaction between the students
and the instructor synchronously or asynchronously.""",
        "key_points": [
            "Includes online courses",
            "Includes correspondence courses with interaction",
            "Does NOT include traditional mail courses without interaction",
            "Categories: Exclusively DE, Some DE, No DE"
        ],
        "categories": {
            "Exclusively DE": "All courses are distance education",
            "Some DE": "At least one but not all courses are distance education",
            "No DE": "No courses are distance education"
        },
        "ipeds_part": "Part A"
    },

    "enrolled_in_state": {
        "term": "Enrolled in State",
        "definition": """For distance education students, 'enrolled in state' means the student
is taking distance education courses while physically located in the same
state as the institution. This is determined by the student's location at
the time of enrollment, not their permanent residence.""",
        "key_points": [
            "Based on physical location during enrollment",
            "Not the same as state of residence",
            "Important for exclusively DE students",
            "Affects state-level reporting"
        ],
        "ipeds_part": "Part A"
    },

    "race_ethnicity": {
        "term": "Race/Ethnicity Categories",
        "definition": """IPEDS uses a two-question format to collect race and ethnicity data.
First, students are asked if they are Hispanic/Latino. Then, they select
one or more racial categories. Reporting follows a specific hierarchy.""",
        "categories": {
            "Hispanic/Latino": "A person of Cuban, Mexican, Puerto Rican, South or Central American, or other Spanish culture or origin, regardless of race",
            "American Indian/Alaska Native": "A person having origins in any of the original peoples of North and South America who maintains tribal affiliation or community attachment",
            "Asian": "A person having origins in any of the original peoples of the Far East, Southeast Asia, or the Indian subcontinent",
            "Black/African American": "A person having origins in any of the black racial groups of Africa",
            "Native Hawaiian/Pacific Islander": "A person having origins in any of the original peoples of Hawaii, Guam, Samoa, or other Pacific Islands",
            "White": "A person having origins in any of the original peoples of Europe, the Middle East, or North Africa",
            "Two or More Races": "Non-Hispanic students who selected more than one race",
            "Race/Ethnicity Unknown": "Race and ethnicity unknown or not reported",
            "Nonresident Alien": "A person who is not a citizen or national of the United States and who is in this country on a temporary basis"
        },
        "key_points": [
            "Hispanic/Latino is asked first and separately",
            "If Hispanic/Latino, race is not separately reported",
            "Nonresident aliens are reported separately regardless of race",
            "Two or more races only for non-Hispanic students"
        ],
        "ipeds_part": "Part A"
    },

    "student_faculty_ratio": {
        "term": "Student-to-Faculty Ratio",
        "definition": """The student-to-faculty ratio is calculated by dividing the total
FTE student enrollment by the total FTE instructional staff. FTE for
students is calculated as full-time students plus one-third part-time
students. Faculty FTE includes only instructional staff whose primary
function is instruction.""",
        "key_points": [
            "Student FTE = Full-time + (Part-time / 3)",
            "Faculty FTE = Sum of FTE values for instructional staff",
            "Only includes faculty with instruction as primary function",
            "Reported as ratio (e.g., 15:1)"
        ],
        "calculation": """
Student-to-Faculty Ratio = Student FTE / Faculty FTE

Where:
- Student FTE = FT Students + (PT Students ÷ 3)
- Faculty FTE = Sum of individual faculty FTE values
  (1.0 for full-time, proportional for part-time)
        """,
        "ipeds_part": "Part F"
    },

    "cohort": {
        "term": "Cohort",
        "definition": """A cohort is a specific group of students established for tracking
purposes. In IPEDS, the fall enrollment retention rate cohort consists
of all first-time, degree/certificate-seeking undergraduate students who
entered the institution in a particular fall term.""",
        "key_points": [
            "Established in a specific fall term",
            "First-time students only",
            "Degree or certificate-seeking",
            "Tracked to the following fall"
        ],
        "ipeds_part": "Part E"
    },

    "exclusions": {
        "term": "Cohort Exclusions",
        "definition": """Students may be excluded from a cohort for retention rate calculations
if they left the institution due to specific allowable reasons. These
exclusions adjust the denominator of the retention rate calculation.""",
        "allowable_exclusions": [
            "Death",
            "Permanent disability",
            "Service in armed forces (including active duty)",
            "Service with a foreign aid service of the federal government",
            "Service on official church missions"
        ],
        "key_points": [
            "Documentation may be required",
            "Reduces adjusted cohort size",
            "Cannot exclude for academic or financial reasons",
            "Must be verified by institution"
        ],
        "ipeds_part": "Part E"
    }
}

# Search keywords mapped to definitions
KEYWORD_MAPPINGS = {
    "first-time": "first_time_student",
    "first time": "first_time_student",
    "new student": "first_time_student",
    "freshman": "first_time_student",
    "full-time": "full_time_student",
    "full time": "full_time_student",
    "12 credit": "full_time_student",
    "part-time": "part_time_student",
    "part time": "part_time_student",
    "less than 12": "part_time_student",
    "transfer": "transfer_in_student",
    "transfer-in": "transfer_in_student",
    "continuing": "continuing_student",
    "returning": "continuing_student",
    "degree-seeking": "degree_seeking",
    "degree seeking": "degree_seeking",
    "certificate-seeking": "certificate_seeking",
    "certificate seeking": "certificate_seeking",
    "non-degree": "non_degree_seeking",
    "non degree": "non_degree_seeking",
    "retention": "retention_rate",
    "retention rate": "retention_rate",
    "persist": "retention_rate",
    "distance education": "distance_education",
    "online": "distance_education",
    "de student": "distance_education",
    "in state": "enrolled_in_state",
    "in-state": "enrolled_in_state",
    "race": "race_ethnicity",
    "ethnicity": "race_ethnicity",
    "hispanic": "race_ethnicity",
    "latino": "race_ethnicity",
    "faculty ratio": "student_faculty_ratio",
    "student-to-faculty": "student_faculty_ratio",
    "student to faculty": "student_faculty_ratio",
    "cohort": "cohort",
    "exclusion": "exclusions",
    "exclude": "exclusions",
    "allowable exclusion": "exclusions"
}


class IPEDSDocumentationLookup:
    """
    Simple RAG-like lookup for IPEDS definitions.

    Provides methods to search and retrieve IPEDS definitions based on
    keywords or specific definition keys.
    """

    def __init__(self):
        """Initialize the lookup with definitions."""
        self.definitions = IPEDS_DEFINITIONS
        self.keyword_mappings = KEYWORD_MAPPINGS

    def get_definition(self, key: str) -> Optional[Dict]:
        """
        Get a specific definition by its key.

        Args:
            key: The definition key (e.g., "first_time_student")

        Returns:
            Dictionary containing the definition, or None if not found
        """
        return self.definitions.get(key)

    def search(self, query: str) -> List[Dict]:
        """
        Search for relevant definitions based on a query string.

        Args:
            query: The search query

        Returns:
            List of matching definitions
        """
        query_lower = query.lower()
        results = []
        matched_keys = set()

        # First, check keyword mappings
        for keyword, def_key in self.keyword_mappings.items():
            if keyword in query_lower and def_key not in matched_keys:
                definition = self.definitions.get(def_key)
                if definition:
                    results.append({
                        "key": def_key,
                        "match_type": "keyword",
                        "matched_keyword": keyword,
                        **definition
                    })
                    matched_keys.add(def_key)

        # If no keyword matches, search in definitions and terms
        if not results:
            for key, definition in self.definitions.items():
                if key not in matched_keys:
                    # Check term
                    if query_lower in definition["term"].lower():
                        results.append({
                            "key": key,
                            "match_type": "term",
                            **definition
                        })
                        matched_keys.add(key)
                    # Check definition text
                    elif query_lower in definition["definition"].lower():
                        results.append({
                            "key": key,
                            "match_type": "definition",
                            **definition
                        })
                        matched_keys.add(key)

        return results

    def get_all_definitions(self) -> Dict[str, Dict]:
        """Get all definitions."""
        return self.definitions

    def format_definition_markdown(self, definition: Dict) -> str:
        """
        Format a definition as markdown for display.

        Args:
            definition: The definition dictionary

        Returns:
            Formatted markdown string
        """
        md = f"## {definition['term']}\n\n"
        md += f"{definition['definition']}\n\n"

        if 'key_points' in definition:
            md += "### Key Points\n"
            for point in definition['key_points']:
                md += f"- {point}\n"
            md += "\n"

        if 'calculation' in definition:
            md += "### Calculation\n"
            md += f"```\n{definition['calculation'].strip()}\n```\n\n"

        if 'categories' in definition:
            md += "### Categories\n"
            for cat, desc in definition['categories'].items():
                md += f"- **{cat}**: {desc}\n"
            md += "\n"

        if 'allowable_exclusions' in definition:
            md += "### Allowable Exclusions\n"
            for exc in definition['allowable_exclusions']:
                md += f"- {exc}\n"
            md += "\n"

        md += f"*IPEDS Part: {definition['ipeds_part']}*"

        return md

    def answer_question(self, question: str) -> str:
        """
        Answer a question about IPEDS definitions.

        Args:
            question: The user's question

        Returns:
            Formatted answer string
        """
        results = self.search(question)

        if not results:
            return """I couldn't find a specific IPEDS definition matching your question.

Here are the available topics I can help with:
- First-time student definition
- Full-time/Part-time definitions
- Transfer-in student
- Continuing student
- Degree-seeking vs Certificate-seeking vs Non-degree-seeking
- Retention rate calculation
- Distance education classifications
- Race/Ethnicity categories
- Student-to-faculty ratio
- Cohort and exclusions

Try rephrasing your question with one of these topics."""

        # Return the most relevant result
        best_match = results[0]
        return self.format_definition_markdown(best_match)


def get_documentation_lookup() -> IPEDSDocumentationLookup:
    """Factory function to create a documentation lookup instance."""
    return IPEDSDocumentationLookup()


if __name__ == "__main__":
    # Demo usage
    lookup = get_documentation_lookup()

    print("=== IPEDS Documentation Lookup Demo ===\n")

    # Test some queries
    test_queries = [
        "What is a first-time student?",
        "How is retention rate calculated?",
        "What are the race/ethnicity categories?",
        "What is full-time status?"
    ]

    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 40)
        answer = lookup.answer_question(query)
        print(answer)
        print("\n" + "=" * 60 + "\n")
