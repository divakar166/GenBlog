from youtube_transcript_api import YouTubeTranscriptApi
ex = YouTubeTranscriptApi.get_transcript('vyQv563Y-fk')
final_text = ""
for item in ex:
    final_text += item['text']
print(final_text)