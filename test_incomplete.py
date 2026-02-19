from app.analyzers.static_analyzer import StaticAnalyzer

code = '''def is_palindrome(text):
    cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        # model stopped here, rest of loop missing'''

result = StaticAnalyzer(code).analyze()
print('Incomplete Generation Found:', result['incomplete_generation']['found'])
if result['incomplete_generation']['found']:
    for detail in result['incomplete_generation']['details']:
        print(f"  - {detail['type']}: {detail['description']}")
