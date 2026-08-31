def extract_best_paragraph(text, query):

    paragraphs = [
        p.strip()
        for p in text.split("\n\n")
        if p.strip()
    ]

    if not paragraphs:
        return text


    query_words = query.lower().split()

    best_paragraph = paragraphs[0]
    best_score = 0


    for paragraph in paragraphs:

        score = 0
        paragraph_lower = paragraph.lower()


        for word in query_words:

            if word in paragraph_lower:
                score += 1


        if score > best_score:
            best_score = score
            best_paragraph = paragraph


    return best_paragraph