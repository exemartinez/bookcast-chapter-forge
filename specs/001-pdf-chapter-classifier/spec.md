# Feature Specification: PDF Chapter Classifier 

**Feature Branch**: `001-pdf-chapter-classifier`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - As a user of NotebookLM I need a python script that takes a pdf and generates N pdfs as output - one per chapter (Priority: P1)

I take a random .pdf file and pass it as an argument to the script (`pdf_parser.py`) in a unix like command console. Then, I just run it. I will see cues of the script running and executing different task. When it successfully ends, I'll see In an `output/` folder 1 to N correct .pdf files. 
One for every preset of pages for every chunk, defined in a `configs/` folder in a `yaml` file that states the criteria by which every pdf should be chunked, the `config.yaml` file:

- Supports a preset of maximum number pages by which the pdf could be chunked. (every file found in the output should have that **maxium** amount of pages)

Output files should have the same name than the input file plus a postfix: `{input file name}-{order number}.pdf`. 

**Why this priority**: it just a way to lower the weight of a HUGE pdf file so NotebookLM accepts it into its scope.

**Independent Test**: Can be fully tested by placing any pdf created with 'Ipsum Lorem' kind of data up to two pages (gibberish, we just need the pages). Then, passed it through the script(`pdf_parser.py`) and it should deliver two pdf files with each page placed in each one.

**Acceptance Scenarios**:

1. **Given** a pdf file with 2 pages, **When** running the pdf_chapter_classifier with a config page of 1, **Then** 2 pdf files should be found in the `output/` folder

---

### User Story 2 - As a parse of pdfs I want a Simple Automatic Chapter Ending identification libreary (Priority: P2)

Add the module `pdf_chapter_classifier.py` as an aid for `pdf_parser.py`. The script will ask the pdf_chapter_classifier where a given chapter ends. This chapter classifier should use the `configs/config.yaml` file parameter, in addition to any previous configuration:

  - A regular expression to identify, generically, and for the english language only:
    - if the pdf is a book or not.
    - if the book has been written in **english**.
    - if a given page is: The end of a chapter.
    - if a given page is the beginning of a chapter.
    - If a given page is the end of the book.
    - If a given page is the beginning of the book.
(These should be in a new section inside the `configs/config.yaml` file, dedicated to this sort of run.)

Then, the `chapter-classifier` module (with their due internal bioma of classes and etc) should return a generator that brings where every chapter ends (at which page), so the `parser` cuts the source pdf in turn.
The previous functionality provided by the `parser` script should be available and executable by parameters. Which means that the current one should be accesable by parameters passed to the parser.
Also, the `parser` should take and process, sequentially, all the .pdf files that he may find inside the `books/` folder in the current repo.
Is important to notice that a "Chapter" is not a "conventional book chapter" here; it's the maximum block of pages in which a given pdf can be devided aside from the current one.
Example: if the current level is: "book", the next is "chapter". But if the current is "library", the next, is "book". And if current is "Chapter", may be is "section" (or pages if there is nothing lesser).
The concept of "chapter" is to divide the current pdf document in its next "greater" subset.

**Why this priority**: Its the next step in the way to algorithmically define where the pdf should be cut. Is it not sustentable to pass a number of pages each time. We need to refactor the original scope by all sorts.

**Independent Test**: 
1. use the file  `books/CSB_Pew_Bible_2nd_Printing.pdf` for testing: it should have 66 chapters/books.

**Acceptance Scenarios**:

1. **Given** `books/CSB_Pew_Bible_2nd_Printing.pdf`, **When** running the script, **Then** 66 pdfs files should have been produced with a number of pages greater than zero each.

---

### User Story 3 - Refactor over the chapter-classifier (Priority: P3)

Encapsulates the logic by which the `chapter-classifier` regex's are being consumed from `configs/config.yml`,
Assume that a way to identify if something is a book, we need to identify where its index is.
Then:

- Add a new set of regex's, in addition to the ones available up until today and in a new section inside `configs/config.yaml`
  - A regex to identify if a given page is an "index page" in english language.

1. Then, the `chapter-classifier` will: read the first 10 pages and the last ten, searching for the index page. It should search for: the word "Index" as the title, a list of sentences followed by dots, lines or nothing and a number before the '\n' or 'new line' char (or whatever comes, or might come, in a pdf)
2. Identify Each chapter name.
3. Identify in which page each chapter is placed (the number at the end of the line)
4. Search the first chapter string name, by name in the whole pdf: identify the `pdf-page` (the page that the pdf file says it is)
5. Compares the `pdf-page` with the `index-page` (the page we identified this chapter should be, by reading the index)
6. Stablishes the `offset` of pages.
7. Returns a generator (the same that in `Use Case 1`, but for this strategy - this is not ´casual` wording, this feature should be implemented as a **strategy pattern** or similar)

The `parser` should be refactored so it can handle the changes and provide the parameters to go for any of the available "chunking" strategies.
Note: Now, each output file should be named: `{input file name}-{order number}-{chapter name (max 10 characters)}.pdf`
Replace any special characters for their acceptable equivalents for a filename.

**Why this priority**: we cannot built this before we have use case 1 & 2 in place.

**Independent Test**: since this is a non-functional requirement we should go by implemented regular unit testing.

**Acceptance Scenarios**:

1. **Given** `books/CSB_Pew_Bible_2nd_Printing.pdf`, **When** running the script with this strategy, **Then** 66 pdfs files should have been produced with a number of pages greater than zero each.

---

### Edge Cases

- What happens when there is no index identyfiable?
  - Throw an error and abort the generation & chunking.
- How does system handle errors?
  - shows them throught the stdout. This is a CLI app.
- What if processing takes more than 5'?
  - Always show the chapters identified, and the progress. 
  - If there is stallment or an issues, leave the user to decide if he aborts the operation.
  - Keep everything in main memory until the parser has the pages by which it has to do the cut. When the chapters has been separated in pdfs, just right there, persist. This conserves transactionality and do not spam the user's HD.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST show progress at all times.
- **FR-002**: System MUST validate that the pdf is a pdf, and then a book. Just then proceed.  
- **FR-003**: Users MUST be able to abort the processing at any given time with ctrl-c. The process should rollback. Nothing should appear in the user's disk (idempotency).

### Key Entities *(include if feature involves data)*

- **Book**: it represents the whole pdf currently being analyzed.
- **Chapter**: the next logical division in which the text can be divided at the highest grade.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The number of pages in all the generated pdf (output) can't be higher than the number of pages in the source pdf (input)

## Assumptions

- This app runs in a bash console (CLI)
- Python 3.9 is installed and with a proper environment to process pdf's files.
