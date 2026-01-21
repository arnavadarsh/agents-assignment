import re

# Test the pattern
text = 'uh-huh'
word = 'uh-huh'
escaped_word = re.escape(word)
pattern = rf'(?<!\w){escaped_word}(?!\w)'
p = re.compile(pattern, re.IGNORECASE)
matches = p.findall(text)
print(f'Text: {text}')
print(f'Word: {word}')
print(f'Escaped: {escaped_word}')
print(f'Pattern: {pattern}')
print(f'Matches: {matches}')
print()

# Test word extraction
words = re.findall(r'\b[\w-]+\b', text.lower())
print(f'Extracted words: {words}')
print()

# The issue: \b doesn't work well with hyphens
# Better approach: treat hyphenated words as a unit
words_in_list = ['uh-huh', 'mm-hmm']
for w in words_in_list:
    if w in text.lower():
        print(f"Direct match: '{w}' found in '{text}'")
