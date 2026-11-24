# Voice-over script (about 90 s) - record over DocInt_demo_video.mp4

1. (0:00) "This is DocInt, an AI app that reads documents and images and returns structured, validated results."
2. (0:05) "The task has five requirements and three success criteria. I built against every one."
3. (0:11) "The file is loaded, an engine reads it - Claude vision, or a local OCR engine that works offline - then a validation layer normalises everything and labels missing or uncertain fields. Same JSON every time."
4. (0:20) "In the web UI you drop a file, optionally type questions, and press Analyze."
5. (0:27) "First, a clean PDF invoice: type, customer, date, total and status, all high confidence, and the questions are answered."
6. (0:37) "Second, a photo of a receipt: OCR reads the text, and the same structure comes out."
7. (0:43) "Now the important one: a bad scan. Blurry, skewed, and an ink stain hides the total. The app doesn't pretend. The ambiguous date, damaged total and weak status are labeled uncertain, and the file is flagged for human review."
8. (0:56) "And a flyer that isn't a supported document: classified unknown, every question answers 'not found'. No made-up values."
9. (1:03) "Underneath is a stable JSON schema: value, confidence and status for every field."
10. (1:09) "Twelve automated tests cover parsing, every sample, schema consistency, and the fallback when the API fails."
11. (1:15) "Limitations are documented and returned inside every result."
12. (1:23) "Install, run the server, upload a document. Set an API key and the same pipeline uses Claude vision. Thanks for watching."
